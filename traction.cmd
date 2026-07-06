@echo off
set "ROOT=%~dp0"
set "RUNTIME=%ROOT%src"
set "PYTHONDONTWRITEBYTECODE=1"
set "TRACTION_CALLER_CWD=%CD%"
pushd "%RUNTIME%"
set "PYTHONPATH=%RUNTIME%;%PYTHONPATH%"
python -m traction --project "%ROOT%" %*
set "EXITCODE=%ERRORLEVEL%"
popd
exit /b %EXITCODE%
