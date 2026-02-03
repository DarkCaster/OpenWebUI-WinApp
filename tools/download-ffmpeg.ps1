#Requires -Version 5

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$extractPath = Join-Path $scriptPath "extract"

$ffmpegExe = Get-ChildItem -Path $scriptPath -Filter "ffmpeg.exe" | Select-Object -First 1
$ffplayExe = Get-ChildItem -Path $scriptPath -Filter "ffplay.exe" | Select-Object -First 1
$ffprobeExe = Get-ChildItem -Path $scriptPath -Filter "ffprobe.exe" | Select-Object -First 1

if ($ffmpegExe -and $ffplayExe -and $ffprobeExe) {
    Write-Host "ffmpeg applications already downloaded, skipping"
    exit 0
}

$ffmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/8.0.1/ffmpeg-8.0.1-full_build.zip"
$ffmpegSha256 = "467cde100a47ed4b03a897988aeb4a296890c1e2b2d2864204657d002bc5fb90"
$ffmpegZip = Join-Path $scriptPath "ffmpeg.zip"

Write-Host "Downloading ffmpeg..."
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing

Write-Host "Validating checksums..."
$ffmpegHash = (Get-FileHash -Path $ffmpegZip -Algorithm SHA256).Hash.ToLower()
if ($ffmpegHash -ne $ffmpegSha256) {
    Write-Host "ffmpeg archive checksum mismatch" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting"
if (Test-Path $extractPath) {
    Remove-Item -Path $extractPath -Recurse -Force
}
New-Item -Path $extractPath -ItemType Directory -Force | Out-Null
Write-Host "Extracting ffmpeg..."
Expand-Archive -Path $ffmpegZip -DestinationPath $extractPath -Force

$ffmpegExe = Get-ChildItem -Path $extractPath -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
if (-not $ffmpegExe) {
    Write-Host "ffmpeg.exe not found"
    exit 1
}

$ffplayExe = Get-ChildItem -Path $extractPath -Filter "ffplay.exe" -Recurse | Select-Object -First 1
if (-not $ffplayExe) {
    Write-Host "ffplay.exe not found"
    exit 1
}

$ffprobeExe = Get-ChildItem -Path $extractPath -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
if (-not $ffprobeExe) {
    Write-Host "ffprobe.exe not found"
    exit 1
}

$targetffmpegExePath = Join-Path $scriptPath "ffmpeg.exe"
$targetffplayExePath = Join-Path $scriptPath "ffplay.exe"
$targetffprobeExePath = Join-Path $scriptPath "ffprobe.exe"

Move-Item -Path $ffmpegExe.FullName -Destination $targetffmpegExePath -Force
Move-Item -Path $ffplayExe.FullName -Destination $targetffplayExePath -Force
Move-Item -Path $ffprobeExe.FullName -Destination $targetffprobeExePath -Force

Write-Host "Cleaning up..."
Remove-Item -Path $ffmpegZip -Force
Remove-Item -Path $extractPath -Recurse -Force

Write-Host "Done"
