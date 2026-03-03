from PIL import Image
from core.image_renderer import ImageRenderer
from models.text_region import TextRegion


def test_render_returns_image():
    renderer = ImageRenderer()
    img = Image.new("RGB", (200, 100), "white")
    placements = [("Hello", 10, 10, 14)]
    result = renderer.render(img, placements)
    assert isinstance(result, Image.Image)
    assert result.size == (200, 100)
    assert result.mode == "RGBA"


def test_render_no_placements():
    renderer = ImageRenderer()
    img = Image.new("RGB", (200, 100), "white")
    result = renderer.render(img, [])
    assert isinstance(result, Image.Image)
    assert result.size == (200, 100)


def test_render_multiple_placements():
    renderer = ImageRenderer()
    img = Image.new("RGB", (400, 300), "white")
    placements = [
        ("Hello", 10, 10, 14),
        ("World", 10, 50, 16),
        ("Test", 200, 10, 12),
    ]
    result = renderer.render(img, placements)
    assert isinstance(result, Image.Image)


def test_render_does_not_modify_original():
    renderer = ImageRenderer()
    img = Image.new("RGB", (200, 100), "white")
    original_data = list(img.getdata())
    renderer.render(img, [("Text", 10, 10, 14)])
    assert list(img.getdata()) == original_data


def test_render_overlay_blanks_regions():
    """Overlay mode should white-out original text regions."""
    renderer = ImageRenderer()
    img = Image.new("RGB", (200, 100), (50, 50, 50))
    regions = [TextRegion(x=10, y=10, w=80, h=30, text="你好")]
    placements = [("Hello", 10, 10, 14)]
    result = renderer.render(img, placements, regions=regions, overlay=True)
    assert isinstance(result, Image.Image)
    # The blanked region should be white (255, 255, 255) under the annotation
    # Check a pixel inside the blanked region but outside text rendering
    px = result.getpixel((50, 35))
    assert px[0] == 255 and px[1] == 255 and px[2] == 255


def test_render_no_overlay_preserves_background():
    """Without overlay, the background under the text region is untouched."""
    renderer = ImageRenderer()
    img = Image.new("RGB", (200, 100), (50, 50, 50))
    regions = [TextRegion(x=10, y=10, w=80, h=30, text="你好")]
    placements = [("Hello", 100, 10, 14)]
    result = renderer.render(img, placements, regions=regions, overlay=False)
    # Pixel inside original text region but outside placement should be original color
    px = result.getpixel((50, 25))
    assert px[0] == 50 and px[1] == 50 and px[2] == 50
