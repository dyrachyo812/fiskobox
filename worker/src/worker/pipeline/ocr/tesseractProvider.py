import numpy as np
import pytesseract

from worker.pipeline.ocr.provider import OCRProvider
from worker.pipeline.ocr.result import OCRResult, WordConfidence
from worker.pipeline.ocr.tesseract import TesseractEngine


class TesseractOCR(OCRProvider):
    name = "tesseract"

    def __init__(self, languages: str) -> None:
        self.languages = languages
        self.engine = TesseractEngine(languages=languages)

    def extract_text(self, image: np.ndarray) -> OCRResult:
        raw_text = self.engine.recognize_receipt(image)
        words, average = self._word_confidences(image)
        return OCRResult(
            raw_text=raw_text,
            confidence=average,
            words_with_confidence=words,
            provider=self.name,
        )

    def _word_confidences(
        self, image: np.ndarray
    ) -> tuple[list[WordConfidence], float | None]:
        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT,
            )
        except Exception:
            return [], None

        words: list[WordConfidence] = []
        scores: list[float] = []
        texts = data.get("text", [])
        confs = data.get("conf", [])
        for text, conf in zip(texts, confs, strict=False):
            token = (text or "").strip()
            if not token:
                continue
            try:
                score = float(conf)
            except (TypeError, ValueError):
                continue
            if score < 0:
                continue
            normalized = score / 100.0
            words.append(WordConfidence(text=token, confidence=normalized))
            scores.append(normalized)

        if not scores:
            return words, None
        return words, sum(scores) / len(scores)
