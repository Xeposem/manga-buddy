"""Diagnostic script to test Japanese OCR with PaddleOCR.

Creates synthetic manga-style text bubbles (vertical and horizontal)
and tests PaddleOCR's ability to recognize them.
"""

import os
import sys
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def find_jp_font():
    """Find a Japanese-capable font on the system."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/msmincho.ttc",
        # Linux
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def create_horizontal_bubble(text, filename, font_size=36):
    """Create a manga-style speech bubble with horizontal Japanese text."""
    font_path = find_jp_font()
    if not font_path:
        print("WARNING: No Japanese font found, using default")
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    # White bubble on light gray background
    img = Image.new("RGB", (400, 200), color=(230, 230, 230))
    draw = ImageDraw.Draw(img)

    # Draw bubble
    draw.ellipse([20, 20, 380, 180], fill="white", outline="black", width=2)

    # Draw text centered
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (400 - tw) // 2
    y = (200 - th) // 2
    draw.text((x, y), text, fill="black", font=font)

    path = os.path.join(SAMPLES_DIR, filename)
    img.save(path)
    print(f"Created: {path}")
    return img


def create_vertical_bubble(text, filename, font_size=36):
    """Create a manga-style speech bubble with vertical Japanese text."""
    font_path = find_jp_font()
    if not font_path:
        print("WARNING: No Japanese font found, using default")
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    char_h = font_size + 4
    total_h = len(text) * char_h + 40
    img_h = max(total_h + 40, 300)
    img_w = 200

    img = Image.new("RGB", (img_w, img_h), color=(230, 230, 230))
    draw = ImageDraw.Draw(img)

    # Draw bubble
    draw.ellipse([10, 10, img_w - 10, img_h - 10], fill="white", outline="black", width=2)

    # Draw each character vertically, centered horizontally
    x = img_w // 2 - font_size // 2
    y_start = (img_h - len(text) * char_h) // 2
    for i, char in enumerate(text):
        draw.text((x, y_start + i * char_h), char, fill="black", font=font)

    path = os.path.join(SAMPLES_DIR, filename)
    img.save(path)
    print(f"Created: {path}")
    return img


def create_multi_column_vertical(lines, filename, font_size=36):
    """Create vertical text with multiple columns (right-to-left), like real manga."""
    font_path = find_jp_font()
    if not font_path:
        print("WARNING: No Japanese font found, using default")
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

    char_h = font_size + 4
    col_w = font_size + 16
    max_chars = max(len(line) for line in lines)
    img_h = max(max_chars * char_h + 80, 300)
    img_w = len(lines) * col_w + 80

    img = Image.new("RGB", (img_w, img_h), color="white")
    draw = ImageDraw.Draw(img)

    # Columns go right-to-left
    for col_idx, line in enumerate(lines):
        x = img_w - 40 - (col_idx + 1) * col_w + col_w // 2 - font_size // 2
        y_start = 40
        for char_idx, char in enumerate(line):
            draw.text((x, y_start + char_idx * char_h), char, fill="black", font=font)

    path = os.path.join(SAMPLES_DIR, filename)
    img.save(path)
    print(f"Created: {path}")
    return img


def test_paddleocr(image, lang="japan", label=""):
    """Run PaddleOCR on an image and print results."""
    from core.ocr_engine import OcrEngine

    engine = OcrEngine(lang=lang)
    regions = engine.detect(image, lang=lang)

    print(f"\n{'='*60}")
    print(f"PaddleOCR results ({label}, lang={lang}):")
    print(f"{'='*60}")
    if not regions:
        print("  ** No text detected **")
    else:
        for i, r in enumerate(regions):
            print(f"  [{i}] text='{r.text}' conf={r.confidence:.3f} "
                  f"bbox=({r.x},{r.y},{r.w},{r.h})")
    return regions


def main():
    font_path = find_jp_font()
    if not font_path:
        print("ERROR: No Japanese font found on this system.")
        print("Install a Japanese font (e.g., MS Gothic) to run this test.")
        return

    print(f"Using font: {font_path}")
    print()

    # Test 1: Horizontal text (should work okay)
    print("=" * 60)
    print("TEST 1: Horizontal Japanese text")
    print("=" * 60)
    img1 = create_horizontal_bubble("こんにちは", "horizontal_hello.png")
    test_paddleocr(img1, lang="japan", label="horizontal こんにちは")
    test_paddleocr(img1, lang="chinese", label="horizontal こんにちは (chinese model)")

    # Test 2: Vertical single line
    print("\n" + "=" * 60)
    print("TEST 2: Vertical Japanese text (single column)")
    print("=" * 60)
    img2 = create_vertical_bubble("こんにちは", "vertical_hello.png")
    test_paddleocr(img2, lang="japan", label="vertical こんにちは")

    # Test 3: Vertical with kanji
    print("\n" + "=" * 60)
    print("TEST 3: Vertical Japanese with kanji")
    print("=" * 60)
    img3 = create_vertical_bubble("東京タワー", "vertical_tokyo.png")
    test_paddleocr(img3, lang="japan", label="vertical 東京タワー")

    # Test 4: Multi-column vertical (manga-style)
    print("\n" + "=" * 60)
    print("TEST 4: Multi-column vertical (manga-style, right-to-left)")
    print("=" * 60)
    img4 = create_multi_column_vertical(
        ["お前はもう", "死んでいる"],
        "multi_column_vertical.png",
    )
    test_paddleocr(img4, lang="japan", label="multi-col vertical")

    # Test 5: Longer sentence vertical
    print("\n" + "=" * 60)
    print("TEST 5: Longer vertical sentence")
    print("=" * 60)
    img5 = create_vertical_bubble("私の名前は田中です", "vertical_long.png")
    test_paddleocr(img5, lang="japan", label="vertical 私の名前は田中です")

    # Test 6: Horizontal sentence (control)
    print("\n" + "=" * 60)
    print("TEST 6: Horizontal sentence (control)")
    print("=" * 60)
    img6 = create_horizontal_bubble("私の名前は田中です", "horizontal_long.png", font_size=28)
    test_paddleocr(img6, lang="japan", label="horizontal 私の名前は田中です")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Check the images in tests/samples/ to verify they look correct.")
    print("Compare horizontal vs vertical recognition accuracy above.")


if __name__ == "__main__":
    main()
