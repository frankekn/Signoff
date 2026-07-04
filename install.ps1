param(
  [string]$Target = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git is required."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python 3.10+ is required."
}

python -c "import sys; assert sys.version_info >= (3,10), 'Traction requires Python 3.10+'; print(f'Python {sys.version_info.major}.{sys.version_info.minor}: OK')"

if ($Target) {
  $ResolvedTarget = (Resolve-Path $Target).Path
  & "$Root\traction.ps1" --project $ResolvedTarget install
  Write-Host "`nInstalled into $ResolvedTarget"
  Write-Host "Next: cd $ResolvedTarget; .\traction.ps1 ui"
  exit 0
}

if (-not (Test-Path "$Root\src\traction\web_dist\index.html")) {
  throw "Prebuilt UI assets are missing. Run npm ci; npm run build:web."
}

& "$Root\traction.ps1" --version
python "$Root\scripts\check_repo.py"
Write-Host "`nTraction is ready."
Write-Host "Run: .\traction.ps1 ui"
Write-Host "Install into another repository: .\install.ps1 C:\path\to\repository"
