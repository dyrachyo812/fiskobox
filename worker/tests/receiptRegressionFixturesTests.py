from datetime import date
from decimal import Decimal
from pathlib import Path

from worker.pipeline.parsing.amount import extract_amount
from worker.pipeline.parsing.date import extract_date
from worker.pipeline.parsing.merchant import extract_merchant

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "receipts"
TODAY = date(2026, 8, 2)


def read_fixture(name: str) -> str:
    path = FIXTURES / name
    assert path.exists(), f"missing fixture: {path}"
    return path.read_text(encoding="utf-8")


class TestAutocafeCafeFixture:
    def test_amount_date_merchant(self):
        text = read_fixture("autocafeCafe.txt")
        assert extract_merchant(text) == 'ООО "Автокафе"'
        assert extract_amount(text) == Decimal("785.00")
        assert extract_date(text, today=TODAY) == date(2025, 7, 29)


class TestDnsAcquiringFixture:
    def test_amount_date_merchant_ignores_terminal_noise(self):
        text = read_fixture("dnsAcquiring.txt")
        assert extract_merchant(text) == "DNS"
        assert extract_amount(text) == Decimal("4199.00")
        assert extract_amount(text) != Decimal(22935087)
        assert extract_date(text, today=TODAY) == date(2023, 5, 2)


class TestUkraineSumaFixture:
    def test_amount_date_merchant(self):
        text = read_fixture("ukraineSuma.txt")
        assert extract_merchant(text) == "McDonald's"
        assert extract_amount(text) == Decimal("274.00")
        assert extract_amount(text) != Decimal("90.00")
        assert extract_date(text, today=TODAY) == date(2025, 3, 15)


class TestDiorLuxuryFixture:
    def test_amount_date_merchant(self):
        text = read_fixture("diorLuxury.txt")
        assert extract_merchant(text) == "Dior"
        assert extract_amount(text) == Decimal("225900.00")
        assert extract_date(text, today=TODAY) == date(2025, 6, 10)
