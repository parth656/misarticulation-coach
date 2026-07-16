#!/usr/bin/env bash
# One-shot setup for Fedora / most Linux distros with an AMD integrated GPU
# (no CUDA) in mind. Run once, then `streamlit run app.py` each time after.
set -e

echo "==> Checking network access to required hosts first"
python3 check_connectivity.py || true
echo ""
read -p "Continue with setup? [Y/n] " reply
if [[ "$reply" =~ ^[Nn]$ ]]; then
    exit 0
fi

echo "==> System dependency: espeak-ng (G2P backend, and the default TTS engine)"
if command -v dnf &> /dev/null; then
    sudo dnf install -y espeak-ng
elif command -v apt-get &> /dev/null; then
    sudo apt-get install -y espeak-ng
else
    echo "Please install espeak-ng manually for your distro, then re-run."
    exit 1
fi

echo "==> Python virtual environment"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing torch (needed by Allosaurus). Trying the CPU-only build"
echo "    first — smaller, no CUDA — falling back to plain PyPI if that"
echo "    index isn't reachable on this network."
pip install --upgrade pip -q
pip install torch --index-url https://download.pytorch.org/whl/cpu -q \
    || { echo "    (CPU-only index unreachable, falling back to PyPI)"; pip install torch -q; }

echo "==> Installing the rest of requirements.txt"
pip install -r requirements.txt -q

echo "==> Downloading the Allosaurus phone recognizer model (from GitHub releases)"
python -m allosaurus.bin.download_model -m latest

echo ""
echo "Setup done — TTS defaults to the espeak-ng binary you just installed,"
echo "no extra download needed. (Optional: PHONEME_BACKEND=wav2vec2 and"
echo "TTS_BACKEND=piper are heavier/nicer upgrades that need huggingface.co —"
echo "see README before switching those on this network.)"
echo ""
echo "Next:"
echo "  1. In another terminal: ollama serve"
echo "  2. ollama pull mistral        (or a smaller model, see README)"
echo "  3. source .venv/bin/activate && streamlit run app.py"
