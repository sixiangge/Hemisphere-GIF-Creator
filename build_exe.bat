@echo off
cd /d "%~dp0"
echo ============================================
echo   Hemisphere GIF - Build EXE
echo ============================================
echo.

REM Install PyInstaller if not present
pip install pyinstaller 2>&1

echo.
echo Building EXE...
pyinstaller --onefile --windowed --name "HemisphereGIF" ^
    --hidden-import PIL ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import numpy ^
    --add-data "hemisphere_gif.py;." ^
    hemisphere_gui.py

echo.
echo ============================================
echo   Build complete!
echo   EXE location: dist\HemisphereGIF.exe
echo ============================================
pause
