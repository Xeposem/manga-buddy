"""Phonetic annotation converters for Chinese, Japanese, and Korean text."""

from abc import ABC, abstractmethod

from models.text_region import TextRegion


class PhoneticConverter(ABC):
    """Base class for phonetic annotation converters."""

    @abstractmethod
    def convert(self, text: str) -> str:
        """Convert text to a phonetic annotation string."""

    @abstractmethod
    def convert_per_char(self, text: str) -> list:
        """Return list of (character, annotation) for each character."""

    def convert_batch(self, regions: list) -> list:
        """Annotate a list of TextRegion objects in-place."""
        for region in regions:
            region.pinyin = self.convert(region.text)
            region.char_pinyin = self.convert_per_char(region.text)
        return regions


def _is_chinese_char(ch: str) -> bool:
    """Check if a character is a CJK ideograph."""
    cp = ord(ch)
    return (
        (0x4E00 <= cp <= 0x9FFF)
        or (0x3400 <= cp <= 0x4DBF)
        or (0x20000 <= cp <= 0x2A6DF)
        or (0x2A700 <= cp <= 0x2B73F)
        or (0x2B740 <= cp <= 0x2B81F)
        or (0x2B820 <= cp <= 0x2CEAF)
        or (0xF900 <= cp <= 0xFAFF)
        or (0x2F800 <= cp <= 0x2FA1F)
    )


class ChinesePinyinConverter(PhoneticConverter):
    """Convert Chinese characters to pinyin with tone marks."""

    def __init__(self):
        from pypinyin import pinyin, Style
        self._pinyin = pinyin
        self._style = Style

    def convert(self, text: str) -> str:
        result = self._pinyin(text, style=self._style.TONE)
        return " ".join(syllable[0] for syllable in result)

    def convert_per_char(self, text: str) -> list:
        if not text:
            return []

        py_result = self._pinyin(text, style=self._style.TONE)
        pairs = []
        src_idx = 0

        for entry in py_result:
            py_str = entry[0]

            if src_idx >= len(text):
                break

            has_latin = any(c.isalpha() and ord(c) < 0x3000 for c in py_str)

            if has_latin and _is_chinese_char(text[src_idx]):
                pairs.append((text[src_idx], py_str))
                src_idx += 1
            else:
                for ch in py_str:
                    if src_idx < len(text) and text[src_idx] == ch:
                        pairs.append((ch, ch))
                        src_idx += 1

        while src_idx < len(text):
            pairs.append((text[src_idx], text[src_idx]))
            src_idx += 1

        return pairs


class JapaneseFuriganaConverter(PhoneticConverter):
    """Convert Japanese kanji to furigana (hiragana). Kana passes through."""

    def __init__(self):
        import pykakasi
        self._kakasi = pykakasi.kakasi()

    def convert(self, text: str) -> str:
        if not text:
            return ""
        result = self._kakasi.convert(text)
        return " ".join(item["hira"] for item in result)

    def convert_per_char(self, text: str) -> list:
        if not text:
            return []

        result = self._kakasi.convert(text)
        pairs = []

        for item in result:
            orig = item["orig"]
            hira = item["hira"]

            if len(orig) == 1:
                # Single kana doesn't need furigana; kanji does
                if _is_kana(orig):
                    pairs.append((orig, ""))
                else:
                    pairs.append((orig, hira))
            elif orig != hira:
                # Mixed kanji+kana: split so each kanji gets its reading
                pairs.extend(self._split_furigana(orig, hira))
            else:
                # Punctuation or other unchanged sequences
                for ch in orig:
                    pairs.append((ch, ""))

        return pairs

    def _split_furigana(self, orig, hira):
        """Split mixed kanji+kana so each kanji gets only its reading."""
        # Match kana suffix (account for katakana→hiragana)
        oi = len(orig) - 1
        hi = len(hira) - 1
        while oi >= 0 and _is_kana(orig[oi]) and hi >= 0:
            oi -= 1
            hi -= 1

        # Match kana prefix
        oj, hj = 0, 0
        while oj <= oi and _is_kana(orig[oj]) and hj <= hi:
            oj += 1
            hj += 1

        pairs = []
        # Prefix kana — no furigana needed
        for ch in orig[:oj]:
            pairs.append((ch, ""))

        # Kanji core with remaining reading
        kanji_chars = orig[oj:oi + 1]
        kanji_reading = hira[hj:hi + 1]
        if len(kanji_chars) == 1:
            pairs.append((kanji_chars[0], kanji_reading))
        elif kanji_chars:
            # Multiple kanji — can't reliably split, show on first
            pairs.append((kanji_chars[0], kanji_reading))
            for ch in kanji_chars[1:]:
                pairs.append((ch, ""))

        # Suffix kana — no furigana needed
        for ch in orig[oi + 1:]:
            pairs.append((ch, ""))

        return pairs


