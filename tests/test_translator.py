import pytest
from core.translator import Translator
from models.text_region import TextRegion


@pytest.fixture(scope="module")
def translator():
    return Translator()


def test_translate_basic(translator):
    result = translator.translate("你好")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result.lower() != "你好"


def test_translate_empty(translator):
    result = translator.translate("")
    assert result == ""


def test_translate_batch_single_group(translator):
    """Two close regions should be grouped and translated together."""
    regions = [
        TextRegion(x=50, y=50, w=100, h=25, text="你好"),
        TextRegion(x=55, y=80, w=90, h=25, text="世界"),
    ]
    result = translator.translate_batch(regions)
    assert len(result) == 2
    # First region has the full group translation
    assert result[0].translation != ""
    # Second region is blank (grouped with first)
    assert result[1].translation == ""
    # Both should share the same group_id
    assert result[0].group_id == result[1].group_id


def test_translate_batch_two_groups(translator):
    """Far apart regions should be separate groups with separate translations."""
    regions = [
        TextRegion(x=10, y=10, w=100, h=25, text="你好"),
        TextRegion(x=10, y=400, w=100, h=25, text="世界"),
    ]
    result = translator.translate_batch(regions)
    assert result[0].translation != ""
    assert result[1].translation != ""
    assert result[0].group_id != result[1].group_id


def test_translate_batch_single_region(translator):
    regions = [TextRegion(x=0, y=0, w=100, h=25, text="测试")]
    result = translator.translate_batch(regions)
    assert result is regions
    assert result[0].translation != ""
    assert result[0].group_id >= 0
