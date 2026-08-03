from typing import Protocol

import numpy as np


class OcrEngine(Protocol):
    def recognize(self, image: np.ndarray) -> str: ...

    def recognize_receipt(self, gray: np.ndarray, variant: int = 0) -> str: ...
