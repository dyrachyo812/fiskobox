from datetime import date
from decimal import Decimal
from pathlib import Path

from worker.pipeline.parsing.amount import extract_amount
from worker.pipeline.parsing.currency import extract_currency
from worker.pipeline.parsing.date import extract_date
from worker.pipeline.parsing.merchant import extract_merchant

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestDnsReceiptFixture:
    def test_ideal_ocr_amount_and_date(self):
        text = read_fixture("dnsIdealOcr.txt")
        assert extract_amount(text) == Decimal("4199.00")
        assert extract_date(text) == date(2023, 5, 2)
        assert "DNS" in (extract_merchant(text) or "")

    def test_total_keyword_beats_terminal_and_inn(self):
        text = read_fixture("dnsIdealOcr.txt")
        assert extract_amount(text) != Decimal(22935087)
        assert extract_amount(text) != Decimal(30)

    def test_noisy_actual_ocr_does_not_return_bogus_81(self):
        text = read_fixture("dnsActualOcr.txt")
        amount = extract_amount(text)
        assert amount != Decimal(81)
        assert extract_date(text) != date(1988, 5, 12)


class TestAutocafeReceiptFixture:
    def test_ideal_ocr_amount(self):
        text = read_fixture("autocafeIdealOcr.txt")
        assert extract_amount(text) == Decimal("410.00")
        assert extract_merchant(text) == 'ООО "Автокафе"'

    def test_space_thousands_and_itog_oplate(self):
        text = "ИТОГ ОПЛАТЕ\n4 199.00"
        assert extract_amount(text) == Decimal("4199.00")

    def test_date_near_time_preferred(self):
        text = "ИНН 7719674941147\n02.05.23 20:16\n12.05.88"
        assert extract_date(text) == date(2023, 5, 2)


class TestUkraineSumaReceiptFixture:
    def test_suma_keyword_beats_line_item_90(self):
        text = read_fixture("ukraineSumaIdealOcr.txt")
        assert extract_amount(text) == Decimal("274.00")
        assert extract_amount(text) != Decimal("90.00")

    def test_ukrainian_total_keywords(self):
        assert extract_amount("Товар 90.00\nСума 274.00") == Decimal("274.00")
        assert extract_amount("Товар 90.00\nДо сплати 274.00") == Decimal("274.00")
        assert extract_amount("Товар 90.00\nВсього 274.00") == Decimal("274.00")
        assert extract_amount("Товар 90.00\nРазом 274.00") == Decimal("274.00")

    def test_suma_amount_on_next_line(self):
        text = "Товар 90.00\nСума\n274.00"
        assert extract_amount(text) == Decimal("274.00")


class TestMcdonaldsReceiptFixture:
    def test_ideal_ocr_amount_is_274_not_90(self):
        text = read_fixture("mcdonaldsIdealOcr.txt")
        assert extract_amount(text) == Decimal("274.00")
        assert extract_amount(text) != Decimal("90.00")
        assert extract_currency(text) == "UAH"

    def test_actual_ocr_prefers_payment_total(self):
        text = read_fixture("mcdonaldsActualOcr.txt")
        assert extract_amount(text) == Decimal("274.00")
        assert extract_amount(text) != Decimal("90.00")
        assert extract_currency(text) == "UAH"

    def test_multiply_line_without_anchor_returns_none(self):
        text = "2. X 45.00 = 90.00 A\nЧІЗБУРГЕР 29.00 A"
        assert extract_amount(text) is None

    def test_payment_grn_beats_misread_suma_214(self):
        text = (
            "2. X 45.00 = 90.00 A\n"
            "Суна 214.00\n"
            "Картка ый 4.00\n"
            "СУМА: 274.00 ГРН\n"
        )
        assert extract_amount(text) == Decimal("274.00")


class TestProblemReceiptFixtures:
    def test_problem_17_suma_126(self):
        text = read_fixture("problemReceipt17.txt")
        assert extract_amount(text) == Decimal("126.00")

    def test_problem_17_date_within_window(self):
        text = read_fixture("problemReceipt17.txt")
        assert extract_date(text, today=date(2026, 8, 2)) == date(2015, 11, 17)

    def test_problem_18_do_splaty_163(self):
        text = read_fixture("problemReceipt18.txt")
        assert extract_amount(text) == Decimal("163.95")

    def test_problem_18_invalid_ocr_date_rejected(self):
        text = read_fixture("problemReceipt18.txt")
        assert extract_date(text) is None

    def test_problem_19_suma_grn_2200(self):
        text = read_fixture("problemReceipt19.txt")
        assert extract_amount(text) == Decimal("2200.63")

    def test_problem_19_no_date(self):
        text = read_fixture("problemReceipt19.txt")
        assert extract_date(text) is None

    def test_problem_19_merchant_tavrida(self):
        text = read_fixture("problemReceipt19.txt")
        merchant = extract_merchant(text)
        assert merchant is not None
        assert "Таврида" in merchant

    def test_problem_18_rejects_garbage_merchant(self):
        text = read_fixture("problemReceipt18.txt")
        assert extract_merchant(text) is None

    def test_problem_20_suma_2324(self):
        text = read_fixture("problemReceipt20.txt")
        assert extract_amount(text) == Decimal("2324.00")

    def test_problem_20_no_date(self):
        text = read_fixture("problemReceipt20.txt")
        assert extract_date(text) is None

    def test_problem_20_no_merchant(self):
        text = read_fixture("problemReceipt20.txt")
        assert extract_merchant(text) is None
