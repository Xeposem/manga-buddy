"""Integration tests: run the full pipeline end-to-end."""
import pytest
from PIL import Image, ImageDraw, ImageFont

from core.ocr_engine import OcrEngine
from core.translator import Translator
from core.pinyin_converter import PinyinConverter
from core.text_placer import TextPlacer
from core.image_renderer import ImageRenderer


@pytest.fixture(scope="module")
def ocr():
    return OcrEngine()


@pytest.fixture(scope="module")
def translator():
    return Translator()


@pytest.fixture(scope="module")
def pinyin_conv():
    return PinyinConverter()


@pytest.fixture(scope="module")
def renderer():
    return ImageRenderer()


def _get_font(size=36):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)
    except OSError:
        return ImageFont.load_default()


def _make_test_image():
    img = Image.new("RGB", (500, 200), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font()
    draw.text((30, 40), "你好世界", fill="black", font=font)
    draw.text((30, 110), "测试文本", fill="black", font=font)
    return img


def _make_bubble_image():
    """Image with two lines close together (one bubble) and one far away."""
    img = Image.new("RGB", (500, 500), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font()
    draw.text((30, 40), "你好世界", fill="black", font=font)
    draw.text((30, 90), "很高兴", fill="black", font=font)
    draw.text((30, 400), "再见", fill="black", font=font)
    return img


def _make_punctuation_image():
    """Image with Chinese text containing punctuation."""
    img = Image.new("RGB", (500, 100), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font()
    draw.text((30, 30), "你好！世界。", fill="black", font=font)
    return img


def test_full_pipeline_translation(ocr, translator, renderer):
    img = _make_test_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1

    translator.translate_batch(regions)
    assert any(r.translation for r in regions)
    assert all(r.group_id >= 0 for r in regions)

    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "translation")
    assert len(placements) >= 1

    result = renderer.render(img, placements)
    assert result.size == img.size
    assert result.mode == "RGBA"


def test_full_pipeline_translation_overlay(ocr, translator, renderer):
    img = _make_test_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1

    translator.translate_batch(regions)

    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "translation", overlay="always")
    assert len(placements) >= 1

    result = renderer.render(img, placements, regions=regions, overlay="always")
    assert result.size == img.size


def test_grouped_translation(ocr, translator):
    img = _make_bubble_image()
    regions = ocr.detect(img)
    assert len(regions) >= 2

    translator.translate_batch(regions)
    translations_with_text = [r for r in regions if r.translation]
    assert len(translations_with_text) >= 1
    assert all(r.group_id >= 0 for r in regions)


def test_full_pipeline_pinyin_per_char(ocr, pinyin_conv, renderer):
    img = _make_test_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1

    pinyin_conv.convert_batch(regions)
    for r in regions:
        assert r.pinyin != ""
        assert len(r.char_pinyin) == len(r.text)

    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "pinyin")
    total_chars = sum(len(r.text) for r in regions)
    assert len(placements) == total_chars

    result = renderer.render(img, placements)
    assert result.size == img.size


def test_pinyin_with_punctuation(ocr, pinyin_conv):
    """Punctuation in OCR output should produce correct char_pinyin mappings."""
    img = _make_punctuation_image()
    regions = ocr.detect(img)
    if not regions:
        return

    pinyin_conv.convert_batch(regions)
    for r in regions:
        # char_pinyin count should match text length exactly
        assert len(r.char_pinyin) == len(r.text), (
            f"Mismatch for '{r.text}': "
            f"char_pinyin has {len(r.char_pinyin)}, text has {len(r.text)}"
        )


def test_full_pipeline_pinyin_overlay(ocr, pinyin_conv, renderer):
    img = _make_test_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1

    pinyin_conv.convert_batch(regions)

    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "pinyin", overlay="always")
    total_chars = sum(len(r.text) for r in regions)
    assert len(placements) == total_chars

    result = renderer.render(img, placements, regions=regions, overlay="always")
    assert result.size == img.size


def test_pipeline_with_mixed_content(ocr, translator, pinyin_conv):
    img = _make_test_image()
    regions = ocr.detect(img)
    assert len(regions) >= 1

    translator.translate_batch(regions)
    pinyin_conv.convert_batch(regions)

    for r in regions:
        assert r.pinyin != ""
        assert len(r.char_pinyin) == len(r.text)
    assert any(r.translation for r in regions)


def test_ocr_preserves_polygon(ocr):
    img = _make_test_image()
    regions = ocr.detect(img)
    for r in regions:
        assert len(r.polygon) == 4
        for point in r.polygon:
            assert len(point) == 2


def test_edge_text_stays_in_bounds(ocr, translator, renderer):
    """Text near the image edge should have annotations clamped inside."""
    img = Image.new("RGB", (200, 80), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font(28)
    draw.text((120, 25), "你好", fill="black", font=font)
    regions = ocr.detect(img)
    if not regions:
        return

    translator.translate_batch(regions)
    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "translation")

    for text, x, y, font_size in placements:
        assert x >= 0
        assert y >= 0
        tw, th = placer._estimate_text_size(text, font_size)
        assert x + tw <= img.width
