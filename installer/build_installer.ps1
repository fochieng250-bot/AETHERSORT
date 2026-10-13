$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$iss = Join-Path $PSScriptRoot 'AetherSort.iss'
$compilerCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$compiler = $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $compiler) {
    throw 'Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php and retry.'
}
New-Item -ItemType Directory -Force -Path 'dist\installer' | Out-Null
if (-not (Test-Path 'dist\AetherSort\AetherSort.exe')) {
    throw 'dist\AetherSort\AetherSort.exe not found. Run .\build_windows.ps1 first.'
}
& $compiler $iss
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }
Write-Host 'Installer created under dist\installer.' -ForegroundColor Green
