import numpy as np
import cv2
from PIL import Image
from paddleocr import PaddleOCR

from models.text_region import TextRegion


class OcrEngine:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)

    def _preprocess(self, image: Image.Image) -> np.ndarray:
        img = np.array(image)
        if len(img.shape) == 2:
            gray = img
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        return enhanced_rgb

    def detect(self, image: Image.Image) -> list:
        img = self._preprocess(image)
        results = self.ocr.ocr(img, cls=True)
        regions = []
        if not results or not results[0]:
            return regions
        for line in results[0]:
            bbox_points = line[0]
            text, confidence = line[1]
            xs = [p[0] for p in bbox_points]
            ys = [p[1] for p in bbox_points]
            x = int(min(xs))
            y = int(min(ys))
            w = int(max(xs) - x)
            h = int(max(ys) - y)
            regions.append(TextRegion(
                x=x, y=y, w=w, h=h,
                text=text,
                confidence=confidence,
                polygon=[list(p) for p in bbox_points],
            ))
        return regions
