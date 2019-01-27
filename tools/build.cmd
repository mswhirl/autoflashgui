@echo off
cls

SET FILE-COMPILE=autoflashgui

cd..

echo ******** Cleaning temporary file...
if exist __pycache__ rmdir /s /q __pycache__
if exist build       rmdir /s /q build
if exist dist        rmdir /s /q dist
if exist %FILE-COMPILE%.spec del %FILE-COMPILE%.spec > NUL
if exist %FILE-COMPILE%.exe del %FILE-COMPILE%.exe > NUL 
ECHO.
ECHO ******** Creating %FILE-COMPILE% installer...
ECHO.
pyinstaller --distpath ./ --onefile %FILE-COMPILE%.py

if not exist %FILE-COMPILE%.exe goto no.exe.file

ECHO.
ECHO ******** Compilation OK!
if exist build       rmdir /s /q build
if exist %FILE-COMPILE%.spec del %FILE-COMPILE%.spec > NUL
goto end

:no.exe.file
ECHO.
ECHO ******** Compilation error!
ECHO File '%FILE-COMPILE%.exe' not available in 'dist' folder!

:end
ECHO.
ECHO.
ECHO   #### Press any key to exit ####
pause >NUL

if exist __pycache__ rmdir /s /q __pycache__
if exist dist        rmdir /s /q dist

SET FILE-COMPILE=
