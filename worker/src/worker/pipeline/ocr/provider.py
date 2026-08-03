from abc import ABC, abstractmethod

import numpy as np

from worker.pipeline.ocr.result import OCRResult


class OCRProvider(ABC):
    name: str

    @abstractmethod
    def extract_text(self, image: np.ndarray) -> OCRResult:
        raise NotImplementedError
