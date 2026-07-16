"""
Phoneme recognizer abstraction layer.

Two backends, switchable via the PHONEME_BACKEND env var (same pattern as
the Ollama/Mistral auto-switching used elsewhere: keep the swap-point in
one place so the rest of the app doesn't care which model is loaded):

  - "allosaurus" (default): lightweight universal phone recognizer, CPU
    friendly, good match for 8GB RAM / no dedicated GPU. Lower ceiling on
    accuracy but noticeably faster to load and run.
  - "wav2vec2": facebook/wav2vec2-lv-60-espeak-cv-ft, a ~1.3GB wav2vec2
    model fine-tuned for phoneme recognition on the espeak phoneme set.
    More accurate, heavier: expect slower load and inference on CPU-only
    hardware. Requires `pip install transformers torch`.

Both backends return a plain list of phone strings so the rest of the
pipeline (g2p + align) never needs to know which one produced them.
"""

import os
from typing import List, Protocol


class PhonemeRecognizer(Protocol):
    def recognize(self, wav_path: str) -> List[str]: ...


class AllosaurusRecognizer:
    def __init__(self, model_name: str = "latest"):
        from allosaurus.app import read_recognizer
        # Downloads the pretrained model to ~/.allosaurus on first run.
        self.model = read_recognizer(model_name)

    def recognize(self, wav_path: str) -> List[str]:
        # lang_id='eng' narrows output to the English phone inventory
        # instead of the full cross-lingual set.
        result = self.model.recognize(wav_path, lang_id="eng")
        return result.split()


class Wav2Vec2PhonemeRecognizer:
    MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"

    def __init__(self):
        import torch
        from transformers import (
            Wav2Vec2ForCTC,
            Wav2Vec2Processor,
            Wav2Vec2FeatureExtractor,
            Wav2Vec2CTCTokenizer,
        )

        self._torch = torch
        try:
            self.processor = Wav2Vec2Processor.from_pretrained(self.MODEL_ID)
        except TypeError:
            # Some transformers versions mis-detect this checkpoint's
            # tokenizer during Processor.from_pretrained and raise
            # "Received a bool for argument tokenizer". Loading the
            # feature extractor and tokenizer explicitly sidesteps it.
            feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.MODEL_ID)
            tokenizer = Wav2Vec2CTCTokenizer.from_pretrained(self.MODEL_ID)
            self.processor = Wav2Vec2Processor(
                feature_extractor=feature_extractor, tokenizer=tokenizer
            )
        self.model = Wav2Vec2ForCTC.from_pretrained(self.MODEL_ID)
        self.model.eval()

    def recognize(self, wav_path: str) -> List[str]:
        import librosa

        audio, _ = librosa.load(wav_path, sr=16000, mono=True)
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
        with self._torch.no_grad():
            logits = self.model(inputs.input_values).logits
        predicted_ids = self._torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription.split()


def get_recognizer(backend: str = None) -> PhonemeRecognizer:
    backend = backend or os.getenv("PHONEME_BACKEND", "allosaurus")
    if backend == "wav2vec2":
        return Wav2Vec2PhonemeRecognizer()
    return AllosaurusRecognizer()
