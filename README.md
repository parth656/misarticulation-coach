# Misarticulation Coach

Record yourself saying a word, get a **phoneme-level** breakdown of what
actually came out versus what should have. Free, fully local — no API
keys, nothing leaves your machine.

## Why phoneme-level, not just Whisper

Standard speech-to-text is trained to guess the *intended* word even when
it's mispronounced — say "wabbit" and most ASR will still transcribe
"rabbit". Comparing transcribed text to a target word won't catch a
misarticulation; it'll usually just look "correct." This app instead
recognizes the actual phones produced and diffs them against the expected
phoneme sequence.

## How it works

```
mic recording (st.audio_input)
        |
        v
phoneme recognizer  --->  actual phones     ["w", "æ", "b", "ɪ", "t"]
(Allosaurus, or optionally wav2vec2-lv-60-espeak-cv-ft)
                                  \
target word  --->  G2P (phonemizer/espeak)  expected phones  ["ɹ", "æ", "b", "ɪ", "t"]
                                  /
                    Needleman-Wunsch alignment
                                  |
                                  v
                    diff: match / sub / omit / add
                        /                    \
                       v                      v
              Ollama coaching tip      espeak-ng TTS playback
              (local Mistral, etc.)    of correct pronunciation
                                       (or optionally Piper, nicer voice)
```

Both phoneme recognizer options and the G2P step use the **same espeak
phoneme inventory**, which matters — comparing two different phoneme sets
would flag false errors everywhere.

## Behind Cisco SSE / corporate network filtering

This is built specifically to work with a Cisco Secure Access (or similar
SSE/CASB) block in place. Some background on why, and what changed from
an unrestricted setup:

Cisco Secure Access ships an "AI Access" feature that specifically
identifies and can block generative-AI / ML platform traffic (separate
from ordinary developer traffic like GitHub or PyPI). In practice that
usually means **huggingface.co is the domain most likely to be blocked**,
while github.com, pypi.org, and OS package repos are far more likely to
be allowed (they're needed for basically any normal dev work, so IT teams
rarely restrict them even under strict AI policies).

Checked directly against this project's dependencies:

| Component | Downloads from | Status |
|---|---|---|
| Allosaurus (default phoneme backend) | `github.com` -> GitHub release asset CDN | GitHub-hosted, verified working — usually fine |
| phonemizer / espeak-ng (G2P + default TTS) | OS package manager, PyPI | no ML model download at all |
| wav2vec2 phoneme backend (optional) | `huggingface.co` | **likely blocked** |
| Piper TTS voices (optional) | `huggingface.co/rhasspy/piper-voices` | **likely blocked** — yes, even Piper's voice files live on HF |
| Ollama model pulls | `registry.ollama.ai` | separate concern, check with `check_connectivity.py` |

That last row about Piper is easy to miss — it looks like a fully
separate, self-contained local TTS tool, but the actual voice files it
downloads are hosted on Hugging Face. That's why this build defaults to
`TTS_BACKEND=espeak` (the espeak-ng binary you already have installed for
G2P) instead: zero marginal network dependency, just a more robotic voice.

**Run this first**, before anything else:
```bash
python3 check_connectivity.py
```
It's stdlib-only (no pip installs needed to run it) and tells you exactly
which of the hosts above are reachable on your current network, so you're
not guessing.

## Setup

```bash
chmod +x setup.sh
./setup.sh
```

This checks connectivity, installs `espeak-ng` (system package) and torch,
installs `requirements.txt`, and pre-downloads the Allosaurus model from
GitHub. Nothing here touches huggingface.co by default.

You'll also need Ollama running separately, same as your other projects:
```bash
ollama serve
ollama pull mistral
```
If `registry.ollama.ai` isn't reachable on this network but you've already
pulled a model elsewhere, Ollama can still serve it locally without
re-pulling.

## Running

```bash
source .venv/bin/activate
streamlit run app.py
```

## Configuration

Copy `.env.example` to `.env` and adjust, or just export these directly:

| Variable | Default | Notes |
|---|---|---|
| `PHONEME_BACKEND` | `allosaurus` | `allosaurus` (GitHub-hosted, default) or `wav2vec2` (heavier, more accurate, **needs huggingface.co**) |
| `TTS_BACKEND` | `espeak` | `espeak` (default, zero extra downloads) or `piper` (nicer voice, **needs huggingface.co**) |
| `OLLAMA_HOST` | `http://localhost:11434` | |
| `OLLAMA_MODEL` | `mistral` | swap for something smaller (e.g. `phi3`) if RAM is tight |
| `PIPER_VOICE` | `en_US-lessac-medium` | only read when `TTS_BACKEND=piper` |
| `PIPER_VOICE_DIR` | `./voices` | only read when `TTS_BACKEND=piper` |

## Hardware notes (Ryzen 5 5500U / 8GB RAM / integrated GPU)

Free + max accuracy + fast don't all max out together on this hardware —
this build defaults to **balanced**, and now also to **whatever actually
gets through the network**:

- **Allosaurus** by default: CPU-only, no GPU needed, noticeably lighter
  than the wav2vec2 option, and its model comes from GitHub rather than
  Hugging Face. Good enough to catch clear substitutions/omissions; not
  as sharp on subtle distortions.
- Switch `PHONEME_BACKEND=wav2vec2` for a real accuracy jump **only if**
  `check_connectivity.py` shows huggingface.co reachable — it's a ~1.3GB
  model, so also expect slower load/inference on CPU. Don't run it
  alongside a large Ollama model if RAM gets tight.
- Don't hold the phoneme model, Ollama, and TTS all doing heavy work at
  the exact same instant — the pipeline already runs them sequentially
  for this reason.

## Troubleshooting

- **`TypeError: Received a bool for argument tokenizer`** when using the
  `wav2vec2` backend — a known loader quirk on some `transformers`
  versions for this specific checkpoint. `phoneme_recognizer.py` already
  falls back to loading the feature extractor/tokenizer explicitly; if it
  still fails, try a different `transformers` version.
- **Allosaurus model download fails even though `github.com` is
  reachable** — the actual bytes come from a signed, expiring URL on
  `release-assets.githubusercontent.com` after a redirect; ask IT to
  confirm that host specifically isn't singled out.
- **"Piper voice not found"** — this means `TTS_BACKEND=piper` is set but
  huggingface.co isn't reachable, or the voice hasn't been downloaded yet.
  Switch back to `TTS_BACKEND=espeak`, or download the voice from a
  network where HF works and copy the `.onnx` + `.onnx.json` files into
  `PIPER_VOICE_DIR` manually.
- **Coaching tip says Ollama unreachable** — make sure `ollama serve` is
  running in another terminal and the model in `OLLAMA_MODEL` has been
  pulled.
- **SSL/certificate errors on `pip install` itself** — a different symptom
  of the same kind of network, where the proxy does TLS inspection with
  its own certificate. If `check_connectivity.py` shows `TLS ERROR`
  anywhere, that's IT's corporate root CA needing to be trusted by
  Python/pip, not a code problem — ask IT for the CA bundle they expect
  you to install (`pip config set global.cert <path>` once you have it).

## Ideas for later (not built yet)

- Docker + Hugging Face Spaces deploy, like your other projects (note:
  the Spaces build environment itself has normal internet access, so the
  wav2vec2/Piper restrictions here are purely a local-machine concern)
- Per-sound progress charts (the SQLite table already logs every attempt)
- Swap the fixed word list for sentences / connected speech
- Timestamped phoneme output (Allosaurus supports `--timestamp=True`) to
  highlight *where in the recording* the error happened
