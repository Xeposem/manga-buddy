import pytest
from PIL import Image, ImageDraw, ImageFont

from core.ocr_engine import OcrEngine
from models.text_region import TextRegion


@pytest.fixture(scope="module")
def ocr():
    return OcrEngine()


def _make_chinese_image(text="你好世界", size=(400, 100)):
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 32)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 30), text, fill="black", font=font)
    return img


def test_detect_finds_text(ocr):
    img = _make_chinese_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1
    assert all(isinstance(r, TextRegion) for r in regions)


def test_detect_returns_valid_bboxes(ocr):
    img = _make_chinese_image()
    regions = ocr.detect(img)
    for r in regions:
        assert r.x >= 0
        assert r.y >= 0
        assert r.w > 0
        assert r.h > 0
        assert r.x + r.w <= img.width
        assert r.y + r.h <= img.height


def test_detect_returns_text_content(ocr):
    img = _make_chinese_image("你好世界")
    regions = ocr.detect(img)
    all_text = "".join(r.text for r in regions)
    assert "你好" in all_text or "世界" in all_text


def test_detect_returns_confidence(ocr):
    img = _make_chinese_image()
    regions = ocr.detect(img)
    for r in regions:
        assert 0.0 < r.confidence <= 1.0


def test_detect_blank_image(ocr):
    img = Image.new("RGB", (200, 100), "white")
    regions = ocr.detect(img)
    assert isinstance(regions, list)
    assert len(regions) == 0


def test_detect_grayscale_image(ocr):
    img = _make_chinese_image().convert("L")
    regions = ocr.detect(img)
    assert isinstance(regions, list)
