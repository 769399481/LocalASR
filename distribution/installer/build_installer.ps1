param(
    [string]$Standalone,
    [string]$Compiler,
    [string]$OutputDirectory,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (-not $Standalone) { $Standalone = Join-Path $root 'dist/LocalASR-Phase14' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $root 'dist/release' }
$payload = (Resolve-Path -LiteralPath $Standalone).Path
$output = [IO.Path]::GetFullPath($OutputDirectory)
if ($output -eq $payload -or $output.StartsWith($payload + [IO.Path]::DirectorySeparatorChar)) { throw 'Output must be outside the payload' }
$versionSource = Get-Content -LiteralPath (Join-Path $root 'src/app_version.py') -Raw
$matchesFound = [regex]::Matches($versionSource, '(?m)^APP_VERSION\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$')
if ($matchesFound.Count -ne 1) { throw 'Expected one APP_VERSION in src/app_version.py' }
$version = $matchesFound[0].Groups[1].Value
foreach ($name in @('LocalASR.exe','_internal/python311.dll','_internal/model_catalog.json','_internal/torch/lib/torch_cpu.dll','_internal/third_party_licenses')) {
    if (-not (Test-Path -LiteralPath (Join-Path $payload $name))) { throw "Missing payload: $name" }
}
$files = @(Get-ChildItem -LiteralPath $payload -Recurse -File)
if ($files | Where-Object { $_.Name -eq 'model.bin' -or $_.Name -like 'pytorch_model*.bin' -or $_.Extension -eq '.safetensors' }) { throw 'Model weights must not be installed with app files' }
$exeVersion = (Get-Item -LiteralPath (Join-Path $payload 'LocalASR.exe')).VersionInfo.ProductVersion
if ($exeVersion -ne $version) { throw "Payload version $exeVersion differs from source $version" }
if (-not $Compiler) {
    $candidates = @((Join-Path $root 'tools/InnoSetup/ISCC.exe'), (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6/ISCC.exe'))
    $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Compiler -or -not (Test-Path -LiteralPath $Compiler)) { throw 'Install official Inno Setup 6 or pass -Compiler <ISCC.exe>' }
$Compiler = (Resolve-Path -LiteralPath $Compiler).Path
$artifact = Join-Path $output "LocalASR-Setup-$version-win64.exe"
if ($CheckOnly) { [pscustomobject]@{version=$version;payload=$payload;bytes=($files|Measure-Object Length -Sum).Sum;compiler=$Compiler;artifact=$artifact}; return }
if (Test-Path -LiteralPath $artifact) { throw 'Installer already exists; use a new output directory to preserve it' }
if (Test-Path -LiteralPath (Join-Path $output 'SHA256SUMS.txt')) { throw 'Checksum file exists; use a new output directory' }
New-Item -ItemType Directory -Force -Path $output | Out-Null
$watch = [Diagnostics.Stopwatch]::StartNew()
& $Compiler /Qp "/DAppVersion=$version" "/DPayloadDir=$payload" "/DProjectRoot=$root" "/DArtifactDir=$output" (Join-Path $PSScriptRoot 'LocalASR.iss')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $artifact)) { throw 'Installer compilation failed' }
$watch.Stop()
& (Join-Path $root 'distribution/checksums.ps1') -Files $artifact -Output (Join-Path $output 'SHA256SUMS.txt')
$sourceBytes = ($files | Measure-Object Length -Sum).Sum
$installerBytes = (Get-Item -LiteralPath $artifact).Length
$summary = [ordered]@{version=$version;app_id='{013B05DD-FB78-45E4-8C99-1256B77D01F2}';standalone_bytes=$sourceBytes;installer_bytes=$installerBytes;installer_to_payload_ratio=($installerBytes/$sourceBytes);compile_seconds=$watch.Elapsed.TotalSeconds;sha256=(Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash;signing=(Get-AuthenticodeSignature -LiteralPath $artifact).Status.ToString();compiler_sha256=(Get-FileHash -LiteralPath $Compiler).Hash;artifact=[IO.Path]::GetFileName($artifact)}
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'build-summary.json') -Encoding utf8
$summary | ConvertTo-Json
