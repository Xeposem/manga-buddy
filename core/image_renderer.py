import os

from PIL import Image, ImageDraw, ImageFont

from models.text_region import TextRegion
from core.text_grouper import group_bbox

# Candidate fonts in preference order.  CJK-capable fonts come first so that
# Japanese text, romaji with diacritics, and mixed CJK/Latin all render
# correctly.  Paths cover Windows, macOS, and common Linux locations.
_FONT_CANDIDATES = [
    # Windows – CJK-capable
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    # Windows – good Latin/Unicode fallback
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Linux – Noto CJK
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]


def _find_system_font():
    """Return the first available font path from the candidate list."""
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


class ImageRenderer:
    def __init__(self):
        self._font_cache = {}
        self._font_path = _find_system_font()

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            if self._font_path:
                self._font_cache[size] = ImageFont.truetype(self._font_path, size)
            else:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    def render(self, image: Image.Image, placements: list,
               regions: list = None, overlay: bool = False,
               bg_color=(255, 255, 255, 200),
               text_color=(0, 0, 0, 255)) -> Image.Image:
        result = image.copy().convert("RGBA")
        draw_result = ImageDraw.Draw(result)

        # When overlay mode is on, white-out text regions (grouped by bubble)
        if overlay and regions:
            blanked = set()
            groups_map = {}
            for r in regions:
                if r.group_id >= 0:
                    groups_map.setdefault(r.group_id, []).append(r)
                else:
                    groups_map.setdefault(id(r), [r])

            for gid, group in groups_map.items():
                gx, gy, gw, gh = group_bbox(group)
                draw_result.rectangle(
                    [gx, gy, gx + gw, gy + gh],
                    fill=(255, 255, 255, 255),
                )

        overlay_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_layer)

        for text, x, y, font_size in placements:
            font = self._get_font(font_size)
            bbox = draw.textbbox((x, y), text, font=font)
            pad = 2
            draw.rectangle(
                [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
                fill=bg_color,
            )
            draw.text((x, y), text, fill=text_color, font=font)

        result = Image.alpha_composite(result, overlay_layer)
        return result
