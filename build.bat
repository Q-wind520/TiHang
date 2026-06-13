@echo off
REM ================================================================
REM  Nuitka Build Script for 题航 TiHang
REM  Usage: .\build.bat
REM  Prerequisites: pip install nuitka (installed in .venv)
REM ================================================================

cd /d "%~dp0"

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [2/2] Building TiHang standalone executable...
echo This may take 10-20 minutes on first build...

python -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --enable-plugins=pyside6 ^
    --windows-console-mode=disable ^
    --include-data-dir=data=data ^
    --include-data-dir=assets=assets ^
    --output-dir=builder ^
    --output-filename=tihang.exe ^
    --remove-output ^
    run.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================
    echo   Build successful!
    echo   Output: builder\run.dist\tihang.exe
    echo ==============================================================
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)
pause
