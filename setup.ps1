# Native Windows setup (no WSL needed). Run from PowerShell in the project
# folder. If script execution is blocked, run this once first (affects only
# the current window):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "==> Checking network access to required hosts first"
python check_connectivity.py
Write-Host ""
$continue = Read-Host "Continue with setup? [Y/n]"
if ($continue -eq "n") { exit }

Write-Host "==> Checking for espeak-ng"
$espeakFound = Get-Command espeak-ng -ErrorAction SilentlyContinue
if (-not $espeakFound -and -not (Test-Path "C:\Program Files\eSpeak NG\espeak-ng.exe")) {
    Write-Host "espeak-ng not found. Options:"
    Write-Host "  Admin / normal install rights:"
    Write-Host "    Download the .msi (X64) from:"
    Write-Host "    https://github.com/espeak-ng/espeak-ng/releases"
    Write-Host "  No admin rights (Scoop, per-user, no admin needed):"
    Write-Host "    irm get.scoop.sh | iex"
    Write-Host "    scoop install espeak-ng"
    Write-Host ""
    Write-Host "Install it, then re-run this script."
    exit 1
}
Write-Host "espeak-ng found."

Write-Host "==> Python virtual environment"
python -m venv .venv
.\.venv\Scripts\Activate.ps1

Write-Host "==> Installing torch (CPU-only build first, falls back to PyPI default)"
pip install --upgrade pip -q
pip install torch --index-url https://download.pytorch.org/whl/cpu -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "    (CPU-only index unreachable, falling back to PyPI)"
    pip install torch -q
}

Write-Host "==> Installing the rest of requirements.txt"
pip install -r requirements.txt -q

Write-Host "==> Downloading the Allosaurus phone recognizer model (from GitHub releases)"
python -m allosaurus.bin.download_model -m latest

Write-Host ""
Write-Host "Setup done. TTS defaults to espeak-ng (no extra download needed)."
Write-Host "Next:"
Write-Host "  1. Make sure the Ollama app is running (installs as a background service)"
Write-Host "  2. ollama pull mistral        (or a smaller model, see README)"
Write-Host "  3. .venv\Scripts\Activate.ps1 ; streamlit run app.py"
