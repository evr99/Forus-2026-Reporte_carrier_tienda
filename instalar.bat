@echo off
title Instalador - Reporte Tiendas-Carrier
color 0A

echo ============================================
echo     INSTALADOR - Reporte Tiendas-Carrier
echo ============================================
echo.

:: Verificar que se ejecuta desde la carpeta correcta
if not exist "main.py" (
    echo [ERROR] Ejecuta instalar.bat desde la carpeta del proyecto.
    echo         La carpeta debe contener main.py
    pause
    exit /b 1
)

:: Si ya esta instalado, saltar descarga
if exist "python\python.exe" (
    echo [OK] Python embebido ya esta instalado.
    goto :instalar_deps
)

echo [1/3] Descargando Python 3.10.11 embebido...
echo       Esto puede tardar unos minutos...
echo.

if not exist "python" mkdir python

powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile 'python_embed.zip' -UseBasicParsing"

if not exist "python_embed.zip" (
    echo [ERROR] No se pudo descargar Python. Verifica tu conexion a internet.
    pause
    exit /b 1
)

echo [2/3] Extrayendo Python...
powershell -Command "Expand-Archive -Path 'python_embed.zip' -DestinationPath 'python' -Force"
del python_embed.zip

:: Habilitar site-packages usando Python para escribir el archivo limpio
python\python.exe -c "open('python/python310._pth','w').write('python310.zip\n.\nLib\\site-packages\nimport site\n')"

:: Verificar que site funciona
python\python.exe -c "import site" 2>nul
if errorlevel 1 (
    echo [ERROR] No se pudo configurar Python embebido.
    pause
    exit /b 1
)

:: Instalar pip
echo [3/3] Instalando pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing"
python\python.exe get-pip.py --quiet
del get-pip.py

python\python.exe -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no se instalo correctamente.
    pause
    exit /b 1
)

echo [OK] Python 3.10.11 listo.
echo.

:instalar_deps
echo ============================================
echo     INSTALANDO DEPENDENCIAS
echo ============================================
echo.
echo Este proceso puede tardar varios minutos.
echo.

python\python.exe -m pip install --upgrade pip --quiet --no-warn-script-location

echo [1/7] Instalando streamlit...
python\python.exe -m pip install streamlit "streamlit[charts]" --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo streamlit & pause & exit /b 1 )

echo [2/7] Instalando pywebview...
python\python.exe -m pip install pywebview --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo pywebview & pause & exit /b 1 )

echo [3/7] Instalando pywin32...
python\python.exe -m pip install pywin32 --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo pywin32 & pause & exit /b 1 )

echo [4/7] Instalando openvino...
python\python.exe -m pip install openvino --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo openvino & pause & exit /b 1 )

echo [5/7] Instalando optimum-intel...
python\python.exe -m pip install "optimum[openvino]" --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo optimum & pause & exit /b 1 )

echo [6/7] Instalando transformers...
python\python.exe -m pip install transformers accelerate --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo transformers & pause & exit /b 1 )

echo [7/7] Instalando pandas y openpyxl...
python\python.exe -m pip install pandas openpyxl --quiet --no-warn-script-location
if errorlevel 1 ( echo [ERROR] Fallo pandas/openpyxl & pause & exit /b 1 )

echo.
echo ============================================
echo     INSTALACION COMPLETADA
echo ============================================
echo.
echo Ahora puedes abrir la aplicacion con:
echo   iniciar.bat
echo.
pause
