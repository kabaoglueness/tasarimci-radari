@echo off
echo StudioFinder baslatiliyor...
start http://localhost:8090
python "%~dp0server.py"
pause
