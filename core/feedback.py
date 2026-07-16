"""
Turns a phoneme-level diff into a short, plain-language coaching tip using
a local Ollama model. No cloud calls, no API key.
"""

import os
import requests
from typing import List
from core.align import PhonemeOp

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def _describe_error(op: PhonemeOp) -> str:
    if op.op == "sub":
        return f"expected /{op.expected}/ but produced /{op.actual}/"
    if op.op == "omit":
        return f"dropped the /{op.expected}/ sound entirely"
    if op.op == "add":
        return f"added an extra /{op.actual}/ sound that shouldn't be there"
    return ""


def generate_feedback(target_word: str, errors: List[PhonemeOp]) -> str:
    if not errors:
        return f"That matched the expected pronunciation of \"{target_word}\"."

    error_desc = "; ".join(_describe_error(e) for e in errors)
    prompt = (
        f"You are a friendly, concise speech coach. Someone tried to say the word "
        f"\"{target_word}\". A phoneme-level comparison against the correct pronunciation "
        f"found: {error_desc}. In 2-3 short sentences and plain language (no IPA symbols, "
        f"no clinical jargon), explain what likely happened and give one concrete physical "
        f"tip (tongue position, lips, airflow) to fix it."
    )

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        return (
            f"Found {len(errors)} sound mismatch(es) on \"{target_word}\", but the coaching "
            f"tip couldn't be generated (Ollama unreachable at {OLLAMA_HOST}: {e}). "
            f"Make sure `ollama serve` is running and `ollama pull {OLLAMA_MODEL}` has been run."
        )
