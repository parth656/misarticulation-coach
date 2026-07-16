import json
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.g2p import text_to_phonemes
from core.align import align_phonemes, accuracy, errors_only
from core.phoneme_recognizer import get_recognizer
from core.feedback import generate_feedback
from core.tts import synthesize_to_file

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "history.db"
WORD_BANK_PATH = DATA_DIR / "practice_words.json"

st.set_page_config(page_title="Misarticulation Coach", page_icon="◈", layout="centered")

# ---------------------------------------------------------------- styling --
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
        h1, h2, h3 { font-family: 'Fraunces', serif; font-weight: 600; letter-spacing: -0.01em; }
        .stApp { background-color: #FAF8F4; }
        .ph-match { color: #6B7A63; }
        .ph-sub   { color: #B0512E; font-weight: 600; }
        .ph-omit  { color: #B0512E; font-weight: 600; opacity: 0.75; }
        .ph-add   { color: #3E5C76; font-weight: 600; }
        .phoneme-row { font-size: 1.4rem; letter-spacing: 0.04em; margin: 0.75rem 0 1rem 0; }
        .accuracy-badge {
            display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
            font-size: 0.85rem; font-weight: 500; background: #EFEBE3; color: #4A4640;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------- data --

def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT, category TEXT,
            expected TEXT, actual TEXT,
            accuracy REAL, timestamp TEXT
        )"""
    )
    conn.commit()
    conn.close()


def log_attempt(word, category, expected, actual, acc):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO attempts (word, category, expected, actual, accuracy, timestamp) VALUES (?,?,?,?,?,?)",
        (word, category, " ".join(expected), " ".join(actual), acc, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def recent_progress(limit=8):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT word, category, accuracy, timestamp FROM attempts ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


@st.cache_resource(show_spinner="Loading phoneme recognizer (first run only)...")
def load_recognizer():
    return get_recognizer()


def render_diff_html(ops) -> str:
    parts = []
    for op in ops:
        if op.op == "match":
            parts.append(f'<span class="ph-match">{op.expected}</span>')
        elif op.op == "sub":
            parts.append(f'<span class="ph-sub">{op.expected}\u2192{op.actual}</span>')
        elif op.op == "omit":
            parts.append(f'<span class="ph-omit">{op.expected}\u2715</span>')
        elif op.op == "add":
            parts.append(f'<span class="ph-add">+{op.actual}</span>')
    return " &nbsp; ".join(parts)


# ------------------------------------------------------------------- app ---

def main():
    init_db()

    st.title("Misarticulation Coach")
    st.caption(
        "Record a word, get a phoneme-level breakdown of what actually came out "
        "versus what should have — not just whether the word was \"understood.\""
    )

    with open(WORD_BANK_PATH) as f:
        word_bank = json.load(f)

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Focus sound", list(word_bank.keys()))
    with col2:
        options = word_bank[category]
        word_choice = st.selectbox("Word", options)

    target_word = (
        st.text_input("Custom word", value="", placeholder="type your own word instead")
        if word_choice == "your word here"
        else word_choice
    )

    st.divider()

    if not target_word:
        st.info("Pick or type a word above, then record yourself saying it.")
        return

    st.markdown(f"### Say: \u201c{target_word}\u201d")
    audio_value = st.audio_input("Record your attempt")

    if audio_value:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_value.getbuffer())
            wav_path = tmp.name

        try:
            recognizer = load_recognizer()
            with st.spinner("Analyzing pronunciation..."):
                expected = text_to_phonemes(target_word)
                actual = recognizer.recognize(wav_path)
                ops = align_phonemes(expected, actual)
                acc = accuracy(ops)
                errors = errors_only(ops)

            st.markdown(
                f'<span class="accuracy-badge">{acc:.0%} phoneme match</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f'<div class="phoneme-row">{render_diff_html(ops)}</div>', unsafe_allow_html=True)
            st.caption("green = correct \u00b7 rust = substitution/omission \u00b7 blue = extra sound")

            if errors:
                with st.spinner("Getting a coaching tip..."):
                    tip = generate_feedback(target_word, errors)
                st.info(tip)
            else:
                st.success("Every phoneme matched the expected pronunciation.")

            if st.button("\U0001F50A Hear correct pronunciation"):
                out_wav = str(DATA_DIR / "_correct_playback.wav")
                try:
                    synthesize_to_file(target_word, out_wav)
                    st.audio(out_wav)
                except FileNotFoundError as e:
                    st.warning(str(e))

            log_attempt(target_word, category, expected, actual, acc)

        finally:
            os.unlink(wav_path)

    with st.expander("Recent progress"):
        rows = recent_progress()
        if not rows:
            st.caption("No attempts logged yet.")
        else:
            for word, cat, acc, ts in rows:
                st.write(f"**{word}** ({cat}) \u2014 {acc:.0%} \u00b7 {ts[:16].replace('T', ' ')}")


if __name__ == "__main__":
    main()
