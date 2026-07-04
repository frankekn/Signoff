@echo off
set "ROOT=%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONPATH=%ROOT%src;%PYTHONPATH%"
python -m traction %*
