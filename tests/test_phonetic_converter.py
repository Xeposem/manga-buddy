"""Tests for all phonetic converter classes and language detection."""

import pytest

from models.text_region import TextRegion
from core.phonetic_converter import (
    ChinesePinyinConverter,
    JapaneseFuriganaConverter,
    JapaneseRomajiConverter,
    KoreanRomanizer,
    detect_language,
)


# ── Chinese Pinyin Converter ──

class TestChinesePinyinConverter:
    def setup_method(self):
        self.conv = ChinesePinyinConverter()

    def test_convert_basic(self):
        result = self.conv.convert("你好")
        assert "nǐ" in result
        assert "hǎo" in result

    def test_convert_empty(self):
        assert self.conv.convert("") == ""

    def test_convert_single_char(self):
        result = self.conv.convert("中")
        assert "zhōng" in result

    def test_convert_per_char(self):
        pairs = self.conv.convert_per_char("你好")
        assert len(pairs) == 2
        assert pairs[0][0] == "你"
        assert "nǐ" in pairs[0][1]
        assert pairs[1][0] == "好"
        assert "hǎo" in pairs[1][1]

    def test_convert_per_char_empty(self):
        assert self.conv.convert_per_char("") == []

    def test_convert_per_char_with_punctuation(self):
        pairs = self.conv.convert_per_char("你好！世界。")
        assert len(pairs) == 6
        assert pairs[2] == ("！", "！")
        assert pairs[5] == ("。", "。")

    def test_convert_batch(self):
        regions = [
            TextRegion(x=0, y=0, w=10, h=10, text="你好"),
            TextRegion(x=0, y=0, w=10, h=10, text="世界"),
        ]
        result = self.conv.convert_batch(regions)
        assert len(result) == 2
        assert result[0].pinyin != ""
        assert result[1].pinyin != ""
        assert "nǐ" in result[0].pinyin
        assert len(result[0].char_pinyin) == 2

    def test_convert_batch_returns_same_list(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="测试")]
        result = self.conv.convert_batch(regions)
        assert result is regions


# ── Japanese Furigana Converter ──

class TestJapaneseFuriganaConverter:
    def setup_method(self):
        self.conv = JapaneseFuriganaConverter()

    def test_convert_basic(self):
        result = self.conv.convert("漢字")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_convert_empty(self):
        assert self.conv.convert("") == ""

    def test_convert_hiragana_passthrough(self):
        """Hiragana should pass through as-is."""
        result = self.conv.convert("ありがとう")
        assert "ありがとう" in result

    def test_convert_katakana(self):
        """Katakana should be converted to hiragana."""
        result = self.conv.convert("カタカナ")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_convert_per_char(self):
        pairs = self.conv.convert_per_char("東京")
        assert len(pairs) == 2
        assert pairs[0][0] == "東"
        assert pairs[1][0] == "京"

    def test_convert_per_char_empty(self):
        assert self.conv.convert_per_char("") == []

    def test_convert_per_char_mixed(self):
        """Mixed kanji and kana should produce correct pairs."""
        pairs = self.conv.convert_per_char("食べる")
        assert len(pairs) == 3
        assert pairs[0][0] == "食"
        # べ and る are hiragana, should pass through
        assert pairs[1][0] == "べ"
        assert pairs[2][0] == "る"

    def test_convert_batch(self):
        regions = [
            TextRegion(x=0, y=0, w=10, h=10, text="東京"),
        ]
        result = self.conv.convert_batch(regions)
        assert result[0].pinyin != ""
        assert len(result[0].char_pinyin) == 2


# ── Japanese Romaji Converter ──

class TestJapaneseRomajiConverter:
    def setup_method(self):
        self.conv = JapaneseRomajiConverter()

    def test_convert_basic(self):
        result = self.conv.convert("東京")
        assert isinstance(result, str)
        # Should contain latin characters
        assert any(c.isascii() and c.isalpha() for c in result)

    def test_convert_empty(self):
        assert self.conv.convert("") == ""

    def test_convert_hiragana(self):
        result = self.conv.convert("ありがとう")
        assert isinstance(result, str)
        assert any(c.isascii() and c.isalpha() for c in result)

    def test_convert_per_char(self):
        pairs = self.conv.convert_per_char("東京")
        assert len(pairs) == 2
        assert pairs[0][0] == "東"
        assert pairs[1][0] == "京"

    def test_convert_per_char_empty(self):
        assert self.conv.convert_per_char("") == []

    def test_convert_batch(self):
        regions = [
            TextRegion(x=0, y=0, w=10, h=10, text="東京"),
        ]
        result = self.conv.convert_batch(regions)
        assert result[0].pinyin != ""
        assert any(c.isascii() and c.isalpha() for c in result[0].pinyin)


# ── Korean Romanizer ──

class TestKoreanRomanizer:
    def setup_method(self):
        self.conv = KoreanRomanizer()

    def test_convert_basic(self):
        result = self.conv.convert("안녕하세요")
        assert isinstance(result, str)
        assert any(c.isascii() and c.isalpha() for c in result)

    def test_convert_empty(self):
        assert self.conv.convert("") == ""

    def test_convert_per_char(self):
        pairs = self.conv.convert_per_char("한국")
        assert len(pairs) == 2
        assert pairs[0][0] == "한"
        assert pairs[1][0] == "국"
        # Annotations should be latin
        assert any(c.isascii() and c.isalpha() for c in pairs[0][1])

    def test_convert_per_char_empty(self):
        assert self.conv.convert_per_char("") == []

    def test_convert_per_char_with_punctuation(self):
        pairs = self.conv.convert_per_char("안녕!")
        assert len(pairs) == 3
        assert pairs[2] == ("!", "!")

    def test_convert_batch(self):
        regions = [
            TextRegion(x=0, y=0, w=10, h=10, text="안녕하세요"),
        ]
        result = self.conv.convert_batch(regions)
        assert result[0].pinyin != ""


# ── Language Detection ──

class TestLanguageDetection:
    def test_detect_chinese(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="你好世界")]
        assert detect_language(regions) == "chinese"

    def test_detect_japanese(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="ありがとうございます")]
        assert detect_language(regions) == "japanese"

    def test_detect_japanese_mixed(self):
        """Japanese with kanji and hiragana should be detected."""
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="食べる東京")]
        assert detect_language(regions) == "japanese"

    def test_detect_korean(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="안녕하세요")]
        assert detect_language(regions) == "korean"

    def test_detect_empty(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="")]
        assert detect_language(regions) == "chinese"

    def test_detect_no_regions(self):
        assert detect_language([]) == "chinese"

    def test_detect_katakana(self):
        regions = [TextRegion(x=0, y=0, w=10, h=10, text="カタカナ")]
        assert detect_language(regions) == "japanese"

    def test_detect_multiple_regions(self):
        regions = [
            TextRegion(x=0, y=0, w=10, h=10, text="안녕"),
            TextRegion(x=0, y=0, w=10, h=10, text="하세요"),
        ]
        assert detect_language(regions) == "korean"
