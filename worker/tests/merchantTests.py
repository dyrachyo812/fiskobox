from worker.pipeline.parsing.merchant import (
    extract_merchant,
    extract_merchant_with_source,
)
from worker.pipeline.parsing.receipt import parse_receipt


class TestExtractMerchant:
    def test_first_meaningful_line(self):
        text = "АТБ Маркет\nИТОГО: 100,00"
        assert extract_merchant(text) == "АТБ"

    def test_skips_empty_and_numeric_lines(self):
        text = "\n123456\nСильпо"
        assert extract_merchant(text) == "Сільпо"

    def test_skips_tax_and_country_lines(self):
        text = "Україна\nм.Київ\nПН 0900000060003\nООО Ромашка\nСума 100.00"
        assert extract_merchant(text) == "ООО Ромашка"

    def test_legal_form_tov_with_quotes(self):
        text = 'ТОВ "Смачний Хліб"\nКасовий чек\nСума 50.00'
        assert extract_merchant(text) == 'ТОВ "Смачний Хліб"'

    def test_ocr_ooo_as_zeros_with_quotes(self):
        text = '000 "Таврида-Петролиум"\nАЗС, магазин №0Д19\nСУМА, ГРН 2200,63'
        merchant = extract_merchant(text)
        assert merchant is not None
        assert "Таврида" in merchant

    def test_skips_terminal_header_lines(self):
        text = (
            "Терминал 22935087\n"
            "Ростов-на-Дону\n"
            "Кассовый чек\n"
            'ООО "Ромашка"\n'
            "ИТОГО: 100.00"
        )
        assert extract_merchant(text) == 'ООО "Ромашка"'

    def test_known_brand_from_noisy_ocr(self):
        text = "ПІІ 'МакДональдз Юкрейн Лтд'\nСума 274.00\nГРН"
        assert extract_merchant(text) == "McDonald's"

    def test_skips_product_model_lines(self):
        text = "ІД 36469918 ПН 3646993126531\nКаса 01\nSONY NW-WS413B 4GB Black\nСума 3299.00"
        assert extract_merchant(text) is None

    def test_skips_product_and_garbage_lines(self):
        text = "лето\nТовар2 1265 .09ГВ\nЕкстра заміна 365\nСума 126.00"
        assert extract_merchant(text) is None

    def test_garbage_merchant_returns_none_and_rejected(self):
        text = "== = =- Clana: Qua\nс = — ~ ‘Магазин,\nСума 163.95"
        merchant, source = extract_merchant_with_source(text)
        assert merchant is None
        assert source == "rejected"

    def test_short_cleanup_returns_none(self):
        text = "АБ\nСума 10.00"
        merchant, source = extract_merchant_with_source(text)
        assert merchant is None
        assert source in {"rejected", "none"}

    def test_no_merchant_returns_none(self):
        assert extract_merchant("123\n456") is None

    def test_fop_legal_form(self):
        text = "ФОП Тестовий\nКасовий чек\nСума 274.00"
        assert extract_merchant(text) == "ФОП Тестовий"


class TestParseReceipt:
    def test_builds_structure(self):
        text = "АТБ Маркет\n15.03.2024\nИТОГО: 250,00 грн"
        result = parse_receipt(text, [])
        assert result["merchant_name"] == "АТБ"
        assert result["amount"] is not None
        assert result["purchase_date"] is not None
        assert result["category"] is None

    def test_rejected_merchant_marks_manual_review(self):
        text = "== = =- Clana\nс = — ~ Магазин\nДо сплати 163.95"
        result = parse_receipt(text, [])
        assert result["merchant_name"] is None
        assert result["merchant_source"] == "rejected"
        assert result["needs_manual_review"] is True