class JapaneseRomajiConverter(PhoneticConverter):
    """Convert Japanese text to romaji (latin alphabet)."""

    def __init__(self):
        import pykakasi
        self._kakasi = pykakasi.kakasi()

    def convert(self, text: str) -> str:
        if not text:
            return ""
        result = self._kakasi.convert(text)
        return " ".join(item["hepburn"] for item in result)

    def convert_per_char(self, text: str) -> list:
        if not text:
            return []

        result = self._kakasi.convert(text)
        pairs = []

        for item in result:
            orig = item["orig"]
            romaji = item["hepburn"]

            if len(orig) == 1:
                pairs.append((orig, romaji))
            elif all(_is_kana(ch) for ch in orig):
                # Kana-only group: convert individually
                for ch in orig:
                    r = self._kakasi.convert(ch)
                    pairs.append((ch, r[0]["hepburn"] if r else ch))
            elif orig == romaji:
                # Unchanged (punctuation, ASCII, etc.)
                for ch in orig:
                    pairs.append((ch, ch))
            else:
                # Mixed kanji+kana: split so each part gets its romaji
                pairs.extend(self._split_romaji(orig, romaji))

        return pairs

    def _split_romaji(self, orig, romaji):
        """Split mixed kanji+kana so each kanji gets only its romaji."""
        # Find kana suffix and prefix boundaries
        oi = len(orig) - 1
        while oi >= 0 and _is_kana(orig[oi]):
            oi -= 1

        oj = 0
        while oj <= oi and _is_kana(orig[oj]):
            oj += 1

        prefix_kana = orig[:oj]
        kanji_core = orig[oj:oi + 1]
        suffix_kana = orig[oi + 1:]

        # Get group romaji for prefix and suffix to subtract from compound
        prefix_romaji = ""
        if prefix_kana:
            r = self._kakasi.convert(prefix_kana)
            prefix_romaji = "".join(item["hepburn"] for item in r)

        suffix_romaji = ""
        if suffix_kana:
            r = self._kakasi.convert(suffix_kana)
            suffix_romaji = "".join(item["hepburn"] for item in r)

        # Kanji romaji = compound minus prefix and suffix
        kanji_romaji = romaji
        if prefix_romaji and kanji_romaji.startswith(prefix_romaji):
            kanji_romaji = kanji_romaji[len(prefix_romaji):]
        if suffix_romaji and kanji_romaji.endswith(suffix_romaji):
            kanji_romaji = kanji_romaji[:-len(suffix_romaji)]

        pairs = []
        # Prefix kana: individual romaji
        for ch in prefix_kana:
            r = self._kakasi.convert(ch)
            pairs.append((ch, r[0]["hepburn"] if r else ch))

        # Kanji core
        if len(kanji_core) == 1:
            pairs.append((kanji_core[0], kanji_romaji))
        elif kanji_core:
            pairs.append((kanji_core[0], kanji_romaji))
            for ch in kanji_core[1:]:
                pairs.append((ch, ""))

        # Suffix kana: individual romaji
        for ch in suffix_kana:
            r = self._kakasi.convert(ch)
            pairs.append((ch, r[0]["hepburn"] if r else ch))

        return pairs


class KoreanRomanizer(PhoneticConverter):
    """Convert Korean hangul to romanized latin text."""

    def __init__(self):
        from korean_romanizer.romanizer import Romanizer
        self._romanizer_cls = Romanizer

    def convert(self, text: str) -> str:
        if not text:
            return ""
        return self._romanizer_cls(text).romanize()

    def convert_per_char(self, text: str) -> list:
        if not text:
            return []

        pairs = []
        for ch in text:
            if _is_hangul(ch):
                romanized = self._romanizer_cls(ch).romanize()
                pairs.append((ch, romanized.strip()))
            else:
                pairs.append((ch, ch))
        return pairs


def _is_cjk_or_kanji(text: str) -> bool:
    """Check if text contains CJK ideographs (shared Chinese/Japanese kanji)."""
    return any(_is_chinese_char(ch) for ch in text)


def _is_hangul(ch: str) -> bool:
    """Check if a character is Korean hangul."""
    cp = ord(ch)
    return (
        (0xAC00 <= cp <= 0xD7AF)  # Hangul Syllables
        or (0x1100 <= cp <= 0x11FF)  # Hangul Jamo
        or (0x3130 <= cp <= 0x318F)  # Hangul Compatibility Jamo
    )


def _is_kana(ch: str) -> bool:
    """Check if a character is hiragana or katakana."""
    cp = ord(ch)
    return (0x3040 <= cp <= 0x309F) or (0x30A0 <= cp <= 0x30FF)


def _is_hiragana(ch: str) -> bool:
    """Check if a character is hiragana."""
    return 0x3040 <= ord(ch) <= 0x309F


def _is_katakana(ch: str) -> bool:
    """Check if a character is katakana."""
    return 0x30A0 <= ord(ch) <= 0x30FF


def detect_language(regions: list) -> str:
    """Detect language from OCR'd text regions.

    Simple heuristic based on character frequency:
    - Mostly hiragana/katakana → Japanese
    - Mostly hangul → Korean
    - Otherwise → Chinese

    Returns: "japanese", "korean", or "chinese"
    """
    total = 0
    jp_chars = 0
    kr_chars = 0

    for region in regions:
        for ch in region.text:
            if ch.isspace() or not ch.strip():
                continue
            total += 1
            if _is_hiragana(ch) or _is_katakana(ch):
                jp_chars += 1
            elif _is_hangul(ch):
                kr_chars += 1

    if total == 0:
        return "chinese"

    if jp_chars / total > 0.1:
        return "japanese"
    if kr_chars / total > 0.3:
        return "korean"
    return "chinese"
