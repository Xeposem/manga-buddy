from core.pinyin_converter import PinyinConverter
from models.text_region import TextRegion


def test_convert_basic():
    pc = PinyinConverter()
    result = pc.convert("你好")
    assert "nǐ" in result
    assert "hǎo" in result


def test_convert_empty():
    pc = PinyinConverter()
    result = pc.convert("")
    assert result == ""


def test_convert_single_char():
    pc = PinyinConverter()
    result = pc.convert("中")
    assert "zhōng" in result


def test_convert_per_char():
    pc = PinyinConverter()
    pairs = pc.convert_per_char("你好")
    assert len(pairs) == 2
    assert pairs[0][0] == "你"
    assert "nǐ" in pairs[0][1]
    assert pairs[1][0] == "好"
    assert "hǎo" in pairs[1][1]


def test_convert_per_char_empty():
    pc = PinyinConverter()
    pairs = pc.convert_per_char("")
    assert pairs == []


def test_convert_per_char_single():
    pc = PinyinConverter()
    pairs = pc.convert_per_char("中")
    assert len(pairs) == 1
    assert pairs[0][0] == "中"
    assert "zhōng" in pairs[0][1]


def test_convert_per_char_with_punctuation():
    """Punctuation should map to itself, one entry per character."""
    pc = PinyinConverter()
    pairs = pc.convert_per_char("你好！世界。")
    assert len(pairs) == 6
    assert pairs[0] == ("你", "nǐ")
    assert pairs[1] == ("好", "hǎo")
    assert pairs[2] == ("！", "！")
    assert pairs[3] == ("世", "shì")
    assert pairs[4] == ("界", "jiè")
    assert pairs[5] == ("。", "。")


def test_convert_per_char_consecutive_punctuation():
    """Consecutive punctuation like ？！ should be split correctly."""
    pc = PinyinConverter()
    pairs = pc.convert_per_char("什么？！")
    assert len(pairs) == 4
    assert pairs[0][0] == "什"
    assert pairs[1][0] == "么"
    assert pairs[2] == ("？", "？")
    assert pairs[3] == ("！", "！")


def test_convert_per_char_ellipsis():
    """Dots should each be their own entry."""
    pc = PinyinConverter()
    pairs = pc.convert_per_char("你好...")
    assert len(pairs) == 5
    assert pairs[2] == (".", ".")
    assert pairs[3] == (".", ".")
    assert pairs[4] == (".", ".")


def test_convert_per_char_brackets():
    pc = PinyinConverter()
    pairs = pc.convert_per_char("「测试」")
    assert len(pairs) == 4
    assert pairs[0] == ("「", "「")
    assert pairs[1][0] == "测"
    assert pairs[2][0] == "试"
    assert pairs[3] == ("」", "」")


def test_convert_batch():
    pc = PinyinConverter()
    regions = [
        TextRegion(x=0, y=0, w=10, h=10, text="你好"),
        TextRegion(x=0, y=0, w=10, h=10, text="世界"),
    ]
    result = pc.convert_batch(regions)
    assert len(result) == 2
    assert result[0].pinyin != ""
    assert result[1].pinyin != ""
    assert "nǐ" in result[0].pinyin
    assert "shì" in result[1].pinyin
    assert len(result[0].char_pinyin) == 2
    assert result[0].char_pinyin[0] == ("你", "nǐ")
    assert len(result[1].char_pinyin) == 2


def test_convert_batch_with_punctuation():
    pc = PinyinConverter()
    regions = [TextRegion(x=0, y=0, w=10, h=10, text="你好！")]
    result = pc.convert_batch(regions)
    assert len(result[0].char_pinyin) == 3
    assert result[0].char_pinyin[2] == ("！", "！")


def test_convert_batch_returns_same_list():
    pc = PinyinConverter()
    regions = [TextRegion(x=0, y=0, w=10, h=10, text="测试")]
    result = pc.convert_batch(regions)
    assert result is regions
    assert len(result[0].char_pinyin) == 2
