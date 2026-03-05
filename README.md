# Manga Buddy

I made this because I know enough to speak and listen fluently in Chinese and Japanese, but I'm a lot slower when reading the characters. So, I thought it would be nice to have something to add phonetic annotations to the characters, similar to on a Word text document when I was little.
And so, I present Manga Buddy! A desktop application for translating and annotating manga. Capture a region of your screen, and Manga Buddy will detect the text, translate it, or add phonetic annotations (pinyin, furigana, romaji, Korean romanization).

![Manga Buddy](https://raw.githubusercontent.com/Xeposem/manga-buddy/main/screenshot.png)

## Features

- **OCR text detection** — PaddleOCR for text region detection with manga-ocr for accurate Japanese recognition
- **Multi-language support** — Chinese, Japanese, and Korean with automatic language detection
- **Translation** — Translate detected text to English using Google Translate
- **Phonetic annotations** — Pinyin (Chinese), furigana/romaji (Japanese), Korean romanization
- **Smart text placement** — Collision-aware annotation placement that keeps readings consistently positioned
- **Screen capture** — Select any region on your screen to process
- **Dark-themed UI** — Built with PyQt5

## Modes

| Mode | Description |
|------|-------------|
| Translation | Translate detected text to English |
| Pinyin | Show Chinese pinyin above/beside characters |
| Furigana | Show hiragana readings for Japanese kanji |
| Romaji | Show romanized readings for Japanese text |
| Korean | Show romanized readings for Korean hangul |

## Text Replacement

- **Never** — Annotations are placed beside the original text
- **Always** — Annotations overlay the original text
- **Replace if needed** — Try beside first, fall back to overlay when space is limited

## Getting Started

### Prerequisites

- Python 3.9+
- CUDA-capable GPU recommended (for manga-ocr and PaddleOCR)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```bash
python main.py
```

1. Select your language (or use auto-detect)
2. Choose a mode (translation, pinyin, furigana, romaji, or Korean)
3. Click **Capture Region** and drag over the manga panel you want to process
4. The annotated result appears on screen

## Tech Stack

- **OCR** — PaddleOCR (detection) + manga-ocr (Japanese recognition)
- **Translation** — deep-translator (Google Translate)
- **Phonetic conversion** — pypinyin, pykakasi, korean-romanizer
- **UI** — PyQt5 with dark Fusion theme
- **Image processing** — OpenCV, Pillow

