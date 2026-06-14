@echo off
REM ================================================================
REM  Build Script for 题航 TiHang (using PyInstaller)
REM  Usage: .\build.bat
REM ================================================================

cd /d "%~dp0"

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/2] Building TiHang with PyInstaller...
echo This may take 2-5 minutes...

pyinstaller ^
    --name=tihang ^
    --windowed ^
    --onedir ^
    --add-data="data;data" ^
    --add-data="assets;assets" ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=shiboken6 ^
    --hidden-import=openai ^
    --hidden-import=anthropic ^
    --hidden-import=Pygments ^
    --hidden-import=PyPDF2 ^
    --clean ^
    --noconfirm ^
    run.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================
    echo   Build successful!
    echo   Output: dist\tihang\tihang.exe
    echo ==============================================================
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)
pause
