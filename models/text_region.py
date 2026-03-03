from dataclasses import dataclass, field


@dataclass
class TextRegion:
    x: int
    y: int
    w: int
    h: int
    text: str
    confidence: float = 0.0
    translation: str = ""
    pinyin: str = ""
    # Raw 4-point polygon from OCR: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    polygon: list = field(default_factory=list)
    # Per-character pinyin: [(char, pinyin_str), ...]
    char_pinyin: list = field(default_factory=list)
    # Group index assigned by text_grouper (-1 = ungrouped)
    group_id: int = -1

    @property
    def is_vertical(self) -> bool:
        """Detect vertical text: bbox is taller than it is wide."""
        if not self.text:
            return False
        # Single-character regions are ambiguous — treat as horizontal
        if len(self.text) <= 1:
            return False
        return self.h > self.w * 1.2
