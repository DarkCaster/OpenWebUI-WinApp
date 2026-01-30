#Requires -Version 5

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$extractPath = Join-Path $scriptPath "extract"

$upxUrl = "https://github.com/upx/upx/releases/download/v5.1.0/upx-5.1.0-win64.zip"
$uvUrl = "https://github.com/astral-sh/uv/releases/download/0.9.26/uv-x86_64-pc-windows-msvc.zip"

$upxSha256 = "41c7492edeed0f7e67d347ca9e8d2131e2af7ca7a7695f92283a8e655c251c13"
$uvSha256 = "eb02fd95d8e0eed462b4a67ecdd320d865b38c560bffcda9a0b87ec944bdf036"

$upxZip = Join-Path $scriptPath "upx.zip"
$uvZip = Join-Path $scriptPath "uv.zip"

Write-Host "Downloading UPX..."
Invoke-WebRequest -Uri $upxUrl -OutFile $upxZip -UseBasicParsing

Write-Host "Downloading UV..."
Invoke-WebRequest -Uri $uvUrl -OutFile $uvZip -UseBasicParsing

Write-Host "Validating checksums..."
$upxHash = (Get-FileHash -Path $upxZip -Algorithm SHA256).Hash.ToLower()
if ($upxHash -ne $upxSha256) {
    Write-Host "UPX archive checksum mismatch" -ForegroundColor Red
    exit 1
}
$uvHash = (Get-FileHash -Path $uvZip -Algorithm SHA256).Hash.ToLower()
if ($uvHash -ne $uvSha256) {
    Write-Host "UPX archive checksum mismatch"
    exit 1
}

Write-Host "Extracting"
if (Test-Path $extractPath) {
    Remove-Item -Path $extractPath -Recurse -Force
}
New-Item -Path $extractPath -ItemType Directory -Force | Out-Null
Write-Host "Extracting UPX..."
Expand-Archive -Path $upxZip -DestinationPath $extractPath -Force
Write-Host "Extracting UV"
Expand-Archive -Path $uvZip -DestinationPath $extractPath -Force


$upxExe = Get-ChildItem -Path $extractPath -Filter "upx.exe" -Recurse | Select-Object -First 1
$uvExe = Get-ChildItem -Path $extractPath -Filter "uv.exe" -Recurse | Select-Object -First 1
if (-not $upxExe) {
    Write-Host "upx.exe not found"
    exit 1
}
if (-not $uvExe) {
    Write-Host "uv.exe not found"
    exit 1
}
Write-Host "Compressing uv.exe with UPX..."

$uvDirectory = Split-Path -Parent $uvExe.FullName
Push-Location $uvDirectory
& $upxExe.FullName "uv.exe" --brute
Pop-Location

$targetUvPath = Join-Path $scriptPath "uv.exe"
if (Test-Path $targetUvPath) {
    Remove-Item -Path $targetUvPath -Force
}
Move-Item -Path $uvExe.FullName -Destination $targetUvPath -Force

Write-Host "uv.exe moved to: $targetUvPath"

Write-Host "Cleaning up..."
Remove-Item -Path $upxZip -Force
Remove-Item -Path $uvZip -Force
Remove-Item -Path $extractPath -Recurse -Force

Write-Host "Done"
