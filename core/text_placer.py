from models.text_region import TextRegion
from core.text_grouper import group_bbox


class TextPlacer:
    def __init__(self, image_width: int, image_height: int):
        self.image_width = image_width
        self.image_height = image_height
        self.occupied = []

    def _clamp(self, x: int, y: int, w: int, h: int) -> tuple:
        """Clamp placement so it stays fully inside the image bounds."""
        x = max(0, min(x, self.image_width - w))
        y = max(0, min(y, self.image_height - h))
        return x, y

    def _fits(self, x: int, y: int, w: int, h: int) -> bool:
        if x < 0 or y < 0 or x + w > self.image_width or y + h > self.image_height:
            return False
        for ox, oy, ow, oh in self.occupied:
            if x < ox + ow and x + w > ox and y < oy + oh and y + h > oy:
                return False
        return True

    def _estimate_text_size(self, text: str, font_size: int) -> tuple:
        char_width = font_size * 0.6
        w = int(len(text) * char_width) + 8
        h = font_size + 8
        return w, h

    def _wrap_text(self, text: str, font_size: int, max_width: int) -> list:
        """Word-wrap text to fit within max_width.

        Returns a list of lines.
        """
        char_w = font_size * 0.6
        # Max chars that fit in one line (leave small margin)
        max_chars = max(1, int((max_width - 8) / char_w))

        words = text.split()
        if not words:
            return [text]

        lines = []
        current = ""
        for word in words:
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current += " " + word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        # If a single word is still too long, hard-break it
        final = []
        for line in lines:
            while len(line) > max_chars:
                final.append(line[:max_chars])
                line = line[max_chars:]
            final.append(line)

        return final if final else [""]

    def _fit_wrapped(self, text: str, font_size: int,
                     max_w: int, max_h: int) -> tuple:
        """Find font_size and wrapped lines that fit within max_w x max_h.

        Returns (font_size, lines, total_w, total_h).
        """
        while font_size > 6:
            lines = self._wrap_text(text, font_size, max_w)
            line_h = font_size + 4
            total_h = len(lines) * line_h + 8
            widest = max(len(l) for l in lines) if lines else 0
            total_w = int(widest * font_size * 0.6) + 8
            if total_w <= max_w and total_h <= max_h:
                return font_size, lines, total_w, total_h
            font_size -= 1
        lines = self._wrap_text(text, font_size, max_w)
        line_h = font_size + 4
        total_h = len(lines) * line_h + 8
        widest = max(len(l) for l in lines) if lines else 0
        total_w = int(widest * font_size * 0.6) + 8
        return font_size, lines, total_w, total_h

    def _place_overlay(self, text, font_size, region, group):
        """Place text overlaid on top of the original region/group bbox."""
        if group and len(group) > 1:
            gx, gy, gw, gh = group_bbox(group)
        else:
            gx, gy, gw, gh = region.x, region.y, region.w, region.h
        font_size, lines, tw, th = self._fit_wrapped(text, font_size, gw, gh)
        cx, cy = gx, gy
        cx, cy = self._clamp(cx, cy, tw, th)
        self.occupied.append((cx, cy, tw, th))
        return self._lines_to_placements(lines, cx, cy, font_size)

    def _place_beside(self, text, font_size, region, group):
        """Try to place text beside the original region. Returns placements or None."""
        if group and len(group) > 1:
            gx, gy, gw, gh = group_bbox(group)
        else:
            gx, gy, gw, gh = region.x, region.y, region.w, region.h

        target_w = max(gw, 60)
        target_w = min(target_w, self.image_width)

        font_size, lines, tw, th = self._fit_wrapped(
            text, font_size, target_w, self.image_height,
        )

        candidates = [
            (gx + gw + 4, gy),
            (gx, gy + gh + 4),
            (gx - tw - 4, gy),
            (gx, gy - th - 4),
        ]
        for cx, cy in candidates:
            if self._fits(cx, cy, tw, th):
                self.occupied.append((cx, cy, tw, th))
                return self._lines_to_placements(lines, cx, cy, font_size)

        return None, (candidates[0], tw, th, lines, font_size)

    def place_translation(self, region: TextRegion, overlay: str = "never",
                          group: list = None) -> list:
        """Place translation text, word-wrapped to fit the bubble dimensions.

        overlay: "never" (always beside), "always" (always on top),
                 "auto" (try beside first, fall back to overlay).
        Returns a list of (text, x, y, font_size) tuples — one per line.
        """
        text = region.translation
        font_size = max(12, min(region.h, 24))

        if overlay == "always" or overlay is True:
            return self._place_overlay(text, font_size, region, group)

        if overlay == "never" or overlay is False:
            result = self._place_beside(text, font_size, region, group)
            if isinstance(result, list):
                return result
            # No candidate fit — clamp the first candidate
            _, (fallback_pos, tw, th, lines, fs) = result
            cx, cy = fallback_pos
            cx, cy = self._clamp(cx, cy, tw, th)
            self.occupied.append((cx, cy, tw, th))
            return self._lines_to_placements(lines, cx, cy, fs)

        # "auto": try beside first, fall back to overlay
        result = self._place_beside(text, font_size, region, group)
        if isinstance(result, list):
            return result
        # Nothing fit beside — use overlay
        self.used_overlay = True
        return self._place_overlay(text, font_size, region, group)

    def _lines_to_placements(self, lines: list, x: int, y: int,
                             font_size: int) -> list:
        """Convert wrapped lines into placement tuples, clamping each line."""
        line_h = font_size + 4
        pad_x = 4
        pad_y = 4
        placements = []
        for i, line in enumerate(lines):
            lx = x + pad_x
            ly = y + pad_y + i * line_h
            lw = int(len(line) * font_size * 0.6) + 8
            lh = line_h
            lx, ly = self._clamp(lx, ly, lw, lh)
            placements.append((line, lx, ly, font_size))
        return placements

    def place_pinyin_per_char(self, region: TextRegion, overlay: str = "never") -> list:
        """Place pinyin above/beside each character based on text orientation.

        overlay: "never"/"auto" places beside, "always" places on top.
        Returns list of (pinyin_text, x, y, font_size) — one per character.
        """
        if not region.char_pinyin:
            return []

        use_overlay = overlay == "always" or overlay is True
        n = len(region.char_pinyin)
        placements = []

        if region.is_vertical:
            char_h = region.h / n
            font_size = max(8, min(int(char_h * 0.4), 14))

            for i, (char, py) in enumerate(region.char_pinyin):
                if use_overlay:
                    cx = region.x
                    cy = region.y + int(i * char_h)
                else:
                    cx = region.x + region.w + 3
                    cy = region.y + int(i * char_h + char_h * 0.3)
                cx, cy = self._clamp(cx, cy, int(len(py) * font_size * 0.6) + 4, font_size + 4)
                placements.append((py, cx, cy, font_size))
        else:
            char_w = region.w / n
            font_size = max(8, min(int(char_w * 0.45), 14))
            pinyin_h = font_size + 4

            for i, (char, py) in enumerate(region.char_pinyin):
                py_pixel_w = len(py) * font_size * 0.55

                if use_overlay:
                    cx = region.x + int(i * char_w + char_w / 2 - py_pixel_w / 2)
                    cy = region.y
                else:
                    cx = region.x + int(i * char_w + char_w / 2 - py_pixel_w / 2)
                    cy = region.y - pinyin_h - 1

                cx, cy = self._clamp(cx, cy, int(py_pixel_w) + 4, pinyin_h)
                placements.append((py, cx, cy, font_size))

        return placements

    def compute_placements(self, regions: list, mode: str = "translation",
                           overlay: str = "never") -> list:
        self.occupied = []
        self.used_overlay = False

        # For "never" and "auto", mark original regions as occupied
        if overlay != "always" and overlay is not True:
            for r in regions:
                self.occupied.append((r.x, r.y, r.w, r.h))

        groups_map = {}
        for r in regions:
            if r.group_id >= 0:
                groups_map.setdefault(r.group_id, []).append(r)

        placements = []
        for region in regions:
            if mode == "translation" and region.translation:
                group = groups_map.get(region.group_id)
                placements.extend(self.place_translation(
                    region, overlay=overlay, group=group,
                ))
            elif mode == "pinyin" and region.char_pinyin:
                placements.extend(self.place_pinyin_per_char(region, overlay=overlay))
        return placements
