# External Integrations

**Analysis Date:** 2026-03-04

## APIs & External Services

**Translation:**
- Google Translate (via deep-translator wrapper) - Translates detected text to English
  - SDK/Client: deep-translator library
  - Auth: None (public API via deep-translator)
  - Implementation: `core/translator.py` - GoogleTranslator class
  - Supports: Chinese (zh-CN), Japanese (ja), Korean (ko) source languages

## Data Storage

**Databases:**
- None - Application is stateless, no persistent data storage

**File Storage:**
- Local filesystem only - All output is temporary in-memory images or screen overlays
- Model cache directories (external):
  - `~/.paddleocr/` - PaddleOCR model cache
  - `~/.cache/huggingface/` - Transformers model cache
  - `~/.manga_ocr_models/` - Manga-OCR model cache (if applicable)

**Caching:**
- In-process only:
  - PaddleOCR engine instances cached in `OcrEngine._engines` dict (one per language used)
  - Manga-OCR recognizer lazily loaded and cached in `OcrEngine._manga_ocr`
  - GoogleTranslator instances cached in `Translator` object for language pair
  - Converter objects (Pinyin, Furigana, Romaji, Korean) maintained in memory for reuse

## Authentication & Identity

**Auth Provider:**
- None - No user authentication required
- Application is local-only desktop tool

## Monitoring & Observability

**Error Tracking:**
- None - Errors surfaced via dialog boxes to user

**Logs:**
- Console logging disabled for PaddleOCR (`show_log=False` in `OcrEngine._get_engine()`)
- No persistent logging configured
- Errors caught and displayed via `QMessageBox` dialogs

## CI/CD & Deployment

**Hosting:**
- Desktop application - No remote hosting

**CI Pipeline:**
- Local testing via pytest only
- No CI/CD infrastructure configured

## Environment Configuration

**Required env vars:**
- None required at runtime (optional: PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK is pre-set by application)

**Secrets location:**
- No secrets management - Application is local/offline after model download

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - All integrations are via synchronous library calls (Google Translate API via deep-translator)

## External Model Sources

**PaddleOCR:**
- Downloads from official PaddleOCR model CDN on first use per language
- Models are pre-trained on large OCR datasets
- Supports rotation and angle correction for manga pages
- No custom fine-tuning or local models

**Manga-OCR:**
- Pre-trained model for Japanese text in manga style
- Specialized for handling manga-specific text rendering (vertical text, stylized fonts)
- Lazy-loaded only when Japanese language detected during auto-detect phase

**Transformers (Hugging Face):**
- Downloaded models used by PaddleOCR inference
- Cached locally after download
- No custom fine-tuning

## Network Requirements

**Connectivity:**
- Internet required only for:
  - Initial model downloads (PaddleOCR, manga-ocr, transformers)
  - Google Translate API calls during translation mode
- Offline operation not supported

**Rate Limiting:**
- Google Translate API (via deep-translator) may have rate limits
- Implementation batches translations by speech bubble groups to minimize calls
- See `core/translator.py` - `translate_batch()` method

---

*Integration audit: 2026-03-04*
