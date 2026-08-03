from datetime import date
from decimal import Decimal

import pytest
from worker.pipeline.parsing.amount import extract_amount, normalize
from worker.pipeline.parsing.currency import extract_currency
from worker.pipeline.parsing.date import extract_date, parse_text_date


class TestExtractAmountFormats:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("₴850.00", Decimal("850.00")),
            ("850,00 грн", Decimal("850.00")),
            ("850 грн", Decimal(850)),
            ("$850.00", Decimal("850.00")),
            ("ИТОГО: 850.00", Decimal("850.00")),
            ("TOTAL $850.50", Decimal("850.50")),
            ("Разом 850,00 ₴", Decimal("850.00")),
            ("ИТОГО: 4 199.00", Decimal("4199.00")),
        ],
    )
    def test_currency_formats(self, text, expected):
        assert extract_amount(text) == expected

    def test_bare_number_without_anchor_returns_none(self):
        assert extract_amount("850.00") is None
        assert extract_amount("850,00") is None

    def test_total_keyword_beats_line_items(self):
        text = "Хлеб 45,00\nМолоко 89,90\nИТОГО: 134,90"
        assert extract_amount(text) == Decimal("134.90")

    def test_ukrainian_suma_beats_line_items(self):
        text = "Товар А 90.00\nТовар Б 100.00\nСума 274.00"
        assert extract_amount(text) == Decimal("274.00")

    def test_no_anchor_does_not_guess(self):
        text = "позиция 120,00\nпозиция 850,00\nпозиция 45,00"
        assert extract_amount(text) is None

    def test_empty_text_returns_none(self):
        assert extract_amount("") is None
        assert extract_amount("   \n  ") is None

    def test_garbage_text_returns_none(self):
        assert extract_amount("### ??? @@@") is None
        assert extract_amount("тут нет никаких чисел") is None

    def test_absurd_card_number_ignored(self):
        assert extract_amount("Карта 1234567890123456") is None

    def test_terminal_and_inn_ignored(self):
        text = (
            "Терминал 22935087\n"
            "Код авторизации 211000004035\n"
            "ИНН 7719674941147\n"
            "ФН 1234567890123456\n"
            "ИТОГ ОПЛАТЕ\n"
            "4 199.00"
        )
        assert extract_amount(text) == Decimal("4199.00")

    def test_european_thousands_and_decimal(self):
        assert extract_amount("ITOGO: 1.234,56") == Decimal("1234.56")
        assert extract_amount("ИТОГО: 1.234,56") == Decimal("1234.56")

    def test_invalid_numeric_token_skipped(self):
        assert extract_amount("ИТОГО: 12..34") is None

    def test_firmware_version_not_amount(self):
        text = "2. X 45.00 = 90.00 A\nIngenico Group TE90198. 11/06/13\nСУМА: 274.00 ГРН"
        assert extract_amount(text) == Decimal("274.00")
        assert extract_amount(text) != Decimal("90198.11")

    def test_ambiguous_totals_return_none(self):
        from worker.pipeline.parsing.amount import extract_amount_with_source

        text = "ИТОГО 100.00 TOTAL 250.00"
        amount, source = extract_amount_with_source(text)
        assert amount is None
        assert source == "ambiguous"

    def test_last_anchor_wins_same_keyword(self):
        text = "Сума 100.00\nСума 274.00"
        assert extract_amount(text) == Decimal("274.00")

    def test_payment_anchor_beats_earlier_suma(self):
        text = "Сума 214.00\nДо сплати 274.00"
        assert extract_amount(text) == Decimal("274.00")

    def test_last_total_line_wins(self):
        text = "ИТОГО: 100.00\nTOTAL: 250.00"
        assert extract_amount(text) == Decimal("250.00")


class TestExtractAmountOcrTypos:
    def test_o_instead_of_zero(self):
        assert extract_amount("ИТОГО: 5O0,00") == Decimal("500.00")

    def test_mixed_latin_and_cyrillic_o(self):
        assert extract_amount("ИТОГО: 1o0,оO") == Decimal("100.00")

    def test_l_instead_of_one(self):
        assert extract_amount("ИТОГО: 85l,00") == Decimal("851.00")

    def test_pipe_instead_of_one(self):
        assert extract_amount("ИТОГО: |00,00") == Decimal("100.00")

    def test_company_ooo_is_not_amount(self):
        text = "ООО Ромашка\nИТОГО: 100,00 руб"
        assert extract_amount(text) == Decimal("100.00")

    def test_letters_only_token_is_not_amount(self):
        assert normalize("ООО") is None
        assert normalize("Oo") is None


