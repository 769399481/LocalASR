param(
    [Parameter(Mandatory=$true)][string]$ModelRoot,
    [Parameter(Mandatory=$true)][string]$SmallModel,
    [Parameter(Mandatory=$true)][string]$Audio,
    [string]$BuildDirectory,
    [string]$ReportDirectory
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
if (-not $BuildDirectory) { $BuildDirectory = Join-Path $repo 'dist\LocalASR' }
if (-not $ReportDirectory) { $ReportDirectory = Join-Path $repo 'validation\phase9' }
$run = Join-Path $env:TEMP ('LocalASR-validation-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $run | Out-Null
Copy-Item -LiteralPath $BuildDirectory -Destination (Join-Path $run 'LocalASR') -Recurse
$data = Join-Path $run 'UserRoot\LocalASR'
$models = Join-Path $data 'models'
New-Item -ItemType Directory -Path $models -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $ModelRoot 'large-v3') -Destination $models -Recurse
Copy-Item -LiteralPath (Join-Path $ModelRoot 'opus-mt-en-zh') -Destination $models -Recurse
Copy-Item -LiteralPath $SmallModel -Destination (Join-Path $models 'small') -Recurse
$fixture = Join-Path $run 'fixture.wav'
Copy-Item -LiteralPath $Audio -Destination $fixture
# Environment changes affect this validation launcher and its children only.
Get-ChildItem Env: | Where-Object { $_.Name -match '^(CONDA|PYTHON|LOCALASR|HF_|HUGGINGFACE|TRANSFORMERS)' } | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
$env:LOCALAPPDATA = Join-Path $run 'UserRoot'
$env:HF_HOME = Join-Path $run 'EmptyCache'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$exe = Join-Path $run 'LocalASR\LocalASR.exe'
$report = Join-Path $run 'packaged.json'
$arguments = '--packaged-check --offline --models "{0}" --audio "{1}" --report "{2}"' -f $models,$fixture,$report
$env:LOCALASR_LAUNCH_UNIX = ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000).ToString([cultureinfo]::InvariantCulture)
$process = Start-Process -FilePath $exe -WorkingDirectory $run -ArgumentList $arguments -PassThru
$modules = [System.Collections.Generic.HashSet[string]]::new()
while (-not $process.HasExited) {
    try { $process.Modules | ForEach-Object { [void]$modules.Add($_.FileName) } } catch { }
    Start-Sleep -Seconds 1
    $process.Refresh()
}
$exitCode = $process.ExitCode
$metadata = @{run=$run; exit_code=$exitCode; path=$env:PATH; modules=@($modules | Sort-Object)}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $run 'isolation.json') -Encoding utf8
# A second fresh user directory verifies actual first-run and missing-model UI.
$env:LOCALAPPDATA = Join-Path $run 'EmptyUserRoot'
$startupReport = Join-Path $run 'startup.json'
$env:LOCALASR_LAUNCH_UNIX = ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000).ToString([cultureinfo]::InvariantCulture)
$startup = Start-Process -FilePath $exe -WorkingDirectory $run -ArgumentList ('--packaged-check --offline --startup-only --report "{0}"' -f $startupReport) -Wait -PassThru
$destination = $ReportDirectory
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($file in @($report, $startupReport, (Join-Path $run 'isolation.json'))) {
    if (Test-Path -LiteralPath $file) { Copy-Item -LiteralPath $file -Destination $destination }
}
Write-Output "Validation artifacts retained: $run"
Write-Output "Full check exit: $exitCode; startup check exit: $($startup.ExitCode)"
if ($exitCode -ne 0 -or $startup.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report)) { throw 'Packaged process failed; inspect retained logs' }
$full = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$empty = Get-Content -LiteralPath $startupReport -Raw | ConvertFrom-Json
if ($full.backend_error -or $full.gui_check_error -or $full.timeout -or
    -not $full.frozen -or -not $full.first_run_dialog -or -not $full.completion_valid -or
    -not $full.missing_vtt_incomplete -or -not $full.file_translation_complete -or
    -not $full.bilingual_docx -or -not $full.realtime.microphone_start_stop_twice -or
    -not $full.realtime.clean_shutdown -or $full.realtime.replay_errors.Count -ne 0 -or
    $full.realtime.replay_finals.Count -eq 0 -or
    $full.realtime.replay_finals.Count -ne $full.realtime.replay_translations.Count -or
    -not $empty.missing_model_prompt -or -not $empty.first_run_dialog) {
    throw 'A packaged validation assertion failed; inspect retained JSON reports'
}
foreach ($result in @($full, $empty)) {
    foreach ($check in $result.downloader.PSObject.Properties) {
        if ($check.Value -ne $true) { throw "Download check failed: $($check.Name)" }
    }
}
$runtimeLog = Get-Content -LiteralPath (Join-Path $data 'logs\gui.log') -Raw
if ($runtimeLog -notmatch 'Loading local model: .*; device=cuda; compute_type=float16' -or
    $runtimeLog -notmatch 'Realtime model=.* device=cuda compute_type=float16' -or
    $runtimeLog -match 'GPU model loading failed|GPU inference failed|Realtime GPU initialization failed|Realtime CUDA inference failed') {
    throw 'GPU execution evidence missing or CPU fallback detected'
}
Copy-Item -LiteralPath (Join-Path $data 'logs\gui.log') -Destination (Join-Path $destination 'runtime.log')
$full.diagnostics | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $destination 'diagnostics.json') -Encoding utf8
$leftover = @(Get-CimInstance Win32_Process -Filter "Name = 'LocalASR.exe'" | Where-Object { $_.ExecutablePath -eq $exe })
@{remaining_processes=$leftover.Count; checked_at=(Get-Date -Format o)} | ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $destination 'shutdown.json') -Encoding utf8
if ($leftover.Count -ne 0) { throw 'Validation EXE processes remain after shutdown' }
Write-Output 'Packaged validation assertions passed.'
