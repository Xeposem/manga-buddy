from models.text_region import TextRegion


def test_text_region_defaults():
    r = TextRegion(x=10, y=20, w=100, h=50, text="hello")
    assert r.x == 10
    assert r.y == 20
    assert r.w == 100
    assert r.h == 50
    assert r.text == "hello"
    assert r.confidence == 0.0
    assert r.translation == ""
    assert r.pinyin == ""
    assert r.polygon == []
    assert r.char_pinyin == []


def test_text_region_with_all_fields():
    r = TextRegion(
        x=0, y=0, w=200, h=80, text="你好",
        confidence=0.95, translation="Hello", pinyin="nǐ hǎo",
        polygon=[[0, 0], [200, 0], [200, 80], [0, 80]],
        char_pinyin=[("你", "nǐ"), ("好", "hǎo")],
    )
    assert r.confidence == 0.95
    assert r.translation == "Hello"
    assert r.pinyin == "nǐ hǎo"
    assert len(r.polygon) == 4
    assert len(r.char_pinyin) == 2


def test_text_region_mutable():
    r = TextRegion(x=0, y=0, w=10, h=10, text="test")
    r.translation = "updated"
    r.pinyin = "updated_pinyin"
    r.char_pinyin = [("t", "t")]
    assert r.translation == "updated"
    assert r.pinyin == "updated_pinyin"
    assert r.char_pinyin == [("t", "t")]


def test_is_vertical_horizontal_text():
    r = TextRegion(x=0, y=0, w=200, h=40, text="你好世界")
    assert r.is_vertical is False


def test_is_vertical_vertical_text():
    r = TextRegion(x=0, y=0, w=30, h=200, text="你好世界")
    assert r.is_vertical is True


def test_is_vertical_single_char():
    r = TextRegion(x=0, y=0, w=30, h=60, text="你")
    assert r.is_vertical is False  # single char is ambiguous, defaults horizontal


def test_is_vertical_empty():
    r = TextRegion(x=0, y=0, w=30, h=200, text="")
    assert r.is_vertical is False
