from core.text_placer import TextPlacer
from models.text_region import TextRegion


def test_place_translation_right():
    """Translation should be placed to the right when there's room."""
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(x=50, y=50, w=100, h=30, text="你好", translation="Hello")
    placer.occupied = [(region.x, region.y, region.w, region.h)]
    result = placer.place_translation(region)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0][0] == "Hello"


def test_place_translation_wraps_long_text():
    """Long translation should wrap into multiple lines."""
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(x=50, y=50, w=120, h=60, text="你好世界测试",
                        translation="Hello World this is a very long translation text")
    result = placer.place_translation(region, overlay="always")
    assert len(result) > 1  # Should be multiple lines
    # All lines should be within bounds
    for text, x, y, fs in result:
        assert x >= 0
        assert y >= 0


def test_place_translation_overlay():
    """Overlay mode places translation on top of original text."""
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(x=50, y=50, w=200, h=60, text="你好", translation="Hello")
    result = placer.place_translation(region, overlay="always")
    assert len(result) >= 1
    assert result[0][0] == "Hello"
    # Should be within the region bounds
    assert result[0][1] >= region.x
    assert result[0][2] >= region.y


def test_place_translation_overlay_with_group():
    """Overlay mode with a group uses the group bbox."""
    placer = TextPlacer(image_width=800, image_height=600)
    r1 = TextRegion(x=50, y=50, w=100, h=25, text="你好", translation="Hello World")
    r2 = TextRegion(x=55, y=80, w=90, h=25, text="世界", translation="")
    group = [r1, r2]
    result = placer.place_translation(r1, overlay="always", group=group)
    assert len(result) >= 1
    # Should be placed at or near the group bbox origin
    assert result[0][1] >= 50


def test_place_translation_clamped_at_right_edge():
    """When text is at right edge, fallback is clamped into frame."""
    placer = TextPlacer(image_width=200, image_height=200)
    region = TextRegion(x=140, y=50, w=50, h=30, text="你好",
                        translation="Hello World Long Text")
    placer.occupied = [(region.x, region.y, region.w, region.h)]
    result = placer.place_translation(region)
    for text, x, y, fs in result:
        tw, _ = placer._estimate_text_size(text, fs)
        assert x >= 0
        assert x + tw <= placer.image_width


def test_place_translation_clamped_at_bottom_edge():
    """When text is at bottom edge, placement is clamped."""
    placer = TextPlacer(image_width=200, image_height=100)
    region = TextRegion(x=10, y=70, w=180, h=25, text="你好",
                        translation="Hello World Long Text Here")
    placer.occupied = [(region.x, region.y, region.w, region.h)]
    result = placer.place_translation(region)
    for text, x, y, fs in result:
        assert y >= 0


def test_place_translation_clamped_at_left_edge():
    placer = TextPlacer(image_width=300, image_height=300)
    region = TextRegion(x=0, y=50, w=60, h=30, text="你好",
                        translation="A very long translation sentence here")
    result = placer.place_translation(region, overlay="always")
    for _, x, y, _ in result:
        assert x >= 0
        assert y >= 0


def test_wrap_text_short():
    placer = TextPlacer(image_width=800, image_height=600)
    lines = placer._wrap_text("Hello", 14, 200)
    assert lines == ["Hello"]


def test_wrap_text_long():
    placer = TextPlacer(image_width=800, image_height=600)
    lines = placer._wrap_text("Hello World this is a test", 14, 80)
    assert len(lines) > 1
    # Reconstructed text should match original
    assert " ".join(lines) == "Hello World this is a test"


def test_wrap_text_single_long_word():
    placer = TextPlacer(image_width=800, image_height=600)
    lines = placer._wrap_text("Superlongword", 14, 40)
    assert len(lines) >= 1
    assert "".join(lines) == "Superlongword"


def test_place_pinyin_per_char_horizontal():
    """Per-char pinyin placed above each character for horizontal text."""
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=100, w=120, h=30, text="你好世",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì")],
    )
    placements = placer.place_pinyin_per_char(region)
    assert len(placements) == 3
    assert placements[0][0] == "nǐ"
    assert placements[1][0] == "hǎo"
    assert placements[2][0] == "shì"
    for _, _, y, _ in placements:
        assert y < region.y


def test_place_pinyin_per_char_with_punctuation():
    """Punctuation characters should also get placements."""
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=100, w=180, h=30, text="你好！世界。",
        char_pinyin=[
            ("你", "nǐ"), ("好", "hǎo"), ("！", "！"),
            ("世", "shì"), ("界", "jiè"), ("。", "。"),
        ],
    )
    placements = placer.place_pinyin_per_char(region)
    assert len(placements) == 6
    assert placements[2][0] == "！"
    assert placements[5][0] == "。"


def test_place_pinyin_per_char_horizontal_clamped_at_top():
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=2, w=120, h=30, text="你好世",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì")],
    )
    placements = placer.place_pinyin_per_char(region)
    assert len(placements) == 3
    for _, x, y, _ in placements:
        assert x >= 0
        assert y >= 0


