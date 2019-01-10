@echo off
cls

cd..

echo ******** Cleaning temporary file...
if exist __pycache__ rmdir /s /q __pycache__
if exist build       rmdir /s /q build
if exist dist        rmdir /s /q dist
if exist autoflashgui.spec del autoflashgui.spec > NUL
if exist autoflashgui.exe del autoflashgui.exe > NUL 
ECHO.
ECHO ******** Creating autoflashgui installer...
ECHO.
pyinstaller --distpath ./ --onefile autoflashgui.py

if not exist autoflashgui.exe goto no.exe.file

ECHO.
ECHO ******** Compilation OK!
if exist build       rmdir /s /q build
if exist autoflashgui.spec del autoflashgui.spec > NUL
goto end

:no.exe.file
ECHO.
ECHO ******** Compilation error!
ECHO File 'autoflashgui.exe' not available in 'dist' folder!

:end
ECHO.
ECHO.
ECHO   #### Press any key to exit ####
pause >NUL

if exist __pycache__ rmdir /s /q __pycache__
if exist dist        rmdir /s /q dist

