# Architecture

**Analysis Date:** 2026-03-04

## Pattern Overview

**Overall:** Event-driven Desktop Application with Multi-Stage Processing Pipeline

**Key Characteristics:**
- Multi-threaded PyQt5 desktop application with async model loading
- Modular processing pipeline: Text Detection → Translation/Annotation → Text Placement → Rendering
- Language-agnostic text extraction with multi-language support (Chinese, Japanese, Korean)
- Graphics rendering with smart text positioning and fallback strategies
- Layered separation: UI controllers, core processing, data models, and rendering

## Layers

**UI Layer (Presentation):**
- Purpose: User interaction and visualization of results
- Location: `ui/`
- Contains: Main window controller, region selection overlay, result display overlay, theme definitions
- Depends on: Core processing modules, model objects
- Used by: Application entry point
- Key files: `ui/main_window.py` (orchestrates pipeline), `ui/region_selector.py`, `ui/result_overlay.py`

**Core Processing Layer (Business Logic):**
- Purpose: Text extraction, translation, annotation, and placement calculations
- Location: `core/`
- Contains: OCR engine, translator, phonetic converters, text grouping logic, text placement algorithm, image rendering
- Depends on: Model objects, external libraries (PaddleOCR, MangaOCR, deep_translator, pykakasi, etc.)
- Used by: UI controllers, each other
- Key modules:
  - `core/ocr_engine.py`: Detects text regions using PaddleOCR with fallback to MangaOCR for Japanese
  - `core/translator.py`: Translates grouped text using Google Translate API
  - `core/phonetic_converter.py`: Converts text to phonetic annotations (pinyin, furigana, romaji, romanization)
  - `core/text_grouper.py`: Clusters nearby regions into speech bubble groups using union-find
  - `core/text_placer.py`: Calculates optimal text placement with wrapping and collision detection
  - `core/image_renderer.py`: Renders text overlays with font handling and caching

**Model Layer (Data):**
- Purpose: Define core data structures passed through pipeline
- Location: `models/`
- Contains: `TextRegion` dataclass with geometry, text, translations, and phonetic annotations
- Depends on: None (pure data)
- Used by: All processing layers
- Key file: `models/text_region.py`

## Data Flow

**Main Pipeline (User Interaction → Rendered Result):**

1. User captures screen region via `RegionSelector` (fullscreen overlay)
2. `MainWindow._run_pipeline()` spawns `PipelineWorker` on separate thread
3. Worker determines OCR language:
   - If "Auto-detect": Try Chinese OCR first, detect language, re-OCR if needed
   - Confidence-based fallback: If Chinese OCR confidence < 0.7 and Japanese available, retry with Japanese
4. `OcrEngine.detect()` returns list of `TextRegion` objects with:
   - Bounding box (x, y, w, h), text, confidence, polygon coordinates
   - For Japanese: Re-recognized via MangaOCR on original (non-preprocessed) image
5. Based on mode:
   - **Translation mode**: `Translator.translate_batch()` groups regions by speech bubble, translates groups together
   - **Phonetic mode**: Selected converter (Chinese/Japanese/Korean) converts per-character
6. `TextPlacer.compute_placements()` determines where to place text:
   - Tries placement beside original region first (for "never"/"auto" modes)
   - Falls back to overlay on top if no space beside
   - Always overlay for "always" mode
   - Handles word-wrapping to fit available space
   - Tracks occupied regions to prevent overlaps
7. `ImageRenderer.render()` creates final result image:
   - Optionally white-out original text regions (overlay mode)
   - Draw translated/annotated text with semi-transparent backgrounds
   - Font selection from system (CJK-aware fonts preferred)
8. Result displayed in `ResultOverlay` fullscreen window

**State Management:**

- **Per-Pipeline**: `PipelineWorker` holds image, regions, placements during processing
- **Per-Session**: `MainWindow` maintains references to OCR engine, translator, converters, renderer (reused across pipelines)
- **Per-Region**: `TextRegion` accumulates state through pipeline: text → translation/pinyin → group_id → placed at (x,y)
- Signals coordinate threading: `QThread`, `pyqtSignal` for cross-thread communication

