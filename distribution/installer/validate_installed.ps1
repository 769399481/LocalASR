param(
    [Parameter(Mandatory=$true)][string]$InstallDirectory,
    [Parameter(Mandatory=$true)][string]$ModelDirectory,
    [Parameter(Mandatory=$true)][string]$Audio,
    [Parameter(Mandatory=$true)][string]$ReportDirectory,
    [ValidateSet('core','startup','system')][string]$Mode = 'core'
)
$ErrorActionPreference = 'Stop'
$exe = Join-Path (Resolve-Path -LiteralPath $InstallDirectory).Path 'LocalASR.exe'
$models = (Resolve-Path -LiteralPath $ModelDirectory).Path
$audioPath = (Resolve-Path -LiteralPath $Audio).Path
$report = [IO.Path]::GetFullPath($ReportDirectory)
New-Item -ItemType Directory -Force -Path $report | Out-Null
$data = Join-Path $env:TEMP ('LocalASR-installed-check-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $data | Out-Null
if ($Mode -ne 'startup') {
    # A junction reuses existing models without downloads/copies. App files stay separate.
    New-Item -ItemType Junction -Path (Join-Path $data 'models') -Target $models | Out-Null
}
Get-ChildItem Env: | Where-Object { $_.Name -match '^(CONDA|PYTHON|LOCALASR|HF_|HUGGINGFACE|TRANSFORMERS)' } | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
$env:LOCALASR_DATA_DIR = $data
$env:HF_HOME = Join-Path $data 'empty-cache'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$result = Join-Path $report 'report.json'
if ($Mode -eq 'system') {
    $arguments = '--system-audio-check --models "{0}" --audio "{1}" --directory "{2}" --duration 45' -f (Join-Path $data 'models'),$audioPath,$report
} elseif ($Mode -eq 'startup') {
    $arguments = '--packaged-check --offline --startup-only --report "{0}"' -f $result
} else {
    $arguments = '--packaged-check --offline --models "{0}" --audio "{1}" --report "{2}"' -f (Join-Path $data 'models'),$audioPath,$result
}
# Visible because this is an explicit GUI acceptance test.
$process = Start-Process -FilePath $exe -WorkingDirectory $data -ArgumentList $arguments -PassThru
$modules = [Collections.Generic.HashSet[string]]::new()
$watch = [Diagnostics.Stopwatch]::StartNew()
while (-not $process.HasExited) {
    try { $process.Modules | ForEach-Object { [void]$modules.Add($_.FileName) } } catch {}
    if ($watch.Elapsed.TotalMinutes -gt 12) { throw 'Acceptance timeout; inspect application, no force-kill performed' }
    Start-Sleep -Seconds 1
    $process.Refresh()
}
$remaining = @(Get-CimInstance Win32_Process -Filter "Name='LocalASR.exe'" | Where-Object { $_.ExecutablePath -eq $exe })
$metadata = @{mode=$Mode;executable=$exe;data=$data;exit_code=$process.ExitCode;seconds=$watch.Elapsed.TotalSeconds;remaining_processes=$remaining.Count;path=$env:PATH;modules=@($modules|Sort-Object)}
$metadata | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $report 'isolation.json') -Encoding utf8
if ($process.ExitCode -ne 0 -or $remaining.Count -ne 0 -or -not (Test-Path -LiteralPath $result)) { throw 'Installed validation did not complete cleanly' }
$r = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
if ($Mode -eq 'core') {
    if (-not $r.frozen -or -not $r.completion_valid -or -not $r.file_translation_complete -or -not $r.bilingual_docx -or -not $r.realtime.microphone_start_stop_twice -or -not $r.realtime.clean_shutdown -or $r.backend_error -or $r.gui_check_error) { throw 'Installed core validation assertion failed' }
} elseif ($Mode -eq 'startup') {
    if (-not $r.frozen -or -not $r.first_run_dialog -or -not $r.missing_model_prompt) { throw 'First-run check failed' }
} else {
    if (-not $r.passed -or -not $r.clean_shutdown -or $r.metrics.dropped_audio_frames -ne 0 -or $r.metrics.translation.dropped_translations -ne 0) { throw 'System audio check failed' }
}
Write-Output "Installed $Mode check PASS; data retained: $data"
