from core.text_grouper import group_regions, group_text, group_bbox, _gap
from models.text_region import TextRegion


def test_gap_overlapping():
    a = TextRegion(x=10, y=10, w=50, h=20, text="A")
    b = TextRegion(x=30, y=10, w=50, h=20, text="B")
    assert _gap(a, b) == 0


def test_gap_horizontal():
    a = TextRegion(x=10, y=10, w=50, h=20, text="A")
    b = TextRegion(x=80, y=10, w=50, h=20, text="B")
    assert _gap(a, b) == 20  # 80 - (10+50) = 20


def test_gap_vertical():
    a = TextRegion(x=10, y=10, w=50, h=20, text="A")
    b = TextRegion(x=10, y=60, w=50, h=20, text="B")
    assert _gap(a, b) == 30  # 60 - (10+20) = 30


def test_gap_diagonal():
    a = TextRegion(x=0, y=0, w=10, h=10, text="A")
    b = TextRegion(x=50, y=50, w=10, h=10, text="B")
    assert _gap(a, b) == 40  # max(50-10, 50-10) = 40


def test_group_single_region():
    regions = [TextRegion(x=10, y=10, w=100, h=30, text="你好")]
    groups = group_regions(regions)
    assert len(groups) == 1
    assert len(groups[0]) == 1


def test_group_two_close_lines():
    """Two lines close together vertically (same speech bubble)."""
    r1 = TextRegion(x=50, y=50, w=120, h=25, text="你好世界")
    r2 = TextRegion(x=55, y=80, w=110, h=25, text="测试文本")
    groups = group_regions([r1, r2])
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_group_two_far_apart():
    """Two regions far apart should be separate groups."""
    r1 = TextRegion(x=10, y=10, w=100, h=25, text="你好")
    r2 = TextRegion(x=10, y=400, w=100, h=25, text="世界")
    groups = group_regions([r1, r2])
    assert len(groups) == 2


def test_group_vertical_text_same_column():
    """Vertical text lines in the same column should group."""
    r1 = TextRegion(x=50, y=10, w=25, h=120, text="你好世界")
    r2 = TextRegion(x=80, y=15, w=25, h=110, text="测试文本")
    groups = group_regions([r1, r2])
    assert len(groups) == 1


def test_group_three_regions_two_bubbles():
    """Three regions: two close together, one far away."""
    r1 = TextRegion(x=50, y=50, w=100, h=25, text="你好")
    r2 = TextRegion(x=55, y=80, w=90, h=25, text="世界")
    r3 = TextRegion(x=400, y=50, w=100, h=25, text="测试")
    groups = group_regions([r1, r2, r3])
    assert len(groups) == 2
    sizes = sorted(len(g) for g in groups)
    assert sizes == [1, 2]


def test_group_empty():
    assert group_regions([]) == []


def test_group_text_concatenation():
    r1 = TextRegion(x=50, y=50, w=100, h=25, text="你好")
    r2 = TextRegion(x=55, y=80, w=90, h=25, text="世界")
    assert group_text([r1, r2]) == "你好世界"


def test_group_bbox_single():
    r = TextRegion(x=10, y=20, w=100, h=30, text="test")
    assert group_bbox([r]) == (10, 20, 100, 30)


def test_group_bbox_multiple():
    r1 = TextRegion(x=10, y=20, w=100, h=30, text="A")
    r2 = TextRegion(x=20, y=60, w=80, h=25, text="B")
    x, y, w, h = group_bbox([r1, r2])
    assert x == 10
    assert y == 20
    assert w == 100  # 110 - 10
    assert h == 65   # 85 - 20


def test_group_reading_order_horizontal():
    """Horizontal text groups should be sorted top-to-bottom."""
    r1 = TextRegion(x=50, y=80, w=100, h=25, text="B")
    r2 = TextRegion(x=50, y=50, w=100, h=25, text="A")
    groups = group_regions([r1, r2])
    assert len(groups) == 1
    assert groups[0][0].text == "A"
    assert groups[0][1].text == "B"
