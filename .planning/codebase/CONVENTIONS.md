# Coding Conventions

**Analysis Date:** 2026-03-04

## Naming Patterns

**Files:**
- Modules: `snake_case.py` (e.g., `ocr_engine.py`, `text_grouper.py`, `pinyin_converter.py`)
- Test files: `test_<module_name>.py` (e.g., `test_ocr_engine.py`, `test_translator.py`)
- Diagnostic files: `diagnose_<purpose>.py` (e.g., `diagnose_manga_ocr.py`)

**Classes:**
- PascalCase (e.g., `OcrEngine`, `TextRegion`, `ChinesePinyinConverter`, `ImageRenderer`)
- Private/internal classes prefixed with underscore: `_MangaOcrRecognizer`, `_TextPlacer`
- Base/abstract classes also PascalCase: `PhoneticConverter` (ABC)

**Functions and Methods:**
- snake_case (e.g., `detect()`, `translate_batch()`, `convert_per_char()`, `place_translation()`)
- Private/internal methods prefixed with underscore: `_preprocess()`, `_get_engine()`, `_wrap_text()`, `_clamp()`
- Helper functions also snake_case: `_gap()`, `_merge_threshold()`, `group_regions()`, `detect_language()`

**Variables:**
- snake_case for local variables and instance attributes (e.g., `image`, `regions`, `group_id`, `char_pinyin`)
- UPPER_CASE for module-level constants (e.g., `LANG_MAP`, `SOURCE_LANG_MAP`, `FONT_CANDIDATES`, `MODE_KEY_MAP`)
- Single underscore prefix for "private" module-level variables: `_FONT_CANDIDATES`, `_MangaOcrRecognizer`

**Type/Data Structure Names:**
- Use dataclasses for data containers (e.g., `TextRegion` at `models/text_region.py`)
- Fields within dataclasses use snake_case with type hints: `x: int`, `y: int`, `w: int`, `h: int`, `text: str`

## Code Style

**Formatting:**
- No explicit formatter configured (not detected in `.pre-commit` or `tox.ini`)
- Import order and style follows implicit PEP 8 conventions
- No `.eslintrc` or `.prettier` config for Python code

**Linting:**
- No explicit linter configuration detected
- No type checking configuration (mypy/pyright config absent)

**Line Length:**
- Lines appear to follow ~80-100 character soft limit based on code samples
- Docstrings and long lines may exceed this when necessary

**Whitespace:**
- 4-space indentation (Python standard)
- Blank lines between method definitions
- Two blank lines between class definitions

## Import Organization

**Order (strict):**
1. Standard library imports (e.g., `import sys`, `import os`, `from abc import ABC`)
2. Third-party imports (e.g., `import numpy as np`, `from PIL import Image`, `from PyQt5.QtWidgets import`)
3. Local application imports (e.g., `from models.text_region import TextRegion`, `from core.translator import Translator`)

**Patterns:**
- Imports grouped by category with blank lines between groups
- Specific imports from modules preferred over `import *` (always explicit)
- No star imports found in codebase (e.g., `from X import Y` not `from X import *`)
- PyQt5 imports often multi-line for readability (see `ui/main_window.py` lines 3-6)

**Path Aliases:**
- No aliases configured (no `tsconfig` or `pyproject.toml` with path mappings)
- Relative imports use absolute package paths: `from core.ocr_engine import OcrEngine` not `from .ocr_engine`
- Project root must be on `sys.path` (managed in `tests/conftest.py` lines 4-5)

## Error Handling

**Patterns:**
- Try-catch with specific exception handling (see `core/ocr_engine.py` lines 22-25)
- Generic Exception catches for compatibility (see `main.py` lines 40-41)
- Guard clauses for None/empty checks before operations (e.g., `if not text.strip(): return ""`)
- Return empty strings/empty lists for error cases rather than raising (e.g., `core/phonetic_converter.py` lines 93-95)
- Optional return values (None for "no result") used sparingly

**Example pattern from codebase:**
```python
# Guard clause for empty input
def convert(self, text: str) -> str:
    if not text:
        return ""
    return self._romanizer_cls(text).romanize()

# Try-except for external dependencies
try:
    font = ImageFont.truetype(font_path, size)
except OSError:
    font = ImageFont.load_default()
```

