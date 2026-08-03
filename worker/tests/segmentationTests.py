import cv2
import numpy as np

from worker.pipeline.preprocessing.segmentation import count_receipts
from worker.pipeline.parsing.amount import extract_amount
from worker.pipeline.parsing.date import extract_date
from worker.pipeline.parsing.merchant import extract_merchant


def _stacked_receipt_like_autocafe() -> np.ndarray:
    height, width = 1000, 500
    gray = np.full((height, width), 255, np.uint8)
    blocks = (
        (40, "OOO Avtokafe / Kassovyi chek / OOO Avtokafe"),
        (380, "Zakusochnyi ..... 120.00"),
        (520, "Zakusochnyi ..... 120.00"),
        (660, "Poziciya ............. 50.00"),
        (800, "ITOGO: 410.00"),
    )
    for y0, label in blocks:
        for offset in range(0, 100, 8):
            cv2.line(gray, (40, y0 + offset), (460, y0 + offset), 0, 2)
        cv2.putText(
            gray,
            label[:28],
            (50, y0 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            0,
            1,
            cv2.LINE_AA,
        )
        for x in range(50, 450, 8):
            cv2.circle(gray, (x, y0 + 110), 1, 0, -1)
    return gray


def _two_receipts_side_by_side() -> np.ndarray:
    height, width = 800, 900
    gray = np.full((height, width), 255, np.uint8)
    for x0 in (30, 480):
        for offset in range(0, 600, 10):
            cv2.line(gray, (x0, 50 + offset), (x0 + 350, 50 + offset), 0, 2)
    return gray


AUTOCAFE_OCR_TEXT = """
ООО "Автокафе"
Кассовый чек
ООО "Автокафе"
----------------------------
Закусочный..........120.00
............................
Закусочный..........120.00
............................
Позиция 3............50.00
............................
Позиция 4............50.00
............................
Позиция 5............30.00
............................
Позиция 6............40.00
............................
ИТОГО: 410.00
""".strip()


class TestCountReceipts:
    def test_single_tall_receipt_with_separators_is_one(self):
        assert count_receipts(_stacked_receipt_like_autocafe()) == 1

    def test_two_side_by_side_receipts_are_two(self):
        assert count_receipts(_two_receipts_side_by_side()) == 2

    def test_blank_image_is_zero(self):
        blank = np.full((400, 300), 255, np.uint8)
        assert count_receipts(blank) == 0


class TestAutocafeOcrText:
    def test_merchant_and_total_from_repeated_header(self):
        assert extract_merchant(AUTOCAFE_OCR_TEXT) == 'ООО "Автокафе"'
        assert extract_amount(AUTOCAFE_OCR_TEXT) is not None
        assert float(extract_amount(AUTOCAFE_OCR_TEXT)) == 410.0

    def test_repeated_company_name_does_not_break_parsing(self):
        assert AUTOCAFE_OCR_TEXT.lower().count("автокафе") >= 2
        assert extract_amount(AUTOCAFE_OCR_TEXT) is not None
        assert extract_date(AUTOCAFE_OCR_TEXT) is None
