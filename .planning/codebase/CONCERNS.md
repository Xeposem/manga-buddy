# Codebase Concerns

**Analysis Date:** 2026-03-04

## Tech Debt

**Dual OCR Pipeline for Japanese:**
- Issue: When language is auto-detected as Chinese, but confidence is low (<0.7), a second Japanese OCR is triggered and result comparison occurs. This adds complexity and processing overhead.
- Files: `core/ocr_engine.py` (lines 78-102), `ui/main_window.py` (lines 85-102)
- Impact: Higher latency on ambiguous Japanese text; unnecessary dual-pass OCR may consume extra memory and computational resources.
- Fix approach: Implement more sophisticated language detection that distinguishes kana from hanzi in the first pass, or use a multi-model ensemble approach with confidence scoring rather than sequential fallback.

**Unbounded Font Cache:**
- Issue: `ImageRenderer._font_cache` accumulates font objects for every requested size with no eviction policy.
- Files: `core/image_renderer.py` (lines 40, 44-49)
- Impact: Long-running sessions with varied font sizes may accumulate memory. No limit on cache growth.
- Fix approach: Implement LRU cache with size limit (e.g., `functools.lru_cache(maxsize=32)`) or track cache size and evict oldest entries.

**Shallow Error Handling:**
- Issue: Most production code has zero exception handling. Only entry points (`main.py`, `ui/main_window.py`) catch generic `Exception`.
- Files: `core/translator.py`, `core/text_placer.py`, `core/text_grouper.py`, `core/phonetic_converter.py`
- Impact: Network failures in translation, OCR errors, or phonetic conversion failures crash the pipeline with generic error messages.
- Fix approach: Add specific exception types and handlers for each module:
  - `TranslationError` for API timeouts, network issues, rate limiting
  - `OcrError` for model loading, inference failures
  - `ConverterError` for phonetic annotation failures

**No Timeout Configuration:**
- Issue: `deep_translator.GoogleTranslator` calls have no timeout specified. Translation requests can hang indefinitely on network issues.
- Files: `core/translator.py` (lines 17-29, 34)
- Impact: UI can freeze if Google Translate API is slow or network is unstable. No recovery mechanism.
- Fix approach: Add timeout parameter to GoogleTranslator initialization and wrap calls in retry logic with exponential backoff.

**Hard-coded Paths and Platform Assumptions:**
- Issue: Font paths are hard-coded for Windows (`C:/Windows/Fonts/`), macOS (`/System/Library/Fonts/`), and Linux (`/usr/share/fonts/`).
- Files: `core/image_renderer.py` (lines 13-27)
- Impact: May fail silently if font paths don't exist (falls back to default font). Non-standard installations or custom font locations will not be used.
- Fix approach: Add font search in standard locations, allow user-configurable font path via environment variable or config file.

**Global Model Caching without Cleanup:**
- Issue: PaddleOCR instances are cached per language in `OcrEngine._engines` dict with no cleanup. MangaOCR is lazy-loaded but never unloaded.
- Files: `core/ocr_engine.py` (lines 45-65)
- Impact: Models consume significant memory (paddle/transformers models are typically 500MB+). No way to clear cache in long-running sessions.
- Fix approach: Implement explicit cleanup method or use weak references with automatic garbage collection.

## Known Bugs

**Language Auto-detection Ambiguity:**
- Symptoms: Japanese text with high kanji content may be misclassified as Chinese; Korean text with low hangul ratio may not trigger Korean OCR.
- Files: `core/phonetic_converter.py` (lines 222-253)
- Trigger: Auto-detect mode with mixed-script text or edge-case character distributions (e.g., mostly kanji with few hiragana).
- Workaround: Users can manually select "Japanese" or "Korean" language mode to force correct OCR model.

