# Technology Stack

**Analysis Date:** 2026-03-04

## Languages

**Primary:**
- Python 3.x - All core logic, UI, and tests

## Runtime

**Environment:**
- Python 3.x

**Package Manager:**
- pip
- Lockfile: requirements.txt (present)

## Frameworks

**Core:**
- PyQt5 - Desktop GUI framework for main application window, region selector, and overlay windows

**OCR:**
- PaddleOCR 2.9.1 - Optical character recognition for Chinese, Japanese, and Korean text
- manga-ocr - Specialized Japanese text recognition for manga (lazy-loaded when needed)

**Translation:**
- deep-translator - Translation API client wrapper for Google Translate

**Text Processing:**
- pypinyin - Chinese character to pinyin conversion with tone marks
- pykakasi - Japanese text analysis for furigana and romaji conversion
- korean-romanizer - Korean hangul to romanization

**Image Processing:**
- OpenCV (opencv-python <4.11) - Image preprocessing, enhancement, and manipulation
- Pillow - Image handling, font rendering, drawing text overlays
- PIL.ImageGrab - Screen region capture for desktop integration

**ML/Deep Learning:**
- PaddleOCR dependencies - Includes transformers <4.45 for model support
- transformers <4.45 - Hugging Face transformers library for model support

**Testing:**
- pytest - Unit and integration testing framework

## Key Dependencies

**Critical:**
- paddlepaddle==2.6.2 - Deep learning inference engine underlying PaddleOCR
- paddleocr==2.9.1 - Multi-language OCR with pre-trained models
- PyQt5 - Cross-platform GUI framework
- Pillow - Image processing and font rendering
- opencv-python<4.11 - Image preprocessing with CLAHE enhancement
- deep-translator - Google Translate API wrapper
- pypinyin - Pinyin conversion library
- pykakasi - Japanese morphological analyzer
- korean-romanizer - Korean text romanization
- manga-ocr - Specialized manga Japanese OCR
- numpy<2 - Numerical computing (required by PaddleOCR)
- transformers<4.45 - Neural network models (required by PaddleOCR)

## Configuration

**Environment:**
- PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK environment variable set to "True" (disables PaddleOCR model source validation)
- No .env file currently in use
- Models are cached locally after first download:
  - PaddleOCR models cached in `~/.paddleocr/` (excluded from version control per .gitignore)
  - Transformers models cached in `~/.cache/huggingface/` (standard location)

**Build:**
- No build configuration files (setup.py, pyproject.toml, etc.) present
- Project runs directly via `python main.py`

## Platform Requirements

**Development:**
- Python 3.x with pip
- System fonts for CJK text rendering (fallback chain searches Windows, macOS, and Linux paths)
- PyQt5 GUI framework (requires display server on Linux)
- Sufficient RAM for model loading (PaddleOCR and manga-ocr models are large)

**Production:**
- Windows/macOS/Linux desktop environment with display
- Fonts: System fonts searched from `C:/Windows/Fonts/` (Windows), `/System/Library/Fonts/` (macOS), `/usr/share/fonts/` (Linux)
- Models downloaded on first run (internet required for initial setup)
- GPU optional but beneficial for faster OCR processing

## Model Management

**PaddleOCR Models:**
- Downloaded on-demand during first use of each language
- Supports: Chinese (ch), Japanese (japan), Korean (korean)
- Cached locally to avoid re-download
- Models disabled source validation via environment variable

**Manga-OCR Model:**
- Lazy-loaded only when Japanese text detection triggers specialized recognition
- Uses transformers library for inference
- Pre-trained on manga image data for better Japanese text accuracy

---

*Stack analysis: 2026-03-04*
