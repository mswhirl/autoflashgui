@ECHO OFF
cd ..
cls
echo ******** Cleaning temporary file...

if exist __pycache__ rmdir /s /q __pycache__
if exist build       rmdir /s /q build
if exist dist        rmdir /s /q dist

if exist autoflashgui.spec del autoflashgui.spec > NUL
if exist autoflashgui.exe  del autoflashgui.exe  > NUL

ECHO.
ECHO.
ECHO   #### Press any key to exit ####

pause >NUL
