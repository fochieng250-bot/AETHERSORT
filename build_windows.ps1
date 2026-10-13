$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# Auto-detect a compatible Python version via the py launcher
$pyTag = $null
foreach ($tag in @('-3.12', '-3.11', '-3.10')) {
    & py $tag --version *> $null
    if ($LASTEXITCODE -eq 0) { $pyTag = $tag; break }
}
if (-not $pyTag) {
    throw "No compatible Python (3.10-3.12) found. Run 'py --list' to see installed versions."
}
Write-Host "Using Python: $(py $pyTag --version)" -ForegroundColor Gray

Write-Host '== AetherSort Windows beta build ==' -ForegroundColor Cyan
& py $pyTag -m pip install --upgrade pip
& py $pyTag -m pip install -e . pyinstaller

Write-Host '== Running automated tests ==' -ForegroundColor Cyan
& py $pyTag -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; refusing to package.' }

Write-Host '== Building Windows application ==' -ForegroundColor Cyan
& py $pyTag -m PyInstaller --noconfirm --clean AetherSort.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

$release = Join-Path $PSScriptRoot 'dist\AetherSort'
if (-not (Test-Path (Join-Path $release 'AetherSort.exe'))) {
    throw 'Build output is missing AetherSort.exe.'
}
$docs = Join-Path $release 'docs'
New-Item -ItemType Directory -Force -Path $docs | Out-Null
Copy-Item README.md, PRIVACY_POLICY.md, EULA.md, SUPPORT.md, RELEASE_NOTES.md -Destination $docs

$checksum = (Get-FileHash (Join-Path $release 'AetherSort.exe') -Algorithm SHA256).Hash
Set-Content -Path (Join-Path $release 'SHA256SUM.txt') -Value "$checksum  AetherSort.exe" -Encoding ascii

Write-Host "Build complete: $release" -ForegroundColor Green
Write-Host 'Next: test on a clean Windows account, then build the installer using installer\AetherSort.iss and Inno Setup.'