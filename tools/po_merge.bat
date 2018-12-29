@ECHO OFF
SETLOCAL EnableExtensions 
SET PROGRAM-NAME=autoflashgui
SET FILE-NAME=autoflashgui

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Update language files using master template
ECHO ********************************************************
ECHO.
ECHO.
ECHO            #### Press any key to continue ####
ECHO            ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Update language files using master template
ECHO ********************************************************

for %%x in (it) do (

ECHO **** Country = %%x - Merging '%FILE-NAME%.po' with '%FILE-NAME%.pot' template....
msgmerge  -U -q -N --backup=none ..\locale\%%x\lc_messages\%FILE-NAME%.po ..\locale\%FILE-NAME%.pot >NUL
ECHO **** Country = %%x - Cleaning obsolete entries from '%FILE-NAME%.po'....
msgattrib --no-obsolete ..\locale\%%x\lc_messages\%FILE-NAME%.po > ..\locale\%%x\lc_messages\%FILE-NAME%_new.po
copy ..\locale\%%x\lc_messages\%FILE-NAME%_new.po ..\locale\%%x\lc_messages\%FILE-NAME%.po >NUL
del ..\locale\%%x\lc_messages\%FILE-NAME%_new.po >NUL
ECHO **** Country = %%x - Statistics about '%FILE-NAME%.po'....
msgfmt --statistics ..\locale\%%x\lc_messages\%FILE-NAME%.po
ECHO *******************************************************

)

if exist Messages.mo del Messages.mo > NUL

ECHO.
ECHO.
ECHO      #### Press any key to exit #####
PAUSE > NUL

SET PROGRAM-NAME=
SET FILE-NAME=

