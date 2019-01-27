@ECHO OFF

SET FILE-COMPILE=autoflashgui

cd ..
cls
echo ******** Cleaning temporary file...

if exist __pycache__ rmdir /s /q __pycache__
if exist build       rmdir /s /q build
if exist dist        rmdir /s /q dist

if exist %FILE-COMPILE%.spec del %FILE-COMPILE%.spec > NUL
if exist %FILE-COMPILE%.exe  del %FILE-COMPILE%.exe  > NUL

ECHO.
ECHO.
ECHO   #### Press any key to exit ####

pause >NUL

SET FILE-COMPILE=
