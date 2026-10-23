# Misarticulation Coach

A local-first speech-practice application that compares the phonemes produced in a recording with the expected phoneme sequence for a target word. It aims to surface possible sound substitutions, omissions, and additions rather than relying only on speech-to-text.

## Why phoneme-level feedback?

Automatic speech recognition may infer the intended word even when a sound is mispronounced. Comparing only the transcript with the target can therefore miss some articulation differences. This project instead aligns recognized phones with expected phones and displays their differences.

## Processing flow

```text
Audio recording
  -> audio preprocessing
  -> phoneme recognition
  -> target text-to-phoneme conversion
  -> phoneme sequence alignment
  -> difference summary
  -> optional coaching tip and pronunciation playback
```

The default recognizer and optional backends have different resource and model-download requirements. See the source configuration and troubleshooting notes before enabling optional models.

## Technology

- Python
- Streamlit
- Allosaurus phoneme recognition
- Phonemizer / espeak-ng for grapheme-to-phoneme conversion
- Sequence alignment
- SQLite practice history
- Optional local LLM coaching through Ollama
- Optional text-to-speech backends

## Setup

```bash
git clone https://github.com/parth656/misarticulation-coach.git
cd misarticulation-coach
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Install the system speech tools required by the configured phonemizer, such as `espeak-ng`, using your operating system's package manager. Optional recognizers or TTS backends may require additional packages and model weights.

## Configuration

Check the environment variables and configuration constants in the source before changing the recognizer or TTS backend. Keep the default path usable without API keys where possible, and never commit tokens or private audio.

## Testing and evaluation

A useful evaluation set should contain:
- Correct target pronunciations.
- Known substitutions, omissions, and insertions.
- Different recording devices and levels of background noise.
- Repeated trials to estimate score stability.

Report phoneme-level precision/recall or alignment accuracy on a documented dataset rather than treating a single score as a diagnosis.

## Privacy and limitations

Audio and practice history can be sensitive. Prefer local processing, explain where data is stored, and provide deletion controls. Results can be affected by accent, dialect, microphone quality, and recognizer errors. This is a practice tool, not a clinical diagnosis or a replacement for professional speech therapy.