**Character-to-Pinyin Alignment Fragility:**
- Symptoms: When Chinese text contains punctuation, spaces, or non-CJK characters, `char_pinyin` list length may not match text length exactly.
- Files: `core/phonetic_converter.py` (lines 54-83)
- Trigger: Text regions with mixed punctuation, Arabic numerals, or Latin characters mixed with Chinese.
- Workaround: Verified in `test_integration.py::test_pinyin_with_punctuation`, but edge cases with multiple consecutive punctuation may still break.

**Thread Resource Leak on Rapid Captures:**
- Symptoms: If user clicks "Capture Region" multiple times before previous pipeline completes, multiple QThread objects accumulate without proper cleanup.
- Files: `ui/main_window.py` (lines 354-367)
- Trigger: Clicking "Capture Region" button while a previous pipeline is still running.
- Workaround: Disable capture button during processing (implemented in `_set_status`), but if user rapidly clicks before button is disabled, multiple threads spawn.

## Security Considerations

**Unvalidated Network Requests:**
- Risk: `deep_translator.GoogleTranslator` makes unauthenticated HTTPS requests to Google's API without certificate verification options exposed.
- Files: `core/translator.py` (lines 1, 17-29)
- Current mitigation: HTTPS encrypts data in transit; Google Translate API is public and free to use.
- Recommendations:
  - Document privacy implications (translations are sent to Google servers)
  - Consider adding proxy support for corporate environments
  - Add optional certificate pinning for high-security deployments

**OCR Model Download Security:**
- Risk: PaddleOCR and manga-ocr download pre-trained models from the internet on first use. Models are not cryptographically verified.
- Files: `core/ocr_engine.py` (lines 52-59, 61-65)
- Current mitigation: Models are downloaded from official repositories; models are executed in the same process (no sandboxing).
- Recommendations:
  - Verify model checksums after download
  - Document which URLs are used for model distribution
  - Consider air-gapped deployment path for offline environments

**No Input Validation on OCR Results:**
- Risk: OCR output directly populates TextRegion objects and is used in rendering without validation. Malicious OCR results could cause rendering issues or crashes.
- Files: `core/ocr_engine.py` (lines 82-100)
- Current mitigation: OCR models are from trusted sources; polygon coordinates are clamped in rendering.
- Recommendations:
  - Validate bounding box coordinates are within image bounds
  - Add bounds checks on polygon points before storing

## Performance Bottlenecks

**Sequential Double-Pass OCR on Language Detection:**
- Problem: For Japanese text with low confidence, a full second OCR pass is executed.
- Files: `ui/main_window.py` (lines 85-102)
- Cause: Confidence-based fallback mechanism requires two complete inference passes.
- Improvement path:
  - Pre-run a fast language classifier (e.g., `langdetect` or character analysis) before OCR
  - Cache results to avoid re-OCR on subsequent operations with same image
  - Implement early-stopping in dual-pass logic to skip second pass if first is confident enough

**Manga-OCR Lazy Loading on Every Japanese Region:**
- Problem: First Japanese region triggers import and initialization of manga-ocr model, causing UI freeze.
- Files: `core/ocr_engine.py` (lines 101-108)
- Cause: Lazy loading defers expensive initialization until first use.
- Improvement path:
  - Pre-load manga-ocr during startup (or on-demand in background thread)
  - Cache the `_MangaOcrRecognizer` instance permanently instead of creating per-language
  - Show progress indicator during model loading

**Text Placement Brute-Force Search:**
- Problem: `TextPlacer` tries up to 4 candidate positions sequentially (right, below, left, above) without spatial indexing.
- Files: `core/text_placer.py` (lines 101-126)
- Cause: For large images with hundreds of regions, O(n²) overlap checking occurs per placement.
- Improvement path:
  - Implement spatial hash or quad-tree for fast collision detection
  - Batch placement computation to reduce redundant checks
  - Cache occupied regions in sorted intervals

**Translation Batch Processing Without Caching:**
- Problem: Each `translate_batch()` call re-initializes GoogleTranslator, even for same source/target language pair.
- Files: `core/translator.py` (lines 15-29)
- Cause: Language switching recreates translator instance unnecessarily.
- Improvement path:
  - Cache GoogleTranslator instances per language pair
  - Implement memo-ization of translation results to avoid re-translating identical strings
  - Add disk cache for frequently-translated phrases

