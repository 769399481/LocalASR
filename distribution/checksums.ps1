param(
    [Parameter(Mandatory=$true)][string[]]$Files,
    [string]$Output = 'SHA256SUMS.txt'
)
$ErrorActionPreference = 'Stop'
$targets = @($Files | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
$outputPath = [IO.Path]::GetFullPath($Output)
if ($targets -contains $outputPath) { throw 'Checksum output must not replace an input file' }
if (Test-Path -LiteralPath $outputPath) { throw 'Output already exists; choose a new output path' }
$names = @($targets | ForEach-Object { [IO.Path]::GetFileName($_) })
if (@($names | Select-Object -Unique).Count -ne $names.Count) { throw 'Input basenames must be unique' }
$lines = foreach ($path in $targets) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Not a file: $path" }
    '{0}  {1}' -f (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant(), [IO.Path]::GetFileName($path)
}
[IO.File]::WriteAllLines($outputPath, [string[]]$lines, [Text.UTF8Encoding]::new($false))