class TestExtractCurrency:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Сумма 100 руб", "RUB"),
            ("Итого 100 ₽", "RUB"),
            ("Total 100 $", "USD"),
            ("Summe 100 €", "EUR"),
            ("Разом 100 ₴", "UAH"),
            ("Разом 100 грн", "UAH"),
            ("Сума 274.00\nКартка 274.00\nСУМА: 274.00 ГРН", "UAH"),
            ("ПІІ МакДональдз\nСума 274.00\nФІСКАЛЬНИЙ ЧЕК", "UAH"),
        ],
    )
    def test_currency_symbols(self, text, expected):
        assert extract_currency(text) == expected

    def test_random_r_dot_does_not_force_rub(self):
        text = "Сума 274.00 ГРН\nпр. Короленка, 1\nФІСКАЛЬНИЙ ЧЕК"
        assert extract_currency(text) == "UAH"

    def test_no_currency_returns_none(self):
        assert extract_currency("просто текст без валюты") is None

    def test_empty_text_returns_none(self):
        assert extract_currency("") is None
        assert extract_currency(None) is None


class TestExtractDateFormats:
    TODAY = date(2026, 8, 2)

    def test_dotted_full_year(self):
        assert extract_date("Дата 15.03.2024", today=self.TODAY) == date(2024, 3, 15)

    def test_slash_short_year(self):
        assert extract_date("15/03/24", today=self.TODAY) == date(2024, 3, 15)

    def test_dash_format(self):
        assert extract_date("15-03-2024", today=self.TODAY) == date(2024, 3, 15)

    def test_iso_format(self):
        assert extract_date("2024-03-15", today=self.TODAY) == date(2024, 3, 15)

    def test_russian_text_month(self):
        assert extract_date("Куплено 15 марта 2024", today=self.TODAY) == date(2024, 3, 15)

    def test_english_text_month(self):
        assert extract_date("Purchased 15 March 2024", today=self.TODAY) == date(2024, 3, 15)

    def test_purchase_date_wins_over_print_date(self):
        text = "Дата покупки: 15.03.2024\nДата печати чека: 20.03.2024"
        assert extract_date(text, today=self.TODAY) == date(2024, 3, 15)

    def test_print_date_fallback(self):
        assert extract_date("Отпечатано 20.03.2024", today=self.TODAY) == date(2024, 3, 20)

    def test_missing_date_returns_none(self):
        assert extract_date("нет даты в этом тексте") is None
        assert extract_date("") is None

    def test_future_date_rejected(self):
        assert extract_date("01.01.2999", today=self.TODAY) is None

    def test_year_outside_window_rejected(self):
        assert extract_date("17.11.2005 14:25", today=self.TODAY) is None

    def test_year_within_fifteen_years_allowed(self):
        assert extract_date("17.11.2015 14:25", today=self.TODAY) == date(2015, 11, 17)
        assert extract_date("30/07/2020 16:02:46", today=self.TODAY) == date(2020, 7, 30)

    def test_year_plus_one_allowed(self):
        assert extract_date("01.01.2027", today=self.TODAY) == date(2027, 1, 1)

    def test_text_month_with_two_digit_year(self):
        assert extract_date("15 марта 24", today=self.TODAY) == date(2024, 3, 15)

    def test_invalid_text_date_returns_none(self):
        assert extract_date("31 февраля 2024", today=self.TODAY) is None

    def test_unknown_month_name_returns_none(self):
        assert parse_text_date("15", "unknownmonth", "2024", today=self.TODAY) is None

    def test_date_with_time_same_line(self):
        assert extract_date("02.05.23 20:16", today=self.TODAY) == date(2023, 5, 2)

    def test_time_then_date_same_line(self):
        assert extract_date("20:16 02.05.2023", today=self.TODAY) == date(2023, 5, 2)

    def test_date_with_time_on_adjacent_line(self):
        text = "Сума 100.00\n15.03.2024\n18:40\nФІСКАЛЬНИЙ ЧЕК"
        assert extract_date(text, today=self.TODAY) == date(2024, 3, 15)

    def test_timed_date_beats_earlier_plain_date(self):
        text = "01.01.2024\nТовар 10\n15.03.2024 18:40"
        assert extract_date(text, today=self.TODAY) == date(2024, 3, 15)

    def test_prefers_earlier_among_same_tier(self):
        text = "10.01.2024\nИТОГО 100\n20.03.2024"
        assert extract_date(text, today=self.TODAY) == date(2024, 1, 10)

    def test_inn_and_terminal_not_parsed_as_date(self):
        text = (
            "ИНН 7719674941147\n"
            "Терминал 22935087\n"
            "ФН 1234567890123456\n"
            "ФД 12345\n"
            "02.05.23 20:16"
        )
        assert extract_date(text, today=self.TODAY) == date(2023, 5, 2)

    def test_invalid_day_rejected(self):
        assert extract_date("ЧАС: 82.08.2026 21:13:35", today=self.TODAY) is None

    def test_invalid_time_not_treated_as_nearby_time(self):
        text = "15.03.2024\n1:85\n20.06.2024 18:40"
        assert extract_date(text, today=self.TODAY) == date(2024, 6, 20)
