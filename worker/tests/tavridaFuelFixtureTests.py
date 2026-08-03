from decimal import Decimal
from pathlib import Path

from worker.pipeline.parsing.amount import extract_amount_with_source
from worker.pipeline.parsing.currency import extract_currency
from worker.pipeline.parsing.hybridMerge import merge_hybrid_results
from worker.pipeline.parsing.merchant import extract_merchant
from worker.pipeline.parsing.receipt import parse_receipt_regex

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"


def read_text() -> str:
    return (FIXTURES / "tavridaFuelOcr.txt").read_text(encoding="utf-8")


class TestTavridaFuelOcrFixture:
    def test_amount_is_2200_63_not_ocr_typo(self):
        amount, source = extract_amount_with_source(read_text())
        assert amount == Decimal("2200.63")
        assert amount != Decimal("2200.83")
        assert source in {"reconciled_change", "consensus", "сума", "грн"}

    def test_currency_is_uah(self):
        assert extract_currency(read_text()) == "UAH"

    def test_merchant(self):
        merchant = extract_merchant(read_text())
        assert merchant is not None
        assert "Таврида" in merchant

    def test_hybrid_overrides_wrong_llm_currency_and_amount(self):
        regex = parse_receipt_regex(read_text(), [])
        llm = {
            **regex,
            "amount": Decimal("2200.83"),
            "currency": "RUB",
            "amount_confident": True,
            "amount_matched_by": "llm",
            "llm_confidence": "high",
            "parser_mode": "llm",
        }
        merged = merge_hybrid_results(llm, regex)
        assert merged["amount"] == Decimal("2200.63")
        assert merged["currency"] == "UAH"
