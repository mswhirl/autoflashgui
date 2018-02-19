rmdir /s /q dist build __pycache__
del autoflashgui.spec
del autoflashgui.7z
pyinstaller autoflashgui.py
mkdir dist\autoflashgui\sources
copy autoflashgui.py dist\autoflashgui\sources
copy mysrp.py dist\autoflashgui\sources
copy defaults.ini dist\autoflashgui
"c:\Program Files\7-Zip\7z.exe" a -mx9 -spe autoflashgui.7z .\dist\*

pause