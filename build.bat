# build.bat - Đóng gói app thành file .exe
# Chạy: .\build.bat  (trong PowerShell hoặc CMD)

@echo off
echo ============================================
echo  Cai dat thu vien can thiet...
echo ============================================
pip install customtkinter requests Pillow pyinstaller

echo.
echo ============================================
echo  Dang dong goi thanh .exe ...
echo ============================================

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "Down and Merge Photos" ^
  --icon "app_icon.ico" ^
  --version-file "version_info.txt" ^
  --add-data "app_icon.ico;." ^
  --collect-all customtkinter ^
  app.py

echo.
echo ============================================
echo  Hoan thanh! File .exe nam tai:
echo  dist\Down and Merge Photos.exe
echo ============================================
pause
