# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A tool for browsing Eugene Marathon race day photos. The official site paginates 29K+ photos across 30 server-rendered pages. This project scrapes the photo hashes and produces a static HTML viewer with infinite scroll.

## Commands

```bash
# Scrape photo hashes (writes photos.json)
uv run python scrape.py           # default race 167913
uv run python scrape.py 167913    # explicit race ID

# Serve the viewer locally
python3 -m http.server 8899
# then open http://localhost:8899/index.html
```

## Architecture

- **`scrape.py`** — Fetches all pages from `results.laurelt.com/eug/photos/claim?race=R&page=N`, extracts SHA-256-like hashes from `data-url` attributes on `.photo` divs. Outputs `photos.json`.
- **`photos.json`** — Index file: `{ race, total, s3_prefix, locations, hashes[] }`. Checked in so GitHub Pages can serve it.
- **`index.html`** — Self-contained static page. Loads `photos.json`, renders a responsive CSS grid with IntersectionObserver-based lazy loading (thumbnails) and infinite scroll (100 photos per batch). Click/tap opens a lightbox with `_mid.jpg`. Arrow keys, click, or swipe to navigate. Responsive grid: 2 columns on phones up to 9 on wide screens.

## Deployment

GitHub Pages via Actions workflow (`.github/workflows/pages.yml`). Deploys from repo root on push to `main`. Enable Pages in repo settings → source: GitHub Actions.

## Photo URL scheme

Photos are on S3: `https://brookseeevents.s3.amazonaws.com/participant/{race}/{hash}_{size}.jpg`
- `_thumb.jpg` — small thumbnail (used in grid)
- `_mid.jpg` — medium resolution (used in lightbox)
