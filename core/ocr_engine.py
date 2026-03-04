import numpy as np
import cv2
from PIL import Image
from paddleocr import PaddleOCR

from models.text_region import TextRegion

# Map user-facing language names to PaddleOCR language codes
LANG_MAP = {
    "chinese": "ch",
    "japanese": "japan",
    "korean": "korean",
}


class _MangaOcrRecognizer:
    """Lazy-loaded manga-ocr wrapper for Japanese text recognition."""

    def __init__(self):
        self._model = None

    def _ensure_loaded(self):
        if self._model is None:
            from manga_ocr import MangaOcr
            self._model = MangaOcr()

    def recognize(self, image: Image.Image, bbox: tuple) -> str:
        """Crop a region from the PIL image and recognize with manga-ocr.

        Args:
            image: Original (non-preprocessed) PIL image.
            bbox: (x, y, w, h) bounding box of the text region.
        """
        self._ensure_loaded()
        x, y, w, h = bbox
        pad = 5
        left = max(0, x - pad)
        top = max(0, y - pad)
        right = min(image.width, x + w + pad)
        bottom = min(image.height, y + h + pad)
        crop = image.crop((left, top, right, bottom))
        return self._model(crop)


class OcrEngine:
    def __init__(self, lang: str = "chinese"):
        self._engines = {}
        self._manga_ocr = None
        # Pre-initialize the requested language
        self._get_engine(lang)

    def _get_engine(self, lang: str) -> PaddleOCR:
        """Get or lazily create a PaddleOCR instance for the given language."""
        ocr_code = LANG_MAP.get(lang, "ch")
        if ocr_code not in self._engines:
            self._engines[ocr_code] = PaddleOCR(
                use_angle_cls=True, lang=ocr_code, show_log=False,
                det_db_thresh=0.2,
                det_db_box_thresh=0.35,
                det_db_unclip_ratio=1.8,
                det_limit_side_len=1280,
            )
        return self._engines[ocr_code]

    def _get_manga_ocr(self) -> _MangaOcrRecognizer:
        """Get or lazily create the manga-ocr recognizer."""
        if self._manga_ocr is None:
            self._manga_ocr = _MangaOcrRecognizer()
        return self._manga_ocr

    def _get_det_engine(self, lang: str) -> PaddleOCR:
        """Get a detection-only PaddleOCR with lower thresholds for small text."""
        key = LANG_MAP.get(lang, "ch") + "_det"
        if key not in self._engines:
            self._engines[key] = PaddleOCR(
                use_angle_cls=True, lang=LANG_MAP.get(lang, "ch"),
                show_log=False,
                det_db_thresh=0.1,
                det_db_box_thresh=0.15,
                det_db_unclip_ratio=1.5,
                det_limit_side_len=1280,
            )
        return self._engines[key]

    def detect(self, image: Image.Image, lang: str = "chinese") -> list:
        img = np.array(image.convert("RGB"))

        # For Japanese, use detection-only + manga-ocr so PaddleOCR's
        # recognition phase doesn't discard small text boxes.
        if lang == "japanese":
            return self._detect_japanese(image, img)

        engine = self._get_engine(lang)
        results = engine.ocr(img, cls=True)
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

    def _detect_japanese(self, image: Image.Image, img: np.ndarray) -> list:
        """Detection-only PaddleOCR + manga-ocr recognition for Japanese.

        Uses lower detection thresholds to catch small text that the full
        PaddleOCR pipeline would drop during its recognition filtering.
        """
        det_engine = self._get_det_engine("japanese")
        dt_result = det_engine.text_detector(img)
        boxes = dt_result[0] if dt_result and len(dt_result) > 0 else []
        if not len(boxes):
            return []

        recognizer = self._get_manga_ocr()
        regions = []
        for box in boxes:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x = int(min(xs))
            y = int(min(ys))
            w = int(max(xs) - x)
            h = int(max(ys) - y)
            if w < 5 or h < 5:
                continue
            text = recognizer.recognize(image, (x, y, w, h))
            if not text or not text.strip():
                continue
            regions.append(TextRegion(
                x=x, y=y, w=w, h=h,
                text=text,
                confidence=1.0,
                polygon=[list(p) for p in box],
            ))
        return regions
