"""
Windows needs two things Linux/macOS mostly don't:
  1. phonemizer can't auto-find libespeak-ng.dll the way it finds the .so
     on Linux — it needs PHONEMIZER_ESPEAK_LIBRARY / PHONEMIZER_ESPEAK_PATH
     pointed at it explicitly.
  2. the espeak-ng.exe binary itself may not be on PATH after the .msi
     installer, depending on install options.

This checks the common install locations and sets the env vars / returns
a resolved binary path automatically, so g2p.py and tts.py don't need
platform-specific code duplicated in both places. No-op on Linux/macOS.
"""

import os
import platform
import shutil
from pathlib import Path

_CANDIDATE_DIRS = [
    Path(r"C:\Program Files\eSpeak NG"),
    Path(r"C:\Program Files (x86)\eSpeak NG"),
    Path.home() / "scoop" / "apps" / "espeak-ng" / "current" / "eSpeak NG",
]

_configured = False


def ensure_espeak_configured() -> None:
    """Set PHONEMIZER_ESPEAK_LIBRARY / PATH on Windows if not already set.
    Safe to call repeatedly; does nothing on non-Windows platforms or if
    the env vars are already present."""
    global _configured
    if _configured or platform.system() != "Windows":
        return

    if "PHONEMIZER_ESPEAK_LIBRARY" not in os.environ:
        for d in _CANDIDATE_DIRS:
            dll = d / "libespeak-ng.dll"
            if dll.exists():
                os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = str(dll)
                break

    if "PHONEMIZER_ESPEAK_PATH" not in os.environ:
        for d in _CANDIDATE_DIRS:
            exe = d / "espeak-ng.exe"
            if exe.exists():
                os.environ["PHONEMIZER_ESPEAK_PATH"] = str(exe)
                break

    _configured = True


def espeak_ng_binary() -> str:
    """Return the best command/path to invoke for the espeak-ng CLI
    (used for TTS), checking PATH first, then Windows install locations."""
    on_path = shutil.which("espeak-ng")
    if on_path:
        return on_path
    if platform.system() == "Windows":
        for d in _CANDIDATE_DIRS:
            exe = d / "espeak-ng.exe"
            if exe.exists():
                return str(exe)
    return "espeak-ng"  # fall back to bare command; will raise a clear error if missing
