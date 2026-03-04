# Testing Patterns

**Analysis Date:** 2026-03-04

## Test Framework

**Runner:**
- pytest 11.x (exact version not pinned in `requirements.txt`)
- Config: No `pytest.ini` or `pyproject.toml` config file detected
- Default pytest discovery: `tests/test_*.py` and `*_test.py` patterns

**Assertion Library:**
- Built-in `assert` statements (no `unittest` or custom assertion library)
- Simple boolean assertions: `assert len(regions) >= 1`, `assert r.x >= 0`

**Run Commands:**
```bash
pytest                 # Run all tests in tests/ directory
pytest tests/          # Run all tests explicitly
pytest tests/test_ocr_engine.py  # Run single test file
pytest -v              # Verbose output
pytest --tb=short      # Shorter traceback output
```

No test coverage configuration found (no `.coveragerc`, `coverage.xml`, or coverage targets).

## Test File Organization

**Location:**
- Co-located: Tests sit alongside source in `tests/` directory, parallel to `core/`, `models/`, `ui/`
- Pattern: One main test file per core module (e.g., `test_ocr_engine.py` for `core/ocr_engine.py`)

**Naming:**
- Test files: `test_<module>.py` (e.g., `test_ocr_engine.py`, `test_translator.py`, `test_phonetic_converter.py`)
- Test functions: `test_<scenario>` (e.g., `test_detect_finds_text()`, `test_translate_batch_single_group()`)
- Test classes: `Test<Feature>` (e.g., `TestChinesePinyinConverter`, `TestLanguageDetection`)

**Structure:**
```
tests/
├── conftest.py                      # Shared fixtures and setup
├── test_ocr_engine.py               # Unit tests for OCR
├── test_translator.py               # Unit tests for translation
├── test_phonetic_converter.py        # Unit tests for phonetic converters
├── test_pinyin_converter.py          # Unit tests for pinyin (backward compat)
├── test_text_grouper.py             # Unit tests for text grouping
├── test_text_placer.py              # Unit tests for text placement
├── test_text_region.py              # Unit tests for data model
├── test_image_renderer.py           # Unit tests for rendering
├── test_integration.py              # Full pipeline integration tests
├── diagnose_manga_ocr.py            # Diagnostic/exploratory tests
├── diagnose_japanese_ocr.py         # Diagnostic/exploratory tests
└── samples/                         # Test data/samples directory
```

## Test Structure

**Suite Organization:**
- Unit tests use function-based structure: individual `test_*()` functions
- Complex modules use class-based grouping: `TestChinesePinyinConverter`, `TestLanguageDetection` (see `test_phonetic_converter.py`)
- Class-based tests use `setup_method()` for per-test setup

**Example from codebase (test_phonetic_converter.py lines 17-25):**
```python
class TestChinesePinyinConverter:
    def setup_method(self):
        self.conv = ChinesePinyinConverter()

    def test_convert_basic(self):
        result = self.conv.convert("你好")
        assert "nǐ" in result
        assert "hǎo" in result
```

**Patterns:**

1. **Setup Pattern (module-level fixtures):**
   - Fixtures with `scope="module"` for expensive initialization (see `test_ocr_engine.py` lines 8-10)
   - Example: `ocr`, `translator`, `renderer` fixtures used across multiple tests
   ```python
   @pytest.fixture(scope="module")
   def ocr():
       return OcrEngine()
   ```

2. **Setup Pattern (class-level):**
   - `setup_method(self)` for class-based test groups initializing test subject (see `test_phonetic_converter.py` line 18)
   - Fixture per test instance, not shared across tests
   ```python
   def setup_method(self):
       self.conv = ChinesePinyinConverter()
   ```

3. **Teardown Pattern:**
   - Not observed in codebase (no stateful cleanup needed)
   - No `teardown_method()` implementations

4. **Assertion Pattern:**
   - Direct boolean assertions with context strings
   - Multiple assertions per test for related conditions
   ```python
   assert len(regions) >= 1                    # Must find text
   assert all(isinstance(r, TextRegion) for r in regions)  # Type check
   for r in regions:
       assert r.x >= 0                        # Bounds validation
       assert r.y >= 0
       assert r.w > 0
   ```

## Mocking

**Framework:** None detected

**Patterns:**
- No mocking library imported (no `unittest.mock`, `pytest-mock`, or similar)
- Tests use real implementations (integration-style unit tests)
- Example: `test_translate_basic()` actually calls GoogleTranslator via `Translator.translate()`
- Expensive operations (OCR models) are cached via pytest fixtures with `scope="module"`

**What to Mock:**
- Not applicable — mocking not used in this codebase
- If mocking were needed, would target external service calls (GoogleTranslator, PaddleOCR)

**What NOT to Mock:**
- Core business logic is tested with real implementations (OCR, translation, text grouping)
- Data structures (`TextRegion`) used as-is without mocking

