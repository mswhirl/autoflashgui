rmdir /s /q dist build __pycache__
del autoflashgui.spec
del autoflashgui.exe
pyinstaller --onefile autoflashgui.py
copy dist\*.exe .
pause