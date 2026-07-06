$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runtime = Join-Path $Root "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPATH = "$Runtime;$env:PYTHONPATH"
$env:TRACTION_CALLER_CWD = (Get-Location).Path
Push-Location -LiteralPath $Runtime
try {
  python -m traction --project $Root @args
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
