# Codebase Structure

**Analysis Date:** 2026-03-04

## Directory Layout

```
Manga-Buddy/
├── core/                   # Processing pipeline (OCR, translation, rendering)
│   ├── __init__.py
│   ├── ocr_engine.py       # Text detection using PaddleOCR + MangaOCR
│   ├── translator.py       # Google Translate API wrapper with grouping
│   ├── phonetic_converter.py  # Multi-language phonetic converters (pinyin, furigana, romaji, romanization)
│   ├── pinyin_converter.py # DEPRECATED - functionality moved to phonetic_converter.py
│   ├── text_grouper.py     # Group text regions by speech bubble (union-find clustering)
│   ├── text_placer.py      # Calculate text placement with collision detection and word-wrapping
│   └── image_renderer.py   # Render text overlays on images with font caching
├── models/                 # Data structures
│   ├── __init__.py
│   └── text_region.py      # TextRegion dataclass - core data structure for detected text
├── ui/                     # PyQt5 user interface
│   ├── __init__.py
│   ├── main_window.py      # Main application window and pipeline orchestrator
│   ├── region_selector.py  # Fullscreen overlay for region selection
│   ├── result_overlay.py   # Fullscreen overlay to display processed result
│   └── theme.py            # Dark theme stylesheet definitions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_ocr_engine.py
│   ├── test_translator.py
│   ├── test_text_grouper.py
│   ├── test_text_placer.py
│   ├── test_text_region.py
│   ├── test_image_renderer.py
│   ├── test_phonetic_converter.py
│   ├── test_pinyin_converter.py
│   ├── diagnose_manga_ocr.py     # Diagnostic script for manga-ocr testing
│   ├── diagnose_japanese_ocr.py  # Diagnostic script for Japanese OCR comparison
│   ├── test_integration.py       # End-to-end pipeline tests
│   └── samples/                  # Test images and expected outputs
├── main.py                 # Application entry point with model loading
├── requirements.txt        # Python dependencies
└── .planning/              # GSD codebase documentation
    └── codebase/           # Generated analysis documents
```

## Directory Purposes

**core/:**
- Purpose: Text processing pipeline - extract, translate, annotate, place, and render text
- Contains: Pure business logic modules, no UI dependencies
- Key files:
  - `ocr_engine.py`: Detects text regions from images
  - `translator.py`: Translates grouped text
  - `phonetic_converter.py`: Converts text to phonetic annotations
  - `text_placer.py`: Calculates optimal text placement
  - `image_renderer.py`: Renders final result image with overlays

**models/:**
- Purpose: Shared data structures used throughout pipeline
- Contains: Dataclasses and enums
- Key files: `text_region.py` - primary data structure passed through all processing stages

**ui/:**
- Purpose: PyQt5 GUI components and window management
- Contains: Window classes, overlays, theme definitions
- Key files:
  - `main_window.py`: Main application window with settings and pipeline orchestration
  - `region_selector.py`: Fullscreen selection overlay
  - `result_overlay.py`: Fullscreen result display

**tests/:**
- Purpose: Unit, integration, and diagnostic tests
- Contains: Test cases, fixtures, test data
- Key files:
  - `test_*.py`: Unit tests for each core module
  - `test_integration.py`: End-to-end pipeline tests
  - `conftest.py`: Shared pytest fixtures and configuration
  - `diagnose_*.py`: Manual diagnostic scripts for OCR engine behavior

## Key File Locations

**Entry Points:**
- `main.py`: Application startup; creates QApplication, shows splash, loads models, creates MainWindow

**Configuration:**
- `ui/theme.py`: Dark theme stylesheet (colors, fonts, borders, effects)

**Core Logic:**
- `core/ocr_engine.py`: Text detection (PaddleOCR + MangaOCR)
- `core/translator.py`: Translation with speech bubble grouping
- `core/phonetic_converter.py`: Phonetic conversion (pinyin, furigana, romaji, romanization)
- `core/text_grouper.py`: Clustering algorithm for speech bubbles
- `core/text_placer.py`: Text placement with collision detection
- `core/image_renderer.py`: Image rendering with font caching

**Data Models:**
- `models/text_region.py`: TextRegion dataclass

**UI Controllers:**
- `ui/main_window.py`: Main window with settings, capture button, pipeline orchestration
- `ui/region_selector.py`: Region selection UI (fullscreen overlay)
- `ui/result_overlay.py`: Result display UI (fullscreen overlay)

**Testing:**
- `tests/conftest.py`: Pytest configuration and fixtures
- `tests/test_integration.py`: End-to-end pipeline tests

## Naming Conventions

**Files:**
- Module files: lowercase with underscores (e.g., `text_placer.py`, `ocr_engine.py`)
- Test files: `test_<module_name>.py` (e.g., `test_text_placer.py`)
- Classes: PascalCase (e.g., `OcrEngine`, `TextPlacer`, `TextRegion`)

**Functions:**
- Public functions: lowercase with underscores (e.g., `group_regions()`, `detect_language()`)
- Private functions: leading underscore (e.g., `_gap()`, `_merge_threshold()`, `_get_engine()`)

**Variables:**
- Instance variables: lowercase with underscores (e.g., `self._engines`, `self._font_cache`)
- Constants: UPPERCASE (e.g., `LANG_MAP`, `LANG_MODES`)
- Regional/positional: x, y, w, h for coordinates; gx, gy, gw, gh for group geometry

**Types:**
- TextRegion uses geometry fields x, y, w, h (not x1, y1, x2, y2)
- Placements tuples: (text, x, y, font_size)
- Groups: list of TextRegion objects

## Where to Add New Code

**New Feature (Translation Mode, Phonetic Type):**
- Primary code: `core/` module for processing logic
- UI updates: Add new combobox item in `ui/main_window.py` and update `LANG_MODES`/`CONVERTER_KEY_MAP` dicts
- Tests: Add test in `tests/test_<module>.py`

**New Converter Language:**
- Implementation: `core/phonetic_converter.py` - subclass `PhoneticConverter`
- Registration: Add instance to converters dict in `main.py` ModelLoader
- UI: Add (language, mode) mapping to `CONVERTER_KEY_MAP` in `ui/main_window.py`
- Testing: Add test case in `tests/test_phonetic_converter.py`

**New UI Component:**
- Implementation: `ui/<component_name>.py`
- Integration: Import and instantiate in `ui/main_window.py`
- Styling: Add rules to `ui/theme.py` with consistent color/font scheme

**Utilities / Helpers:**
- Shared helpers in calling module's file (e.g., `_find_system_font()` in `image_renderer.py`)
- Reusable across modules: Create in `core/` as new module (e.g., `core/geometry_utils.py`)

**Test Data:**
- Images: `tests/samples/` directory
- Fixtures: Define in `tests/conftest.py` using @pytest.fixture

## Special Directories

**tests/samples/:**
- Purpose: Test image files and expected outputs
- Generated: No (committed to repo)
- Committed: Yes (for test reproducibility)
- Structure: Images grouped by language/scenario (e.g., chinese_horizontal.png, japanese_vertical.png)

**.pytest_cache/:**
- Purpose: Pytest caching for test discovery and performance
- Generated: Yes (auto-created by pytest)
- Committed: No (.gitignore)

**.git/:**
- Purpose: Git version control metadata
- Generated: Yes (git init)
- Committed: Yes (core repo data)

**.planning/codebase/:**
- Purpose: Generated GSD codebase analysis documents
- Generated: Yes (by gsd:map-codebase)
- Committed: Yes (reference for future phases)

---

*Structure analysis: 2026-03-04*
