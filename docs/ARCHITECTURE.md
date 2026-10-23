# Misarticulation Coach Architecture

This guide follows the processing flow described in the project README and imports in `app.py`. Exact interfaces should be checked in the current source.

## Processing pipeline

```text
Target word + microphone recording
        |
        +--> Target grapheme-to-phoneme conversion
        |       (phonemizer / espeak)
        |
        +--> Audio preprocessing
                |
                v
          Phoneme recognizer
          (Allosaurus by default,
           optional alternate backend)
                |
                v
          Sequence alignment
                |
                v
          Match / substitution / omission / insertion
                |
                +--> Optional coaching feedback
                +--> Optional pronunciation playback
                +--> Session history (SQLite)
```

## Design rationale

Comparing a target word with an ordinary ASR transcript may miss articulation differences because ASR often infers the intended word. This project aims to compare phoneme sequences directly. The recognizer and target G2P system must use compatible phoneme inventories; mismatched inventories can create false errors.

## Modules referenced by the application

- `core.g2p`: target text to phonemes
- `core.align`: phoneme alignment and accuracy/error helpers
- `core.phoneme_recognizer`: recognizer selection
- `core.feedback`: coaching notes
- `core.tts`: pronunciation playback
- `app.py`: Streamlit UI and orchestration
- `data/`: local practice-word and history data

Confirm actual module names and function contracts if the code changes.

## Test strategy

1. Unit-test G2P output for representative words.
2. Test alignment with clean matches, substitutions, omissions, and insertions.
3. Test resampling, stereo-to-mono conversion, silence, and corrupted audio.
4. Compare predicted phones with manually reviewed examples.
5. Measure per-phoneme performance and false-positive rates across speakers and recording conditions.

## Privacy and safety

Keep processing local by default where possible. Treat audio and stored practice history as sensitive. Results are practice suggestions, not a diagnosis; encourage professional evaluation for persistent or concerning speech difficulties.
