import unicodedata
from pypinyin import pinyin, Style

from models.text_region import TextRegion


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


class PinyinConverter:
    def convert(self, text: str) -> str:
        result = pinyin(text, style=Style.TONE)
        return " ".join(syllable[0] for syllable in result)

    def convert_per_char(self, text: str) -> list:
        """Return list of (character, annotation) for each character.

        Chinese characters get their pinyin; punctuation and other
        characters get themselves as the annotation.

        pypinyin may group consecutive punctuation into one entry,
        so we align by consuming source characters to match each
        pypinyin output entry.
        """
        if not text:
            return []

        py_result = pinyin(text, style=Style.TONE)
        pairs = []
        src_idx = 0

        for entry in py_result:
            py_str = entry[0]

            if src_idx >= len(text):
                break

            # If this entry is a pinyin syllable (contains latin letters),
            # it corresponds to exactly one Chinese character.
            has_latin = any(c.isalpha() and ord(c) < 0x3000 for c in py_str)

            if has_latin and _is_chinese_char(text[src_idx]):
                pairs.append((text[src_idx], py_str))
                src_idx += 1
            else:
                # Punctuation group — consume characters from source that
                # match the grouped output string.
                for ch in py_str:
                    if src_idx < len(text) and text[src_idx] == ch:
                        pairs.append((ch, ch))
                        src_idx += 1

        # Catch any remaining characters not covered by pypinyin
        while src_idx < len(text):
            pairs.append((text[src_idx], text[src_idx]))
            src_idx += 1

        return pairs

    def convert_batch(self, regions: list) -> list:
        for region in regions:
            region.pinyin = self.convert(region.text)
            region.char_pinyin = self.convert_per_char(region.text)
        return regions
