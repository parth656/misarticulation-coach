# Running on Windows

Native Windows, no WSL required. (If WSL is available to you — it needs
admin rights to enable, often blocked on managed corporate laptops — the
simpler path is just running the existing `setup.sh` unchanged inside a
WSL Ubuntu shell. Skip to the steps below if WSL isn't an option.)

Every step here is written as plain commands you can paste one at a time,
in case running `.ps1` scripts is blocked by execution policy on this
machine — `setup.ps1` bundles all of it if scripts *are* allowed.

## 0. Check connectivity first

```powershell
python check_connectivity.py
```
No installs needed to run this — pure standard library, works the same
on Windows. (If `python` isn't recognized, try `py` or `python3`.) This
still matters here — the Cisco SSE reasoning from before carries over
regardless of OS: huggingface.co is the one most likely to be blocked;
github.com and pypi.org almost never are.

## 1. Install espeak-ng

Needed for G2P and the default TTS voice.

**If you can install software normally:** download the `.msi` (X64 build,
for most machines) from the
[espeak-ng releases page](https://github.com/espeak-ng/espeak-ng/releases)
and run it. Default install path: `C:\Program Files\eSpeak NG\`.

**If you don't have admin/install rights** (common on managed corporate
laptops): [Scoop](https://scoop.sh) installs per-user, no admin needed.
```powershell
irm get.scoop.sh | iex
scoop install espeak-ng
```
If the first line errors with something about execution policy, run this
once first (only affects the current window, not a permanent change):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

You should **not** need to manually set `PHONEMIZER_ESPEAK_LIBRARY` /
`PHONEMIZER_ESPEAK_PATH` — `core/platform_utils.py` in this project checks
both the Program Files and Scoop install locations automatically at
startup. If you installed espeak-ng somewhere else entirely, set those two
env vars yourself, pointing at `libespeak-ng.dll` and `espeak-ng.exe`.

## 2. Python virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
cmd.exe instead of PowerShell: `.venv\Scripts\activate.bat`

## 3. Install packages

```powershell
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```
If that first `pip install torch` line fails to reach the CPU-only index
on this network, drop the `--index-url` flag and just `pip install torch`
— larger download, but works the same.

## 4. Download the Allosaurus model

```powershell
python -m allosaurus.bin.download_model -m latest
```
Same GitHub-hosted download verified earlier — no huggingface.co needed.

## 5. Ollama

Install the Windows app from [ollama.com](https://ollama.com) if you
haven't already. It installs as a background service, so you generally
don't need to run `ollama serve` manually — just:
```powershell
ollama pull mistral
```

## 6. Run it

```powershell
streamlit run app.py
```

## Everything else is unchanged

Defaults (`PHONEME_BACKEND=allosaurus`, `TTS_BACKEND=espeak`), the
`.env.example` variables, and all the troubleshooting notes in the main
`README.md` apply the same way on Windows — including the note about
SSL/certificate errors on `pip install` itself being a sign of TLS
inspection rather than a code problem.
