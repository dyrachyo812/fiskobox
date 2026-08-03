from types import SimpleNamespace

from worker.pipeline.parsing.categorize import categorize


def make_categories():
    return [
        SimpleNamespace(name="Продукты", keywords=["атб", "сильпо", "пятерочка", "ашан"]),
        SimpleNamespace(name="Транспорт", keywords=["uber", "bolt", "укрзализныця", "азс", "таврида"]),
        SimpleNamespace(
            name="Кафе",
            keywords=[
                "mcdonald",
                "mcdonalds",
                "макдональдз",
                "starbucks",
                "кафе",
                "ресторан",
                "кофе",
            ],
        ),
        SimpleNamespace(
            name="Электроника",
            keywords=["sony", "dns", "comfy", "м.видео", "ситилинк", "citilink"],
        ),
        SimpleNamespace(
            name="Одежда",
            keywords=["dior", "бутик", "shoes", "сумка", "zara"],
        ),
    ]


class TestCategorize:
    def test_products(self):
        assert categorize("АТБ Маркет", make_categories()) == "Продукты"

    def test_transport(self):
        assert categorize("Uber Trip", make_categories()) == "Транспорт"

    def test_cafe(self):
        assert categorize("STARBUCKS COFFEE", make_categories()) == "Кафе"

    def test_electronics_chains(self):
        assert categorize("DNS", make_categories()) == "Электроника"
        assert categorize('ООО "Ситилинк"', make_categories()) == "Электроника"
        assert categorize("М.Видео", make_categories()) == "Электроника"

    def test_fashion_and_luxury(self):
        assert categorize("Dior Boutique", make_categories()) == "Одежда"
        assert categorize("Shoes & Bags", make_categories()) == "Одежда"

    def test_unknown_returns_none(self):
        assert categorize("Неизвестный Магазин XYZ", make_categories()) is None

    def test_none_merchant_returns_none(self):
        assert categorize(None, make_categories()) is None

    def test_empty_merchant_returns_none(self):
        assert categorize("", make_categories()) is None

    def test_empty_categories_returns_none(self):
        assert categorize("АТБ", []) is None

    def test_first_match_wins_on_equal_hits(self):
        categories = [
            SimpleNamespace(name="A", keywords=["shop"]),
            SimpleNamespace(name="B", keywords=["shop"]),
        ]
        assert categorize("My Shop", categories) == "A"

    def test_does_not_guess_electronics_brand_from_raw_text_alone(self):
        text = "ІД 123\nSONY NW-WS413B\nСума 3299.00"
        assert categorize(None, make_categories(), text) is None

    def test_cafe_from_menu_items_without_merchant(self):
        text = "КАПУЧЧІНО 35.00\nРИБАЙ СТЕЙК 670.00\nСАЛАТ 85.00\nСУМА 2324,00 ГРН"
        assert categorize(None, make_categories(), text) == "Кафе"

    def test_food_signals_override_wrong_transport_guess(self):
        text = (
            "КАВА ДАБЛ ЕСПРЕССО 48.00\nКАПУЧЧІНО 35.00\n"
            "ФІЛЕ ТЕЛЯТИНИ 382.00\nСТЕЙК 430.00\nСУМА 100 ГРН"
        )
        assert (
            categorize(
                "Случайный магазин",
                make_categories(),
                text,
                merchant_source="line",
            )
            == "Кафе"
        )

    def test_rejected_merchant_source_returns_none(self):
        assert (
            categorize(
                "случайный текст",
                make_categories(),
                merchant_source="rejected",
            )
            is None
        )

    def test_reliable_merchant_source_categorizes(self):
        assert (
            categorize(
                "McDonald's",
                make_categories(),
                merchant_source="known",
            )
            == "Кафе"
        )

    def test_gas_station_from_merchant(self):
        assert (
            categorize(
                'ООО "Таврида-Петролиум"',
                make_categories(),
                merchant_source="legal",
            )
            == "Транспорт"
        )
