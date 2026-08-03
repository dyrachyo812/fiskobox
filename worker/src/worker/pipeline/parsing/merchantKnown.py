KNOWN_MERCHANTS = (
    (("макдональдз", "макдональдс", "mcdonald", "mcdonalds"), "McDonald's"),
    (("атб",), "АТБ"),
    (("сільпо", "сильпо", "silpo"), "Сільпо"),
    (("фора", "fora"), "Фора"),
    (("ашан", "auchan"), "Ашан"),
    (("novus", "новус"), "NOVUS"),
    (("nova poshta", "нова пошта", "новa пошта"), "Нова Пошта"),
    (("dns", "днс"), "DNS"),
    (("comfy", "комфі", "комфи"), "Comfy"),
    (("алло", "allo"), "Алло"),
    (("розетка", "rozetka"), "Rozetka"),
    (("епіцентр", "эпицентр", "epicentr"), "Епіцентр"),
    (("metro", "метро"), "METRO"),
    (("варто", "varus"), "VARUS"),
    (("окко", "okko"), "OKKO"),
    (("woq", "вок"), "WOG"),
    (("starbucks", "старбакс"), "Starbucks"),
    (("kfc",), "KFC"),
    (("pizza day", "піца дей"), "Pizza Day"),
    (("автокафе",), 'ООО "Автокафе"'),
    (("таврида", "tavrida"), 'ООО "Таврида-Петролиум"'),
    (("dior",), "Dior"),
    (
        (
            "магнит",
            "magnit",
            "нагнит",
            "нагниt",
            "тандер",
            "tander",
        ),
        "Магнит",
    ),
    (
        (
            "aptekar",
            "аптекар",
            "tabletki.ua",
            "таблетки.ua",
        ),
        "Aptekar",
    ),
    (("резонанс", "resonance"), "Резонанс"),
)


def normalize_text(text: str) -> str:
    return (
        text.lower()
        .replace("ё", "е")
        .replace("’", "'")
        .replace("`", "'")
        .replace("«", '"')
        .replace("»", '"')
    )


def find_known_merchant(text: str) -> str | None:
    haystack = normalize_text(text)
    for aliases, canonical in KNOWN_MERCHANTS:
        for alias in aliases:
            if alias in haystack:
                return canonical
    return None