## Fixtures and Factories

**Test Data:**
- Helper functions create test images on-the-fly using PIL
- Example from `test_integration.py` lines 32-45:
```python
def _get_font(size=36):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)
    except OSError:
        return ImageFont.load_default()

def _make_test_image():
    img = Image.new("RGB", (500, 200), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font()
    draw.text((30, 40), "你好世界", fill="black", font=font)
    draw.text((30, 110), "测试文本", fill="black", font=font)
    return img
```

- Helper functions for specific scenarios:
  - `_make_chinese_image()` - Single line of Chinese text
  - `_make_bubble_image()` - Two bubbles (grouped and ungrouped text)
  - `_make_punctuation_image()` - Text with punctuation marks

**Location:**
- Fixtures in `conftest.py` for cross-test reuse (module-scope fixtures)
- Helper functions (prefixed with `_`) defined within test files for single-file use
- No separate fixtures/factories directory

**Pattern (from test_integration.py):**
```python
@pytest.fixture(scope="module")
def ocr():
    return OcrEngine()

@pytest.fixture(scope="module")
def translator():
    return Translator()

# Helper functions for test data
def _make_test_image():
    # ... build test image ...
    return img

# Tests use both fixtures and helpers
def test_full_pipeline_translation(ocr, translator, renderer):
    img = _make_test_image()  # Helper for test data
    regions = ocr.detect(img)  # Fixture provides OCR
    # ... assertions ...
```

## Coverage

**Requirements:** Not enforced

**Current Status:**
- No coverage config file found (no `.coveragerc`, `coverage.ini`, or `pyproject.toml` coverage settings)
- No GitHub Actions or CI coverage reporting observed (no `.github/workflows`)
- No coverage badges or target percentages specified

**View Coverage:**
```bash
pytest --cov=core --cov=models --cov-report=html
# Would generate coverage report if coverage installed, but not configured
```

## Test Types

**Unit Tests:**
- **Scope:** Individual classes and functions (OCR detection, translation, text grouping)
- **Approach:** Direct testing with real implementations
- **Examples:**
  - `test_ocr_engine.py`: Tests for `OcrEngine.detect()` with synthetic images
  - `test_translator.py`: Tests for `Translator.translate()` and batch operations
  - `test_phonetic_converter.py`: Tests all converter classes (Chinese, Japanese, Korean)
  - `test_text_placer.py`: Tests `TextPlacer` placement algorithms

**Integration Tests:**
- **Scope:** Full pipeline end-to-end
- **Approach:** Real images → OCR → Translation → Text Placement → Rendering
- **Files:** `tests/test_integration.py` contains pipeline tests
- **Examples:**
  - `test_full_pipeline_translation()` - Complete workflow with overlay modes
  - `test_grouped_translation()` - Text grouping within pipeline
  - `test_pipeline_with_mixed_content()` - Multiple transformations on same regions

**E2E Tests:**
- **Status:** Not present
- **Why:** GUI testing skipped (difficult with PyQt5 without external framework)
- **Diagnostic tests available:** `tests/diagnose_*.py` for manual exploration

## Common Patterns

**Async Testing:**
- Not applicable (no async code in codebase)
- PyQt5 threading uses `QThread`, not `async/await`

**Error Testing:**
- Guard clause testing: `test_convert_empty()` patterns test empty input handling
- Return-empty-string pattern for errors (see phonetic converters returning `""` for invalid input)
- Example from `test_translator.py` line 18-20:
```python
def test_translate_empty(translator):
    result = translator.translate("")
    assert result == ""
```

**Boundary Testing:**
- Edge cases for image bounds (see `test_integration.py` lines 186-204)
- Vertical vs horizontal text detection (see `test_phonetic_converter.py` lines 102-109)
- Grouped vs ungrouped regions (see `test_translator.py` lines 23-48)

**Example of boundary test:**
```python
def test_edge_text_stays_in_bounds(ocr, translator, renderer):
    """Text near the image edge should have annotations clamped inside."""
    img = Image.new("RGB", (200, 80), "white")
    draw = ImageDraw.Draw(img)
    font = _get_font(28)
    draw.text((120, 25), "你好", fill="black", font=font)
    regions = ocr.detect(img)
    if not regions:
        return

    translator.translate_batch(regions)
    placer = TextPlacer(img.width, img.height)
    placements = placer.compute_placements(regions, "translation")

    for text, x, y, font_size in placements:
        assert x >= 0
        assert y >= 0
        tw, th = placer._estimate_text_size(text, font_size)
        assert x + tw <= img.width
```

**Test Isolation:**
- Module-scope fixtures reused across tests (performance optimization for expensive models)
- Each test function is independent (no shared state except fixtures)
- Helper functions create fresh test data per invocation

---

*Testing analysis: 2026-03-04*
