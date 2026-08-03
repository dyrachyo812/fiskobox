from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from worker.pipeline.parsing.categorize import categorize
from worker.pipeline.parsing.hybridMerge import merge_hybrid_results
from worker.pipeline.parsing.receipt import parse_receipt_regex

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"


def read_text() -> str:
    return (FIXTURES / "resonanceCafeOcr.txt").read_text(encoding="utf-8")


def cafe_categories():
    return [
        SimpleNamespace(name="Транспорт", keywords=["uber", "азс", "таврида"]),
        SimpleNamespace(
            name="Кафе",
            keywords=["кафе", "ресторан", "кофе", "кава", "резонанс"],
        ),
        SimpleNamespace(name="Продукты", keywords=["атб"]),
    ]


class TestResonanceCafeOcrFixture:
    def test_category_is_cafe_from_menu_items(self):
        text = read_text()
        assert categorize(None, cafe_categories(), text) == "Кафе"
        assert categorize(None, cafe_categories(), text) != "Транспорт"

    def test_currency_and_amount(self):
        parsed = parse_receipt_regex(read_text(), cafe_categories())
        assert parsed["currency"] == "UAH"
        assert parsed["amount"] == Decimal("2324.00")
        assert parsed["category"] == "Кафе"

    def test_hybrid_overrides_wrong_llm_transport(self):
        regex = parse_receipt_regex(read_text(), cafe_categories())
        llm = {
            **regex,
            "category": "Транспорт",
            "parser_mode": "llm",
        }
        merged = merge_hybrid_results(llm, regex)
        assert merged["category"] == "Кафе"
