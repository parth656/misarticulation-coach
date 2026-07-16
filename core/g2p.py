"""
Grapheme-to-phoneme (G2P): turns the target word/sentence text into the
phoneme sequence a correct pronunciation should produce.

Deliberately uses phonemizer's espeak backend (not g2p_en/ARPAbet) because
that's the SAME phoneme inventory the espeak-trained wav2vec2 phoneme
recognizer (facebook/wav2vec2-lv-60-espeak-cv-ft) was trained on, and a
close cousin of what Allosaurus's IPA output looks like. Mismatched
phoneme sets would make every comparison look like an error even when
pronunciation was correct.
"""

from phonemizer import phonemize
from phonemizer.separator import Separator

from core.platform_utils import ensure_espeak_configured

ensure_espeak_configured()


def text_to_phonemes(text: str, language: str = "en-us") -> list[str]:
    result = phonemize(
        text,
        language=language,
        backend="espeak",
        separator=Separator(phone=" ", word="|"),
        strip=True,
        with_stress=False,
    )
    # result looks like "ɹ æ b ɪ t" for one word, or "w ʌ n|t uː" for two
    return result.replace("|", " ").split()


if __name__ == "__main__":
    for w in ["rabbit", "thumb", "yellow", "squirrel", "the quick fox"]:
        print(w, "->", text_to_phonemes(w))
