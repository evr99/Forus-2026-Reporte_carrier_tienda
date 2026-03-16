@echo off
title Reporte Tienda-Carrier
color 0A

:: Verificar instalacion
if not exist "python\python.exe" (
    echo [ERROR] Python no encontrado.
    echo         Ejecuta primero: instalar.bat
    echo.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo [ERROR] No se encontro main.py
    echo         Verifica que todos los archivos del proyecto esten presentes.
    echo.
    pause
    exit /b 1
)

echo Iniciando Proyecto QWEN...
python\python.exe main.py

if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion cerro con un error.
    pause
)
