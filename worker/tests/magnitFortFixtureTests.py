from datetime import date
from decimal import Decimal
from pathlib import Path

from worker.pipeline.parsing.amount import extract_amount_with_source
from worker.pipeline.parsing.date import extract_date
from worker.pipeline.parsing.hybridMerge import merge_hybrid_results
from worker.pipeline.parsing.merchant import extract_merchant
from worker.pipeline.parsing.receipt import parse_receipt_regex

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"
TODAY = date(2026, 8, 3)


def read_text() -> str:
    return (FIXTURES / "magnitFortOcr.txt").read_text(encoding="utf-8")


class TestMagnitFortOcrFixture:
    def test_merchant_is_magnit(self):
        assert extract_merchant(read_text()) == "Магнит"

    def test_amount_is_total_not_cash(self):
        amount, source = extract_amount_with_source(read_text())
        assert amount == Decimal("469.25")
        assert amount != Decimal("5900.00")
        assert source in {"reconciled_change", "всего"}

    def test_date_from_short_year_with_broken_time(self):
        assert extract_date(read_text(), today=TODAY) == date(2015, 6, 12)

    def test_regex_parse_bundle(self):
        parsed = parse_receipt_regex(read_text(), [])
        assert parsed["merchant_name"] == "Магнит"
        assert parsed["amount"] == Decimal("469.25")
        assert parsed["purchase_date"] == date(2015, 6, 12)

    def test_hybrid_overrides_wrong_llm_amount(self):
        regex = parse_receipt_regex(read_text(), [])
        llm = {
            **regex,
            "merchant_name": "НАГНИТ - ФОР T",
            "amount": Decimal("5900.00"),
            "purchase_date": None,
            "amount_confident": True,
            "date_confident": False,
            "merchant_confident": True,
            "amount_matched_by": "llm",
            "date_matched_by": "none",
            "merchant_matched_by": "llm",
            "llm_confidence": "high",
            "parser_mode": "llm",
        }
        merged = merge_hybrid_results(llm, regex)
        assert merged["amount"] == Decimal("469.25")
        assert merged["merchant_name"] == "Магнит"
        assert merged["purchase_date"] == date(2015, 6, 12)
