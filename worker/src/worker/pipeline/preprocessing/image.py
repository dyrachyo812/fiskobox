import cv2
import numpy as np

from worker.pipeline.preprocessing.deskew import deskew


def load_grayscale(image_path: str) -> np.ndarray:
    # Изображение уже лежит в общем томе (его скачал бот), поэтому «скачивание» здесь —
    # это чтение с диска. Сразу в grayscale: цвет для OCR чека бесполезен.
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Не удалось прочитать изображение: {image_path}")
    return image


def enhance(image: np.ndarray) -> np.ndarray:
    denoised = cv2.fastNlMeansDenoising(image, h=8)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(denoised)


def binarize(image: np.ndarray, variant: int) -> np.ndarray:
    # Ключ retry-стратегии: на каждой попытке применяем ДРУГОЙ способ бинаризации.
    # Если один метод дал мусор, другой может сработать на том же кадре.
    if variant <= 0:
        # Адаптивный Гаусс: базовый вариант, хорош при неравномерном освещении.
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
        )
    if variant == 1:
        # Otsu по всему кадру: выигрывает на равномерно освещённых чётких чеках.
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        _, result = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return result
    # Адаптивное среднее с меньшим окном: спасает мелкий/плотный шрифт.
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 9
    )


def preprocess_from_grayscale(gray: np.ndarray, variant: int) -> np.ndarray:
    enhanced = enhance(gray)
    binary = binarize(enhanced, variant)
    return deskew(binary)


def preprocess_image(image_path: str, variant: int = 0) -> np.ndarray:
    # Полный конвейер: чтение → улучшение → бинаризация (зависит от попытки) → выравнивание.
    return preprocess_from_grayscale(load_grayscale(image_path), variant)
