# Xabarnoma avtomatik yangilash (PowerShell)
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ""
Write-Host "===================================================="
Write-Host "  XABARNOMA - Avtomatik yangilash"
Write-Host "===================================================="
Write-Host ""

$ZipUrl = "https://github.com/mexroj978-beep/my-first-project/archive/refs/heads/main.zip"
$ZipFile = Join-Path $env:TEMP "xabarnoma_update.zip"
$ExtractDir = Join-Path $env:TEMP "xabarnoma_extract"

Write-Host "[1/5] GitHub dan yuklanmoqda..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing

Write-Host "[2/5] Ochilyapti..."
if (Test-Path $ExtractDir) { Remove-Item $ExtractDir -Recurse -Force }
Expand-Archive -Path $ZipFile -DestinationPath $ExtractDir -Force

$Src = Join-Path $ExtractDir "my-first-project-main"
if (-not (Test-Path (Join-Path $Src "app"))) {
    Write-Host "[XATO] Fayllar topilmadi!" -ForegroundColor Red
    Read-Host "Enter bosing"
    exit 1
}

Write-Host "[3/5] Fayllar nusxalanmoqda..."
if (Test-Path "app") { Remove-Item "app" -Recurse -Force }
Copy-Item -Path "$Src\app" -Destination "app" -Recurse
if (Test-Path "scripts") { Remove-Item "scripts" -Recurse -Force }
Copy-Item -Path "$Src\scripts" -Destination "scripts" -Recurse

$Files = @("requirements.txt","start.py","run_bot.py","1_API.bat","2_BOT.bat",
           "TOXTATISH.bat","ishga_tushirish.bat","YANGILASH.bat",".env.example")
foreach ($f in $Files) {
    $from = Join-Path $Src $f
    if (Test-Path $from) { Copy-Item $from $f -Force }
}

Write-Host "[4/5] Kutubxonalar..."
if (-not (Test-Path "venv")) {
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3.12 -m venv venv }
    else { python -m venv venv }
}
& "venv\Scripts\pip.exe" install -r requirements.txt -q

Write-Host "[5/5] Tozalash..."
Remove-Item $ZipFile -Force -ErrorAction SilentlyContinue
Remove-Item $ExtractDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "MUVAFFAQIYATLI YANGILANDI!" -ForegroundColor Green
Write-Host ""
Read-Host "Enter bosing - dastur ishga tushadi"

Start-Process cmd -ArgumentList "/k cd /d `"$Root`" && venv\Scripts\activate && python start.py"
Start-Sleep 3
Start-Process "http://localhost:8000/admin"