## Fragile Areas

**Phonetic Converter Character Alignment:**
- Files: `core/phonetic_converter.py` (lines 54-83, 99-129, 145-168, 183-194)
- Why fragile: All converters perform index-based character matching with fallback logic. Differences in how pypinyin, pykakasi, and korean_romanizer tokenize input can cause misalignments.
- Safe modification:
  - Add comprehensive unit tests for each character type and mixed-case inputs
  - Use deterministic tokenization (e.g., explicitly specify how to handle multi-codepoint characters)
  - Return both character and annotation with explicit indices rather than positional inference
- Test coverage: `test_pinyin_converter.py` covers basic cases but lacks edge cases with combining characters, emoji, RTL text.

**Language Detection Heuristic:**
- Files: `core/phonetic_converter.py` (lines 222-253)
- Why fragile: Simple threshold-based detection (jp_chars/total > 0.1, kr_chars/total > 0.3) fails with:
  - Mixed-language text
  - Text with many numbers or symbols (skipped in counting)
  - Rare scripts or non-standard character ranges
- Safe modification:
  - Extend to check for consecutive kana sequences (unlikely in Chinese/Korean)
  - Use Unicode block ranges more precisely
  - Fall back to heuristics from more sophisticated libraries (e.g., `textblob`, `langdetect`)
- Test coverage: `test_phonetic_converter.py` lacks mixed-language test cases.

**Text Grouping Algorithm:**
- Files: `core/text_grouper.py` (lines 25-88)
- Why fragile: Single-linkage clustering with adaptive threshold is sensitive to:
  - Text with varying font sizes (adaptive threshold = avg_h * 1.8)
  - Rotated or skewed text (polygon not fully considered)
  - Images with multiple columns or non-linear text flow
- Safe modification:
  - Validate threshold computation with multiple image scales
  - Add option to use alternative clustering (e.g., DBSCAN, complete-linkage)
  - Include polygon orientation in alignment checks
- Test coverage: `test_text_grouper.py` has basic tests but no rotated/skewed text validation.

**UI Thread Synchronization:**
- Files: `ui/main_window.py` (lines 353-367, 369-381)
- Why fragile: QThread lifecycle management is manual; if user closes window during pipeline execution, dangling references may remain.
- Safe modification:
  - Implement explicit `abort()` method on PipelineWorker
  - Connect window `closeEvent()` to cleanup threads
  - Use context managers or try/finally to guarantee cleanup
- Test coverage: No UI tests; thread cleanup not validated.

## Scaling Limits

**Memory Usage with Large Images:**
- Current capacity: Single image processing with image data + OCR results + placement computation.
- Limit: 4GB+ images will exhaust memory due to:
  - `image.tobytes()` creates full in-memory copy in `_on_pipeline_done`
  - All regions stored in memory simultaneously
  - No streaming or tiling
- Scaling path:
  - Implement tile-based processing for large images
  - Stream regions to disk during OCR if count exceeds threshold
  - Use memory-mapped arrays for image data

**Concurrent OCR Sessions:**
- Current capacity: Single QThread per pipeline; multiple captures spawn multiple threads.
- Limit: With 4+ concurrent pipelines, memory per model (PaddleOCR ~1GB) becomes problematic.
- Scaling path:
  - Implement thread pool with configurable worker count
  - Share single OCR engine instance across threads (with locking)
  - Add queue-based async processing instead of per-request threads

**Font Cache Growth:**
- Current capacity: Unbounded dict of ImageFont objects.
- Limit: After rendering text at 50+ font sizes, cache memory grows linearly.
- Scaling path: See Tech Debt section on unbounded font cache.

## Dependencies at Risk

