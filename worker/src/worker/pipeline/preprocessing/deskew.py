import cv2
import numpy as np


def deskew(binary: np.ndarray) -> np.ndarray:
    # На вход приходит бинаризованное изображение (текст чёрный на белом фоне).
    # Для оценки наклона нам нужны пиксели текста, поэтому инвертируем: текст → белый.
    inverted = cv2.bitwise_not(binary)

    coords = np.column_stack(np.where(inverted > 0))
    if coords.size == 0:
        # Нечего выравнивать (пустое изображение) — возвращаем как есть.
        return binary

    # minAreaRect строит минимальный повёрнутый прямоугольник вокруг всех пикселей
    # текста. Его угол и есть наклон строк — это устойчивый «контурный» способ,
    # не требующий детекции отдельных линий (альтернатива — Hough по краям Canny).
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle

    height, width = binary.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # BORDER_REPLICATE, чтобы после поворота по краям не появлялись чёрные поля,
    # которые OCR может принять за артефакты.
    return cv2.warpAffine(
        binary,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
