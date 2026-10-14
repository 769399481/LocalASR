param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$ReportDirectory,
    [int]$Runs = 2
)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path -LiteralPath $Executable).Path
New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null
$destination = (Resolve-Path -LiteralPath $ReportDirectory).Path
Get-ChildItem Env: | Where-Object { $_.Name -match '^(CONDA|PYTHON|LOCALASR|HF_|HUGGINGFACE|TRANSFORMERS)' } | ForEach-Object { Remove-Item -LiteralPath ('Env:' + $_.Name) }
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
$env:HF_HUB_OFFLINE = $env:TRANSFORMERS_OFFLINE = '1'
$results = @()
for ($i=1; $i -le $Runs; $i++) {
    $run = Join-Path $env:TEMP ('LocalASR-startup-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $run | Out-Null
    $env:LOCALAPPDATA = Join-Path $run 'User'
    $env:HF_HOME = Join-Path $run 'EmptyCache'
    $report = Join-Path $run 'startup.json'
    $env:LOCALASR_LAUNCH_UNIX = ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000).ToString([cultureinfo]::InvariantCulture)
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process -FilePath $exe -WorkingDirectory $run -ArgumentList ('--packaged-check --offline --startup-only --report "{0}"' -f $report) -PassThru
    $window = $null
    $ready = $null
    while (-not $p.HasExited -and $watch.Elapsed.TotalSeconds -lt 120) {
        $p.Refresh()
        if ($null -eq $window -and $p.MainWindowHandle -ne 0) { $window = $watch.Elapsed.TotalSeconds }
        if ($null -eq $ready -and (Test-Path -LiteralPath $report)) { $ready = $watch.Elapsed.TotalSeconds }
        Start-Sleep -Milliseconds 50
    }
    if (-not $p.HasExited) { throw "Startup timed out; process $($p.Id) requires inspection" }
    if (-not (Test-Path -LiteralPath $report)) { throw "Startup report missing; process exit $($p.ExitCode)" }
    if ($null -eq $ready) { $ready = $watch.Elapsed.TotalSeconds }
    $details = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if (-not $details.first_run_dialog -or -not $details.missing_model_prompt) { throw 'Startup checks failed' }
    Copy-Item -LiteralPath $report -Destination (Join-Path $destination "startup-$i.json")
    $results += @{run=$i; first_window_seconds=$window; startup_probe_finished_seconds=$ready;
        internal_timings=$details.timings; exit_code=$p.ExitCode}
}
@{executable=$exe; method='Fresh processes; new user data; Windows file cache NOT cleared; 50ms observation interval'; runs=$results} |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $destination 'timings.json') -Encoding utf8
$results | ConvertTo-Json -Depth 5
