MIN_LENGTH = 15
MIN_ALNUM_RATIO = 0.4


def is_meaningful(text: str) -> bool:
    # Грубый фильтр «мусорного» OCR: если текста слишком мало или в нём преобладают
    # не-буквенно-цифровые символы (типичный признак нераспознанной картинки),
    # считаем результат непригодным — это триггер для retry с другой бинаризацией.
    stripped = text.strip()
    if len(stripped) < MIN_LENGTH:
        return False
    alnum = sum(character.isalnum() for character in stripped)
    return alnum / len(stripped) >= MIN_ALNUM_RATIO
