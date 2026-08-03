import cv2
import numpy as np


def image_to_png_bytes(image: np.ndarray) -> bytes:
    if image.ndim == 2:
        encoded = cv2.imencode(".png", image)[1]
    else:
        encoded = cv2.imencode(".png", image)[1]
    return encoded.tobytes()
