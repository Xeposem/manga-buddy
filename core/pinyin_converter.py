"""Backward-compatible re-export of ChinesePinyinConverter as PinyinConverter."""

from core.phonetic_converter import ChinesePinyinConverter, _is_chinese_char  # noqa: F401


class PinyinConverter(ChinesePinyinConverter):
    """Alias for ChinesePinyinConverter — keeps existing imports working."""
    pass
