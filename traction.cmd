@echo off
set "ROOT=%~dp0"
set "RUNTIME=%ROOT%src"
set "PYTHONDONTWRITEBYTECODE=1"
cd /d "%RUNTIME%"
set "PYTHONPATH=%RUNTIME%;%PYTHONPATH%"
python -m traction --project "%ROOT%" %*
