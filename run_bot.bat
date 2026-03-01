@echo off
REM Ejecuta el bot y lo reinicia automáticamente si se cae (corte de red, etc.)
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo No se encuentra el entorno virtual. Crea primero: python -m venv venv
    echo Luego: venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

:loop
echo.
echo Bot de Gamer Tags - Reinicio automático activado.
echo Si el bot se cae, se reiniciará en 10 segundos. Para detener: cierra esta ventana.
echo.
venv\Scripts\python.exe bot.py
echo.
echo [%time%] El bot terminó. Reiniciando en 10 segundos...
timeout /t 10 /nobreak > nul
goto loop
