import re

import cv2
import numpy as np
import pytesseract

from worker.pipeline.parsing.amount import (
    extract_amount_with_source,
    merge_payment_evidence,
)
from worker.pipeline.parsing.amountAnchors import (
    CURRENCY_PATTERNS,
    PAYMENT_PATTERNS,
    TOTAL_PATTERNS,
)
from worker.pipeline.preprocessing.image import enhance, preprocess_from_grayscale

PAYMENT_LABELS = {label for _pattern, label in PAYMENT_PATTERNS}
TOTAL_LABELS = {label for _pattern, label in TOTAL_PATTERNS}
CURRENCY_LABELS = {label for _pattern, label in CURRENCY_PATTERNS}

MONEY_HINTS = (
    "сум",
    "итог",
    "total",
    "грн",
    "оплат",
    "разом",
    "всього",
    "карт",
    "руб",
    "фіскал",
    "фискал",
)
AMOUNT_TOKEN = re.compile(r"(?<!\d)\d{1,5}[.,]\d{2}(?!\d)")
MULTIPLY_LINE = re.compile(r"\d+[.]?\s*[xх×X]\s*[\d\sOОoо.,]+\s*=")


def upscale(image: np.ndarray, factor: float = 2.0) -> np.ndarray:
    if image.shape[1] >= 1200:
        return image
    return cv2.resize(image, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)


def bottom_crop(gray: np.ndarray, ratio: float = 0.45) -> np.ndarray:
    height = gray.shape[0]
    start = max(0, int(height * (1.0 - ratio)))
    return gray[start:, :]


def score_ocr_text(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        return -1.0

    amounts = AMOUNT_TOKEN.findall(stripped)
    if not amounts:
        return 0.0

    lowered = stripped.lower()
    hints = sum(1 for hint in MONEY_HINTS if hint in lowered)
    multiply_lines = sum(1 for line in stripped.splitlines() if MULTIPLY_LINE.search(line))
    alnum = sum(character.isalnum() for character in stripped)
    ratio = alnum / len(stripped)
    unique_amounts = len(set(amounts))

    score = unique_amounts * 5.0 + hints * 8.0 + multiply_lines * 3.0
    score += ratio * 10.0
    score += min(len(stripped), 1200) / 200.0
    if hints and unique_amounts >= 2:
        score += 15.0

    amount, source = extract_amount_with_source(stripped)
    if amount is None:
        return score

    score += 8.0
    amount_token = f"{amount:.2f}"
    compact = stripped.replace(",", ".")
    if amount_token in compact:
        score += 12.0
    if source in PAYMENT_LABELS:
        score += 50.0
    elif source in TOTAL_LABELS:
        score += 25.0
    elif source in CURRENCY_LABELS:
        score += 10.0
    if re.search(
        rf"(карт\w*).{{0,20}}{re.escape(amount_token)}"
        rf"|{re.escape(amount_token)}.{{0,12}}грн",
        compact.lower(),
        re.S,
    ):
        score += 35.0
    return score


class TesseractEngine:
    def __init__(self, languages: str) -> None:
        self.languages = languages

    def recognize(self, image: np.ndarray) -> str:
        return self._run(image, "--psm 6")

    def recognize_receipt(self, gray: np.ndarray, variant: int = 0) -> str:
        enhanced = enhance(gray)
        scaled = upscale(enhanced)
        binary = preprocess_from_grayscale(gray, variant)
        binary_scaled = upscale(binary)
        bottom = enhance(bottom_crop(gray))
        bottom_scaled = upscale(bottom)

        candidates = [
            (scaled, "--psm 4"),
            (scaled, "--psm 6"),
            (bottom_scaled, "--psm 6"),
            (bottom_scaled, "--psm 4"),
            (enhanced, "--psm 6"),
            (binary_scaled, "--psm 6"),
            (binary, "--psm 4"),
        ]

        texts: list[str] = []
        best_text = ""
        best_score = -1.0
        for image, config in candidates:
            text = self._run(image, config)
            texts.append(text)
            score = score_ocr_text(text)
            if score > best_score:
                best_score = score
                best_text = text

        payment_evidence = merge_payment_evidence(texts)
        if payment_evidence:
            return f"{best_text}\n{payment_evidence}".strip()
        return best_text

    def _run(self, image: np.ndarray, config: str) -> str:
        return pytesseract.image_to_string(
            image,
            lang=self.languages,
            config=config,
        )
