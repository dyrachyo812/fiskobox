from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from worker.pipeline.parsing.ollamaClient import OllamaError
from worker.pipeline.parsing.ollamaJson import OllamaJsonError, extract_json_object
from worker.pipeline.parsing.ollamaParser import OllamaReceiptParser
from worker.pipeline.parsing.ollamaValidate import (
    empty_manual_review_result,
    validate_ollama_payload,
)
from worker.pipeline.parsing.receipt import parse_receipt, parse_receipt_hybrid


class FakeOllamaClient:
    def __init__(self, responses: list[str] | Exception) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str, *, use_json_format: bool = True) -> str:
        del prompt, use_json_format
        self.calls += 1
        if isinstance(self.responses, Exception):
            raise self.responses
        if not self.responses:
            raise OllamaError("no responses left")
        return self.responses.pop(0)


class TestExtractJsonObject:
    def test_parses_plain_json(self):
        data = extract_json_object('{"amount": 10, "merchant_name": "DNS"}')
        assert data["amount"] == 10
        assert data["merchant_name"] == "DNS"

    def test_extracts_json_from_surrounding_text(self):
        data = extract_json_object(
            'Конечно:\n```json\n{"amount": 12.5, "date": "2024-03-15"}\n```\n'
        )
        assert data["amount"] == 12.5
        assert data["date"] == "2024-03-15"

    def test_raises_on_invalid(self):
        with pytest.raises(OllamaJsonError):
            extract_json_object("нет json здесь")


class TestValidateOllamaPayload:
    def test_validates_core_fields(self):
        result = validate_ollama_payload(
            {
                "merchant_name": "DNS",
                "amount": "4 199.00",
                "currency": "uah",
                "date": "2024-07-08",
                "category": "Электроника",
                "items": [{"name": "SSD", "price": 4199, "quantity": 1}],
                "confidence": "high",
            },
            db_category_names=["Электроника", "Продукты"],
            today=date(2024, 8, 1),
        )
        assert result["merchant_name"] == "DNS"
        assert result["amount"] == Decimal("4199.00")
        assert result["currency"] == "UAH"
        assert result["purchase_date"] == date(2024, 7, 8)
        assert result["category"] == "Электроника"
        assert result["needs_manual_review"] is False
        assert result["amount_matched_by"] == "llm"

    def test_maps_food_alias_to_db_category(self):
        result = validate_ollama_payload(
            {
                "merchant_name": "АТБ",
                "amount": 100,
                "currency": "UAH",
                "date": "2024-07-01",
                "category": "Еда",
                "confidence": "medium",
            },
            db_category_names=["Продукты", "Кафе"],
            today=date(2024, 8, 1),
        )
        assert result["category"] == "Продукты"

    def test_rejects_future_date_and_non_positive_amount(self):
        result = validate_ollama_payload(
            {
                "merchant_name": "X",
                "amount": -5,
                "date": "2030-01-01",
                "category": "Прочее",
                "confidence": "high",
            },
            today=date(2024, 8, 1),
        )
        assert result["amount"] is None
        assert result["purchase_date"] is None


class TestOllamaReceiptParser:
    def test_success_on_first_attempt(self):
        client = FakeOllamaClient(
            [
                '{"merchant_name":"Cafe","amount":146.9,"currency":"UAH",'
                '"date":"2024-07-08","category":"Развлечения",'
                '"items":[],"confidence":"high"}'
            ]
        )
        parser = OllamaReceiptParser(client)
        result = parser.parse("Cafe\nИтого 146.90", [])
        assert result["merchant_name"] == "Cafe"
        assert result["amount"] == Decimal("146.90")
        assert client.calls == 1

    def test_retries_invalid_json_then_manual_review(self):
        client = FakeOllamaClient(["not-json", "still not json"])
        parser = OllamaReceiptParser(client)
        result = parser.parse("text", [])
        assert result["needs_manual_review"] is True
        assert result["all_key_fields_missing"] is True
        assert "parser_error" in result
        assert client.calls == 2

    def test_unavailable_ollama_marks_manual_review(self):
        client = FakeOllamaClient(OllamaError("Ollama недоступна"))
        parser = OllamaReceiptParser(client)
        result = parser.parse("text", [])
        assert result["needs_manual_review"] is True
        assert client.calls == 2


class TestParseReceiptModes:
    def test_regex_mode_unchanged(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PARSER_MODE", "regex")
        from shared.config.settings import get_settings

        get_settings.cache_clear()
        result = parse_receipt(
            "АТБ Маркет\nИТОГО: 250,00 грн\n15.03.2024 18:40",
            [],
            mode="regex",
        )
        assert result["parser_mode"] == "regex"
        assert result["amount"] == Decimal("250.00")

    def test_hybrid_falls_back_to_regex(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(
            "worker.pipeline.parsing.receipt.parse_receipt_llm",
            lambda text, categories: empty_manual_review_result(reason="down"),
        )
        result = parse_receipt_hybrid(
            "АТБ Маркет\nИТОГО: 250,00 грн\n15.03.2024 18:40",
            [],
        )
        assert result["parser_mode"] == "hybrid"
        assert result["amount"] == Decimal("250.00")
        assert result.get("llm_fallback_reason") == "down"

    def test_hybrid_fills_gaps_from_regex(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(
            "worker.pipeline.parsing.receipt.parse_receipt_llm",
            lambda text, categories: {
                "amount": None,
                "currency": None,
                "merchant_name": "DNS",
                "purchase_date": None,
                "category": None,
                "items": [],
                "llm_confidence": "medium",
                "needs_manual_review": True,
                "all_key_fields_missing": False,
                "amount_matched_by": "none",
                "date_matched_by": "none",
                "merchant_matched_by": "llm",
                "amount_source": "none",
                "merchant_source": "llm",
                "date_source": "none",
                "amount_confident": False,
                "date_confident": False,
                "merchant_confident": True,
                "parser_mode": "llm",
            },
        )
        result = parse_receipt_hybrid(
            "DNS\nИТОГ ОПЛАТЕ\n4 199.00\n02.05.23 20:16",
            [],
        )
        assert result["parser_mode"] == "hybrid"
        assert result["merchant_name"] == "DNS"
        assert result["amount"] == Decimal("4199.00")
        assert "amount" in (result.get("hybrid_filled_from_regex") or [])

    def test_hybrid_overrides_wrong_confident_llm_amount(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(
            "worker.pipeline.parsing.receipt.parse_receipt_llm",
            lambda text, categories: {
                "amount": Decimal("5900.00"),
                "currency": "RUB",
                "merchant_name": "НАГНИТ",
                "purchase_date": None,
                "category": "Продукты",
                "items": [],
                "llm_confidence": "high",
                "needs_manual_review": False,
                "all_key_fields_missing": False,
                "amount_matched_by": "llm",
                "date_matched_by": "none",
                "merchant_matched_by": "llm",
                "amount_source": "llm",
                "merchant_source": "llm",
                "date_source": "none",
                "amount_confident": True,
                "date_confident": False,
                "merchant_confident": True,
                "parser_mode": "llm",
            },
        )
        text = (
            "НАГНИТ - ФОР T\nmagnit.ru\n"
            "12.06.15 12:06\nВСЕГО:\n\n469.25\n"
            "ИТОГ 5900.00\nСДАЧА =4530.75\nИТОГ =469.25\n"
        )
        result = parse_receipt_hybrid(text, [])
        assert result["amount"] == Decimal("469.25")
        assert result["merchant_name"] == "Магнит"