def test_place_pinyin_per_char_vertical():
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=50, w=30, h=200, text="你好世界",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì"), ("界", "jiè")],
    )
    assert region.is_vertical
    placements = placer.place_pinyin_per_char(region)
    assert len(placements) == 4
    for _, x, _, _ in placements:
        assert x >= region.x + region.w


def test_place_pinyin_per_char_vertical_clamped_at_right():
    placer = TextPlacer(image_width=100, image_height=600)
    region = TextRegion(
        x=70, y=50, w=28, h=200, text="你好世界",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì"), ("界", "jiè")],
    )
    placements = placer.place_pinyin_per_char(region)
    for _, x, y, fs in placements:
        assert x >= 0
        assert y >= 0


def test_place_pinyin_per_char_overlay_horizontal():
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=100, w=120, h=30, text="你好世",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì")],
    )
    placements = placer.place_pinyin_per_char(region, overlay="always")
    assert len(placements) == 3
    for _, _, y, _ in placements:
        assert y == region.y


def test_place_pinyin_per_char_overlay_vertical():
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(
        x=50, y=50, w=30, h=200, text="你好世界",
        char_pinyin=[("你", "nǐ"), ("好", "hǎo"), ("世", "shì"), ("界", "jiè")],
    )
    placements = placer.place_pinyin_per_char(region, overlay="always")
    assert len(placements) == 4
    for _, x, _, _ in placements:
        assert x == region.x


def test_place_pinyin_per_char_empty():
    placer = TextPlacer(image_width=800, image_height=600)
    region = TextRegion(x=50, y=100, w=120, h=30, text="你好", char_pinyin=[])
    assert placer.place_pinyin_per_char(region) == []


def test_compute_placements_translation_mode():
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=100, h=30, text="你好", translation="Hello"),
        TextRegion(x=50, y=150, w=100, h=30, text="世界", translation="World"),
    ]
    placements = placer.compute_placements(regions, "translation")
    assert len(placements) >= 2
    texts = [p[0] for p in placements]
    assert "Hello" in texts
    assert "World" in texts


def test_compute_placements_translation_overlay():
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=200, h=60, text="你好", translation="Hello"),
    ]
    placements = placer.compute_placements(regions, "translation", overlay="always")
    assert len(placements) >= 1
    assert placements[0][0] == "Hello"


def test_compute_placements_grouped_translation():
    """Grouped regions: only the first region has a translation."""
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=100, h=25, text="你好",
                   translation="Hello World", group_id=0),
        TextRegion(x=55, y=80, w=90, h=25, text="世界",
                   translation="", group_id=0),
    ]
    placements = placer.compute_placements(regions, "translation")
    # Should have at least 1 placement (possibly multi-line)
    assert len(placements) >= 1
    texts = " ".join(p[0] for p in placements)
    assert "Hello" in texts
    assert "World" in texts


def test_compute_placements_pinyin_mode_per_char():
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(
            x=50, y=100, w=80, h=30, text="你好",
            char_pinyin=[("你", "nǐ"), ("好", "hǎo")],
        ),
    ]
    placements = placer.compute_placements(regions, "pinyin")
    assert len(placements) == 2
    assert placements[0][0] == "nǐ"
    assert placements[1][0] == "hǎo"


def test_compute_placements_empty_annotations_skipped():
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=100, h=30, text="你好", translation=""),
    ]
    placements = placer.compute_placements(regions, "translation")
    assert len(placements) == 0


def test_compute_placements_auto_fits_beside():
    """Auto mode should place beside when there's room."""
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=100, h=30, text="你好", translation="Hello"),
    ]
    placements = placer.compute_placements(regions, "translation", overlay="auto")
    assert len(placements) >= 1
    assert placements[0][0] == "Hello"
    assert not placer.used_overlay


def test_compute_placements_auto_falls_back_to_overlay():
    """Auto mode should fall back to overlay when no beside position fits."""
    # Tiny image where beside placement can't fit
    placer = TextPlacer(image_width=110, image_height=40)
    regions = [
        TextRegion(x=0, y=0, w=110, h=40, text="你好", translation="Hello"),
    ]
    placements = placer.compute_placements(regions, "translation", overlay="auto")
    assert len(placements) >= 1
    assert placer.used_overlay


def test_used_overlay_false_for_never():
    placer = TextPlacer(image_width=800, image_height=600)
    regions = [
        TextRegion(x=50, y=50, w=100, h=30, text="你好", translation="Hello"),
    ]
    placer.compute_placements(regions, "translation", overlay="never")
    assert not placer.used_overlay


def test_fits_boundary():
    placer = TextPlacer(image_width=100, image_height=100)
    assert placer._fits(0, 0, 50, 50) is True
    assert placer._fits(90, 90, 50, 50) is False
    assert placer._fits(-1, 0, 10, 10) is False


def test_clamp_basic():
    placer = TextPlacer(image_width=100, image_height=100)
    assert placer._clamp(0, 0, 50, 50) == (0, 0)
    assert placer._clamp(-10, -5, 20, 20) == (0, 0)
    assert placer._clamp(90, 90, 20, 20) == (80, 80)
    assert placer._clamp(50, 50, 100, 100) == (0, 0)
