from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import urllib.request

from worker.pipeline.parsing.ollamaClient import OllamaClient
from worker.pipeline.parsing.ollamaParser import OllamaReceiptParser

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"


def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:11434/api/tags", timeout=2
        ) as response:
            return response.status == 200
    except Exception:
        return False


pytestmark = [
    pytest.mark.local_llm,
    pytest.mark.skipif(not ollama_available(), reason="Ollama not running locally"),
]


class TestLocalOllamaReceiptParse:
    def test_dns_fixture_extracts_amount(self):
        text = (FIXTURES / "dnsAcquiring.txt").read_text(encoding="utf-8")
        client = OllamaClient(
            base_url="http://127.0.0.1:11434",
            model="llama3.1:8b",
            timeout_seconds=90,
            temperature=0.1,
        )
        result = OllamaReceiptParser(client).parse(text, [])
        assert result.get("parser_error") is None
        assert result.get("amount") == Decimal("4199.00")
        assert isinstance(result.get("purchase_date"), (date, type(None)))
