param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [string]$Source = (Split-Path $PSScriptRoot -Parent),
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath $Source).Path.TrimEnd('\','/')
$targetRoot = [IO.Path]::GetFullPath($Destination).TrimEnd('\','/')
if ($targetRoot -eq $sourceRoot -or $targetRoot.StartsWith($sourceRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or $sourceRoot.StartsWith($targetRoot+'\',[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Source and destination must be separate, non-overlapping directories'
}
# Explicit public roots/extensions; never copy a whole workspace then delete.
$rootNames = @('.gitignore','build.ps1','README.md','README_EN.md','LICENSE',
    'COMMERCIAL_LICENSE.md','SECURITY.md','PRIVACY.md','THIRD_PARTY_NOTICES.md',
    'CONTRIBUTING.md','RELEASE_NOTES_TEMPLATE.md','RELEASE_NOTES_0.1.0.md',
    'requirements.txt','requirements-realtime.txt','requirements-translation.txt','requirements-build.txt')
$extensions = @{
    src=@('.py','.json'); tests=@('.py','.json'); distribution=@('.py','.ps1','.spec','.iss','.md');
    docs=@('.md','.png','.jpg','.svg'); '.github'=@('.md','.yml','.yaml')
}
$excludedDirectories = @('__pycache__','.pytest_cache','.cache','vendor','third_party_licenses','.git')
function PublicFiles([string]$Directory, [string[]]$Allowed) {
    foreach ($item in Get-ChildItem -LiteralPath $Directory -Force) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in public source tree; review manually' }
        if ($item.PSIsContainer) {
            if ($item.Name -notin $excludedDirectories) { PublicFiles $item.FullName $Allowed }
        } elseif ($item.Extension -in $Allowed) { $item }
    }
}
$files = @($rootNames | ForEach-Object { Get-Item -LiteralPath (Join-Path $sourceRoot $_) })
foreach ($root in $extensions.Keys) { $files += @(PublicFiles (Join-Path $sourceRoot $root) $extensions[$root]) }
$manifest = @($files | Sort-Object FullName | ForEach-Object {
    if ($_.Length -gt 10MB) { throw 'Unexpected large public source file; review before copying' }
    [pscustomobject]@{path=$_.FullName.Substring($sourceRoot.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}
})
# Preflight before any writes. Existing different/unknown files are never overwritten.
if (Test-Path -LiteralPath $targetRoot) {
    if (-not (Test-Path -LiteralPath $targetRoot -PathType Container)) { throw 'Destination is not a directory' }
    foreach ($existing in Get-ChildItem -LiteralPath $targetRoot -Force -Recurse) {
        if ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Destination contains a reparse point' }
        if ($existing.PSIsContainer) { continue }
        $relative = $existing.FullName.Substring($targetRoot.Length+1).Replace('\','/')
        $entry = $manifest | Where-Object path -eq $relative
        if (-not $entry -or (Get-FileHash -LiteralPath $existing.FullName).Hash -ne $entry.sha256) {
            throw "Destination contains unknown or changed file: $relative. Review it or choose a new empty directory."
        }
    }
}
if (-not $DryRun) {
    foreach ($entry in $manifest) {
        $target = Join-Path $targetRoot $entry.path
        New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
        if (-not (Test-Path -LiteralPath $target)) { Copy-Item -LiteralPath (Join-Path $sourceRoot $entry.path) -Destination $target }
        if ((Get-FileHash -LiteralPath $target).Hash -ne $entry.sha256) { throw "Copy verification failed: $($entry.path)" }
    }
}
[pscustomobject]@{dry_run=[bool]$DryRun;count=$manifest.Count;bytes=($manifest|Measure-Object bytes -Sum).Sum;files=$manifest} | ConvertTo-Json -Depth 5

