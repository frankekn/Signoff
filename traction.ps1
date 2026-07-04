$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$Root\src;$env:PYTHONPATH"
python -m traction @args
