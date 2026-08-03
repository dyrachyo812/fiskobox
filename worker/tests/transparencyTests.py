from decimal import Decimal

from worker.notifications.messages import MANUAL_ENTRY_PROMPT, success_message
from worker.pipeline.parsing.amount import extract_amount_with_source
from worker.pipeline.parsing.date import extract_date_with_source
from worker.pipeline.parsing.receipt import parse_receipt


class TestExtractionMatchedBy:
    def test_amount_returns_anchor_label(self):
        amount, matched = extract_amount_with_source("ИТОГО: 850.00")
        assert amount == Decimal("850.00")
        assert matched == "итого"

    def test_date_returns_pattern_label(self):
        from datetime import date

        value, matched = extract_date_with_source("02.05.23 20:16", today=date(2026, 8, 2))
        assert value == date(2023, 5, 2)
        assert matched == "date_with_time"


class TestSuccessMessageTransparency:
    def test_all_key_fields_missing_asks_manual_entry(self):
        text = success_message(
            {
                "all_key_fields_missing": True,
                "needs_manual_review": True,
            }
        )
        assert MANUAL_ENTRY_PROMPT.splitlines()[0] in text
        assert "вручную" in text.lower()

    def test_low_quality_scan_mentioned(self):
        text = success_message(
            {
                "merchant_name": "АТБ",
                "merchant_confident": True,
                "amount": Decimal(100),
                "amount_confident": True,
                "purchase_date": None,
                "date_confident": False,
                "currency": "UAH",
                "category": "Продукты",
                "needs_manual_review": False,
                "all_key_fields_missing": False,
            },
            low_sharpness=True,
        )
        assert "Низкое качество скана" in text

    def test_parse_receipt_stores_matched_by(self):
        parsed = parse_receipt("АТБ Маркет\nИТОГО: 250,00 грн\n15.03.2024 18:40", [])
        assert parsed["amount_matched_by"] == "итого"
        assert parsed["merchant_matched_by"] == "known"
        assert parsed["date_matched_by"] in {"date_with_time", "date_near_time", "plain_date"}
        assert parsed["amount_confident"] is True
        assert parsed["merchant_confident"] is True
