import cv2
import numpy as np


def laplacian_variance(gray: np.ndarray) -> float:
    # Дисперсия лапласиана — стандартная метрика резкости: у размытого изображения
    # мало резких перепадов яркости, поэтому дисперсия отклика Лапласа низкая.
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(gray: np.ndarray, threshold: float) -> bool:
    return laplacian_variance(gray) < threshold
