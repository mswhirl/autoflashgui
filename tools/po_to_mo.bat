@ECHO OFF

SET PROGRAM-NAME=autoflashgui
SET FILE-NAME=autoflashgui
SET MSGFMT-OPTIONS=
CLS
ECHO ******************************************
ECHO * %PROGRAM-NAME%
ECHO * Convert PO files in MO files *
ECHO ******************************************
ECHO.
ECHO.
ECHO      #### Press any key to continue ####
ECHO      ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ******************************************
ECHO * %PROGRAM-NAME%
ECHO * Convert PO files in MO files *
ECHO ******************************************
ECHO.

for %%x in (it) do (

ECHO **** Country = %%x - Compiling '%FILE-NAME%.po' in '%FILE-NAME%.mo'....
msgfmt %MSGFMT-OPTIONS% ..\locale\%%x\lc_messages\%FILE-NAME%.po -o ..\locale\%%x\lc_messages\%FILE-NAME%.mo > NUL
ECHO.
)

ECHO.
ECHO.
ECHO      #### Press any key to exit ####

PAUSE > NUL

SET PROGRAM-NAME=
SET FILE-NAME=
SET MSGFMT-OPTIONS=

