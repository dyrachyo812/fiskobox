from decimal import Decimal
from pathlib import Path

from worker.pipeline.parsing.amount import extract_amount, extract_amount_with_source
from worker.pipeline.parsing.hybridMerge import merge_hybrid_results
from worker.pipeline.parsing.merchant import extract_merchant
from worker.pipeline.parsing.receipt import parse_receipt_regex

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"


def read_text() -> str:
    return (FIXTURES / "aptekarSumaOcr.txt").read_text(encoding="utf-8")


class TestAptekarSumaOcrFixture:
    def test_amount_prefers_consensus_over_last_garbage_line(self):
        amount, source = extract_amount_with_source(read_text())
        assert amount == Decimal("209.91")
        assert amount != Decimal("283.91")
        assert amount != Decimal("510.00")
        assert source in {"consensus", "сума", "грн"}

    def test_merchant_aptekar(self):
        assert extract_merchant(read_text()) == "Aptekar"

    def test_hybrid_overrides_wrong_llm_total(self):
        regex = parse_receipt_regex(read_text(), [])
        llm = {
            **regex,
            "amount": Decimal("283.91"),
            "amount_confident": True,
            "amount_matched_by": "llm",
            "llm_confidence": "high",
            "parser_mode": "llm",
        }
        merged = merge_hybrid_results(llm, regex)
        assert merged["amount"] == Decimal("209.91")
        assert extract_amount(read_text()) == Decimal("209.91")
