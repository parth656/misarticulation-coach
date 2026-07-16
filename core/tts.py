"""
TTS for the "hear correct pronunciation" playback.

Two backends, switchable via TTS_BACKEND (same abstraction pattern as
PHONEME_BACKEND in phoneme_recognizer.py):

  - "espeak" (default): shells out to the espeak-ng binary you already
    installed for phonemizer's G2P step. Zero extra downloads, zero extra
    network dependency — it's a rule-based synthesizer, not a neural one,
    so it sounds more robotic, but it needs nothing beyond what's already
    on disk.
  - "piper": nicer, more natural neural voice — BUT piper's voice files
    are hosted on huggingface.co (rhasspy/piper-voices), so this will
    fail on a network that blocks Hugging Face (which is exactly the
    kind of destination "AI Access" / CASB policies like Cisco Secure
    Access commonly flag). Use this only once you've confirmed
    huggingface.co is actually reachable — see check_connectivity.py.
"""

import os
import subprocess
import wave
from pathlib import Path

from core.platform_utils import espeak_ng_binary

TTS_BACKEND = os.getenv("TTS_BACKEND", "espeak")
ESPEAK_VOICE = os.getenv("ESPEAK_VOICE", "en-us")

PIPER_VOICE_MODEL = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
PIPER_VOICE_DIR = Path(os.getenv("PIPER_VOICE_DIR", "./voices"))

_piper_voice_cache = {}


def _synthesize_espeak(text: str, out_path: str) -> str:
    subprocess.run(
        [espeak_ng_binary(), "-v", ESPEAK_VOICE, "-w", out_path, text],
        check=True,
        capture_output=True,
    )
    return out_path


def _load_piper_voice():
    from piper import PiperVoice

    if "voice" not in _piper_voice_cache:
        model_path = PIPER_VOICE_DIR / f"{PIPER_VOICE_MODEL}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper voice not found at {model_path}. Download it with:\n"
                f"  python -m piper.download_voices --data-dir {PIPER_VOICE_DIR} {PIPER_VOICE_MODEL}\n"
                f"This requires huggingface.co to be reachable — run "
                f"check_connectivity.py first if you're on a filtered network."
            )
        _piper_voice_cache["voice"] = PiperVoice.load(str(model_path))
    return _piper_voice_cache["voice"]


def _synthesize_piper(text: str, out_path: str) -> str:
    voice = _load_piper_voice()
    with wave.open(out_path, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    return out_path


def synthesize_to_file(text: str, out_path: str, backend: str = None) -> str:
    backend = backend or TTS_BACKEND
    if backend == "piper":
        return _synthesize_piper(text, out_path)
    return _synthesize_espeak(text, out_path)


if __name__ == "__main__":
    path = synthesize_to_file("rabbit", "/tmp/_tts_test.wav")
    print("wrote", path)
