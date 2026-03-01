# Script para ejecutar el bot y reiniciarlo automáticamente si se cae (corte de red, error, etc.)
# Uso: .\run_bot.ps1   (o hacer doble clic si PowerShell está asociado)

$botDir = $PSScriptRoot
$python = Join-Path $botDir "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "No se encuentra el entorno virtual. Ejecuta primero: python -m venv venv"
    Write-Host "Luego: .\venv\Scripts\python.exe -m pip install -r requirements.txt"
    pause
    exit 1
}

Set-Location $botDir
Write-Host "Bot de Gamer Tags - Reinicio automático activado."
Write-Host "Si el bot se cae por corte de red o error, se reiniciará en 10 segundos."
Write-Host "Para detener: cierra esta ventana o pulsa Ctrl+C."
Write-Host ""

while ($true) {
    & $python bot.py
    $exitCode = $LASTEXITCODE
    Write-Host ""
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] El bot terminó (código $exitCode). Reiniciando en 10 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}