## Key Abstractions

**TextRegion:**
- Purpose: Unified representation of detected text with geometry and all annotations
- Examples: `models/text_region.py`
- Pattern: Dataclass with optional fields populated at each pipeline stage
- Fields: x, y, w, h (position), text (raw OCR), translation, pinyin (full), char_pinyin (per-char list), group_id, polygon, confidence

**PhoneticConverter (Abstract Base Class):**
- Purpose: Pluggable converters for different language phonetic systems
- Examples: `ChinesePinyinConverter`, `JapaneseFuriganaConverter`, `JapaneseRomajiConverter`, `KoreanRomanizer`
- Pattern: Abstract methods `convert(text)` and `convert_per_char(text)`, shared `convert_batch(regions)` template
- Responsibility: Transform characters to annotations while preserving text-annotation pairing

**Text Grouping (Union-Find):**
- Purpose: Cluster detected text regions belonging to same speech bubble for batch translation
- File: `core/text_grouper.py`
- Pattern: Single-linkage clustering with adaptive threshold based on text height and alignment checks
- Used by: Translator to group text before API call, TextPlacer to compute group bounding boxes, ImageRenderer to white-out groups

**Text Placement Strategy (Greedy with Fallback):**
- Purpose: Find non-overlapping position for text with user-configurable collision handling
- File: `core/text_placer.py`
- Pattern: Try beside (4 candidates), then clamp fallback, or overlay on top
- Supports: Word-wrapping, dynamic font sizing, per-character pinyin placement (above/beside based on text orientation)

**Language Detection (Heuristic):**
- Purpose: Auto-detect language from character frequency when user selects "Auto-detect"
- File: `core/phonetic_converter.py`, function `detect_language()`
- Pattern: Check % of hiragana/katakana → Japanese, % of hangul → Korean, else Chinese
- Used by: MainWindow worker to select OCR model and converter

## Entry Points

**Application Start:**
- Location: `main.py`
- Triggers: User runs `python main.py`
- Responsibilities:
  - Create QApplication
  - Show splash screen with status updates
  - Load models on separate thread (OCR, translator, converters)
  - Instantiate and show MainWindow with loaded models

**User Interaction Flow:**
- Location: `ui/main_window.py`, method `_start_capture()`
- Triggers: User clicks "Capture Region" button
- Responsibilities: Hide main window, show fullscreen region selector

**Pipeline Execution:**
- Location: `ui/main_window.py`, method `_run_pipeline()` → `PipelineWorker.run()`
- Triggers: User selects region and releases mouse
- Responsibilities: Execute all stages of processing on background thread

## Error Handling

**Strategy:** Try-catch at pipeline worker level with user-facing error messages

**Patterns:**
- OCR failures: Empty region list caught in worker, error message "No text detected"
- Translation API failures: Exception from `GoogleTranslator.translate()` caught in worker, displayed to user
- Missing fonts: `ImageRenderer` falls back to `ImageFont.load_default()` if no CJK font found
- Invalid regions: Clamping logic in `TextPlacer._clamp()` ensures placements stay in-bounds even if calculation overflows
- Grouped region failures: If first region in group has empty translation, it's skipped by placer

**Logging Pattern:** No structured logging; exceptions logged to stderr via exception emit and message box

## Cross-Cutting Concerns

**Logging:** None — exceptions use signal emit to UI, debug output to console via print/exception handler

**Validation:**
- TextRegion confidence field for OCR reliability assessment
- Text wrapping validates max_chars > 1 to prevent infinite loops
- Region placement validates bounding box clamping before draw

**Authentication:** None — Google Translate API uses public endpoint (no key required, rate-limited)

**Threading:**
- QThread for model loading at startup (ModelLoader)
- QThread for each pipeline execution (PipelineWorker)
- Signals prevent blocking UI during OCR, translation, rendering

**Language Switching:**
- Translator supports runtime language switch via `set_source_lang()`
- Converters selected based on (language, mode) tuple from UI dropdowns
- OCR engine lazy-loads models per language on first detect call

---

*Architecture analysis: 2026-03-04*
