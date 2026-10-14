param([ValidateSet('full','optimized')][string]$Variant = 'optimized')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
conda run -n asr --no-capture-output python distribution/build.py --variant $Variant
if ($LASTEXITCODE -ne 0) { throw 'Standalone build failed' }
