from deep_translator import GoogleTranslator

from models.text_region import TextRegion
from core.text_grouper import group_regions, group_text, group_bbox

# Map user-facing language names to GoogleTranslator source codes
SOURCE_LANG_MAP = {
    "chinese": "zh-CN",
    "japanese": "ja",
    "korean": "ko",
}


class Translator:
    def __init__(self, source_lang: str = "chinese"):
        self._source_lang = source_lang
        self._translator = GoogleTranslator(
            source=SOURCE_LANG_MAP.get(source_lang, "zh-CN"),
            target="en",
        )

    def set_source_lang(self, lang: str):
        """Switch the source language at runtime."""
        if lang != self._source_lang:
            self._source_lang = lang
            self._translator = GoogleTranslator(
                source=SOURCE_LANG_MAP.get(lang, "zh-CN"),
                target="en",
            )

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._translator.translate(text)

    def translate_batch(self, regions: list) -> list:
        """Translate regions grouped by speech bubble.

        Groups nearby regions, translates each group as a whole,
        and assigns the full translation to the first region in the
        group (the others get an empty translation so they don't
        produce duplicate placements).
        """
        groups = group_regions(regions)

        for gid, group in enumerate(groups):
            full_text = group_text(group)
            full_translation = self.translate(full_text)

            for i, region in enumerate(group):
                region.group_id = gid
                if i == 0:
                    # First region carries the group translation
                    region.translation = full_translation
                else:
                    # Other regions in same group: mark as grouped
                    # so the placer can skip them
                    region.translation = ""

        return regions