## Logging

**Framework:** `print()` or PyQt5 signals (no logger framework detected)

**Patterns:**
- PyQt5 applications use `pyqtSignal()` for status/error messages (see `main.py` lines 11-13)
- Status signals carry operational information: `self.status.emit("Loading OCR engine...")`
- Error signals carry exception details: `self.error.emit(str(e))`
- No persistent logging to files observed
- Console output through event signals in GUI context

**Example from codebase:**
```python
class ModelLoader(QObject):
    finished = pyqtSignal(object, object, object)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.status.emit("Loading OCR engine...")
            # ... operations ...
        except Exception as e:
            self.error.emit(str(e))
```

## Comments

**When to Comment:**
- Module docstrings explain purpose (e.g., `"""Phonetic annotation converters for Chinese, Japanese, and Korean text."""`)
- Function/method docstrings describe purpose, args, and return values
- Inline comments explain non-obvious logic (e.g., `# Lazy-loaded manga-ocr wrapper`)
- Complex algorithms documented with docstrings (e.g., `group_regions()` explains union-find clustering)

**JSDoc/TSDoc:**
- Not applicable (Python project, not TypeScript)
- Docstrings use triple-quote format with description and optional Args/Returns sections
- Example from `core/ocr_engine.py` lines 27-33:
```python
def recognize(self, image: Image.Image, bbox: tuple) -> str:
    """Crop a region from the PIL image and recognize with manga-ocr.

    Args:
        image: Original (non-preprocessed) PIL image.
        bbox: (x, y, w, h) bounding box of the text region.
    """
```

## Function Design

**Size:**
- Functions typically 15-50 lines
- Larger methods (100+ lines) in stateful classes like `TextPlacer` justified by complexity
- Private helper methods keep public methods concise

**Parameters:**
- Maximum 5-6 parameters per function (exceeds rarely)
- Optional parameters with defaults: `def detect(self, image: Image.Image, lang: str = "chinese")`
- Type hints present in signatures: `def translate(self, text: str) -> str`

**Return Values:**
- Explicit return types in signatures
- Early returns for guard clauses (see `translate()` pattern)
- Batch operations return the same list instance (mutation pattern, see `convert_batch()` in phonetic converters)
- Complex returns use tuples for multiple values: `(x, y, w, h)` for bounding boxes

**Example pattern:**
```python
def place_translation(self, region: TextRegion, overlay: str = "never",
                      group: list = None) -> list:
    """Place translation text with wrapping.

    overlay: "never" (always beside), "always" (always on top),
             "auto" (try beside first, fall back to overlay).
    Returns a list of (text, x, y, font_size) tuples — one per line.
    """
    text = region.translation
    font_size = max(12, min(region.h, 24))

    if overlay == "always" or overlay is True:
        return self._place_overlay(text, font_size, region, group)
    # ... more logic
```

## Module Design

**Exports:**
- Classes and public functions exported directly from modules
- Private utilities prefixed with underscore: `_is_chinese_char()`, `_gap()`, `_find_system_font()`
- No `__all__` declarations observed (all public names implicitly exported)

**Barrel Files:**
- Core modules have `__init__.py` but remain empty (no re-exports)
- `models/__init__.py` and `core/__init__.py` are empty
- Imports use full module paths: `from core.ocr_engine import OcrEngine` not `from core import OcrEngine`

**Dataclass Pattern:**
- `TextRegion` in `models/text_region.py` uses `@dataclass` decorator with `field(default_factory=list)` for mutable defaults
- Properties used for computed values: `is_vertical` property in `TextRegion` (lines 21-29)
- No separate getters/setters, direct attribute access is standard

**Example module pattern:**
```python
# core/translator.py
from deep_translator import GoogleTranslator
from models.text_region import TextRegion
from core.text_grouper import group_regions, group_text, group_bbox

SOURCE_LANG_MAP = { ... }  # Module constant

class Translator:
    def __init__(self, source_lang: str = "chinese"):
        # ...

    def translate(self, text: str) -> str:
        # ...
```

---

*Convention analysis: 2026-03-04*
