param(
    [string]$OldVersion = "0.5.0",
    [string]$NewVersion = "0.6.0"
)

$ErrorActionPreference = 'Stop'

Write-Host "Bumping PQL.Assert version from $OldVersion to $NewVersion..." -ForegroundColor Cyan

# Get repo root
$repoRoot = Split-Path $PSScriptRoot -Parent

# File patterns to update
$patterns = @(
    "$repoRoot\src\lib\*.tmdl",
    "$repoRoot\tests\model\TestingModel.SemanticModel\TMDLScripts\Load PQL*.tmdl",
    "$repoRoot\tests\model\TestingModel.SemanticModel\definition\functions.tmdl",
    "$repoRoot\tests\rls_model\RLS_Model.SemanticModel\definition\functions.tmdl"
)

$totalReplacements = 0
$filesModified = 0

# Write text back with the file's original BOM state (PowerShell 5.1's [Text.Encoding]::UTF8 always adds a BOM)
function Write-PreservingBom([string]$path, [string]$text) {
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($hasBom)))
}

foreach ($pattern in $patterns) {
    $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
        $originalContent = $content
        
        # Replace version
        $content = $content -replace "DAXLIB_PackageVersion = $OldVersion", "DAXLIB_PackageVersion = $NewVersion"
        # PQL.Assert.LibraryVersion returns the version as a literal
        $content = $content -replace "(function 'PQL\.Assert\.LibraryVersion' =\s*\(\)\s*=>\s*)`"$([regex]::Escape($OldVersion))`"", "`${1}`"$NewVersion`""

        if ($content -ne $originalContent) {
            Write-PreservingBom $file.FullName $content
            $replacements = ([regex]::Matches($originalContent, [regex]::Escape("DAXLIB_PackageVersion = $OldVersion"))).Count
            $totalReplacements += $replacements
            $filesModified++
            Write-Host "  Updated $($file.Name) ($replacements replacements)" -ForegroundColor Green
        }
    }
}

$manifestPath = "$repoRoot\src\manifest.daxlib"
$manifest = [System.IO.File]::ReadAllText($manifestPath, [System.Text.Encoding]::UTF8)
$newManifest = $manifest -replace "`"version`": `"$([regex]::Escape($OldVersion))`"", "`"version`": `"$NewVersion`""
if ($newManifest -ne $manifest) {
    Write-PreservingBom $manifestPath $newManifest
    $filesModified++
    Write-Host "  Updated manifest.daxlib" -ForegroundColor Green
}

Write-Host "`nVersion bump complete!" -ForegroundColor Cyan
Write-Host "  Files modified: $filesModified" -ForegroundColor Green
Write-Host "  Total replacements: $totalReplacements" -ForegroundColor Green
