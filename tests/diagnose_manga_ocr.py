"""Test manga-ocr as an alternative to PaddleOCR for Japanese text."""

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from PIL import Image

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")


def test_manga_ocr():
    from manga_ocr import MangaOcr
    print("Loading manga-ocr model (first run downloads ~450MB)...")
    mocr = MangaOcr()

    test_cases = [
        ("horizontal_hello.png", "こんにちは"),
        ("vertical_hello.png", "こんにちは"),
        ("vertical_tokyo.png", "東京タワー"),
        ("multi_column_vertical.png", "お前はもう死んでいる"),
        ("vertical_long.png", "私の名前は田中です"),
        ("horizontal_long.png", "私の名前は田中です"),
    ]

    print()
    for filename, expected in test_cases:
        path = os.path.join(SAMPLES_DIR, filename)
        if not os.path.exists(path):
            print(f"SKIP: {filename} not found")
            continue

        img = Image.open(path)
        result = mocr(img)
        match = "OK" if expected in result or result in expected else "MISMATCH"
        print(f"[{match:8s}] {filename:30s} expected='{expected}' got='{result}'")


if __name__ == "__main__":
    test_manga_ocr()