**deep-translator (unmaintained):**
- Risk: Package shows low maintenance activity; no guarantee of continued API compatibility with Google Translate.
- Impact: If Google changes API endpoint or authentication, translations will fail with no fix path.
- Migration plan:
  - Switch to `google-cloud-translate` (official, paid)
  - Or use `pydantic-settings` + configurable translator interface to swap implementations
  - Or implement fallback to other translation APIs (e.g., Microsoft Translator, OpenAI API)

**paddleocr (large, complex dependency):**
- Risk: Brings in PaddlePaddle framework (~1GB models) with unclear dependency tree.
- Impact: Long startup time; large disk footprint; potential conflicts with PyTorch/TensorFlow installations.
- Migration plan:
  - Profile actual model usage to see if smaller alternatives (e.g., EasyOCR) suffice
  - Consider switching to cloud-based OCR (AWS Textract, Google Vision) for production deployment

**manga-ocr (specialized):**
- Risk: Single-purpose library with niche community; may be abandoned.
- Impact: Japanese OCR quality depends on library; no built-in fallback.
- Migration plan:
  - Evaluate PaddleOCR's Japanese model as primary
  - Keep manga-ocr as optional enhancement (graceful degradation if import fails)

**transformers library version constraint (<4.45):**
- Risk: Pinned to pre-4.45; newer versions have breaking changes or security fixes that won't be applied.
- Impact: Security vulnerabilities in older transformers may not be patched.
- Scaling path: Test and update to latest transformers version; adjust code for any API changes.

## Missing Critical Features

**No Undo/Redo:**
- Problem: User cannot undo translation or annotation after applying overlay.
- Blocks: Users cannot correct mistakes without re-capturing region.

**No Translation History/Caching:**
- Problem: Same text translated multiple times hits Google API each time.
- Blocks: Efficient batch processing; offline mode not possible.

**No Batch File Processing:**
- Problem: UI only accepts single screen region at a time.
- Blocks: Processing full pages or multiple images requires manual per-region captures.

**No OCR Confidence Filtering:**
- Problem: Low-confidence OCR results are displayed without user notification.
- Blocks: Users may not notice when OCR is incorrect.

**No Configuration File Support:**
- Problem: All settings (language, overlay mode, fonts) are not persisted between sessions.
- Blocks: User preferences are lost on restart.

## Test Coverage Gaps

**UI Integration Tests:**
- What's not tested: MainWindow signal flow, thread lifecycle, window dragging, overlay closing.
- Files: `ui/main_window.py`, `ui/region_selector.py`, `ui/result_overlay.py`
- Risk: UI bugs only surface at runtime; refactoring UI code is risky without tests.
- Priority: **Medium** — UI is user-facing but relatively simple.

**Network Resilience:**
- What's not tested: GoogleTranslator timeout, retry behavior, network failures.
- Files: `core/translator.py`
- Risk: Production failures on slow networks or API outages go undetected.
- Priority: **High** — Network is a critical external dependency.

**Large Image Handling:**
- What's not tested: Behavior with images >10000x10000 pixels, memory efficiency, OCR with dense text.
- Files: All pipeline modules
- Risk: Crashes or extreme slowdown on large images used by advanced users.
- Priority: **Medium** — Edge case but impacts scalability.

**Character Encoding Edge Cases:**
- What's not tested: Zero-width characters, combining characters, emoji, RTL scripts, ligatures.
- Files: `core/phonetic_converter.py`, `core/text_grouper.py`
- Risk: Crashes or incorrect output with non-ASCII edge cases.
- Priority: **High** — International users may encounter these.

**OCR Model Fallback:**
- What's not tested: Behavior when OCR model fails to load, download failures, corrupted model cache.
- Files: `core/ocr_engine.py`
- Risk: Silent failures or cryptic error messages on model loading issues.
- Priority: **High** — Model loading is a common failure point.

**Concurrent User Interactions:**
- What's not tested: Rapid button clicks, window resizing during processing, multiple captures in flight.
- Files: `ui/main_window.py`
- Risk: Race conditions, resource leaks, undefined behavior.
- Priority: **Medium** — Unlikely with single-user app but still fragile.

---

*Concerns audit: 2026-03-04*
