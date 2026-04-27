# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A better interface for browsing Eugene Marathon race day photos. The official site (results.laurelt.com) paginates 29K+ photos with a clunky UI. This project scrapes the photo hashes, runs OCR to extract bib numbers, and produces a static HTML viewer with infinite scroll and bib search.

## Commands

```bash
# 1. Scrape photo hashes (writes photos.json)
uv run python scrape.py           # default race 167913
uv run python scrape.py 167913    # explicit race ID

# 2. Download all _mid.jpg images for OCR (~9.6GB)
uv run python download_images.py

# 3. Run OCR on all images (writes ocr_index.json, resumable)
uv run python extract_text.py

# 4. Build bib index from OCR data (updates photos.json with bibs field)
uv run python build_index.py

# Serve locally
python3 -m http.server 8899
```

## Architecture

### Pipeline

1. **`scrape.py`** — Fetches all pages from `results.laurelt.com/eug/photos/claim?race=R&page=N`, extracts hashes from `data-url` attributes. Outputs `photos.json` with `{ race, total, s3_prefix, hashes[] }`.
2. **`download_images.py`** — Async downloads all `_mid.jpg` images to `images/` at 50 concurrent connections. Resumable.
3. **`extract_text.py`** — Runs EasyOCR (GPU) on every image, saves all detected text with confidence scores to `ocr_index.json`. Filters watermark strings (2026, eugene, marathon). Resumable, checkpoints every 100 images.
4. **`build_index.py`** — Reads `ocr_index.json`, extracts bib numbers (1-5 digit numbers at >=0.3 confidence), writes `bibs` mapping (`bib -> [photo indices]`) into `photos.json`. Fast, re-runnable.

### Viewer

- **`index.html`** — Self-contained static page. Loads `photos.json`, renders a responsive CSS grid (2 cols mobile → 9 cols ultrawide). Features:
  - IntersectionObserver lazy loading for thumbnails
  - Infinite scroll (100 photos per batch)
  - Range slider scrubber with debounced jump
  - Lightbox with arrow keys, swipe, and history.pushState (back button closes)
  - Bib search: filters to matching photos with teal border, shows ±2 context photos (dimmed), clusters separated by dividers. Lightbox navigates all photos so you can arrow past the context window.
  - Right-click/long-press on grid photos targets `_mid.jpg` (full size)

### Data files

- **`photos.json`** — Checked in. Photo index + bib search data for the viewer.
- **`ocr_index.json`** — Not checked in. Raw OCR output (all text per image). Preserved for future features (sign text search).
- **`images/`** — Not checked in. Downloaded `_mid.jpg` files for OCR processing.

## Deployment

GitHub Pages via Actions workflow (`.github/workflows/pages.yml`). Deploys from repo root on push to `main`. Enable Pages in repo settings → source: GitHub Actions.

## Photo URL scheme

Photos are on S3: `https://brookseeevents.s3.amazonaws.com/participant/{race}/{hash}_{size}.jpg`
- `_thumb.jpg` — small thumbnail (~13KB, used in grid)
- `_mid.jpg` — medium resolution (~388KB, used in lightbox and OCR)
