#!/usr/bin/env python3
"""Run OCR on downloaded images to extract all visible text."""

import json
import sys
from pathlib import Path

import easyocr

IMAGES_DIR = Path("images")
WATERMARK_STRINGS = {"2026", "2025", "2024", "eugene", "marathon", "half"}


def extract_text(reader: easyocr.Reader, path: Path) -> list[dict]:
    results = reader.readtext(str(path), detail=1, paragraph=False)
    texts = []
    for bbox, text, conf in results:
        text = text.strip()
        if not text or conf < 0.2:
            continue
        if text.lower() in WATERMARK_STRINGS:
            continue
        texts.append({"text": text, "conf": round(conf, 3)})
    return texts


def main():
    with open("photos.json") as f:
        data = json.load(f)

    hashes = data["hashes"]
    total = len(hashes)

    ocr_path = Path("ocr_index.json")
    if ocr_path.exists():
        ocr_index = json.load(open(ocr_path))
        print(f"Resuming: {len(ocr_index):,} already processed")
    else:
        ocr_index = {}

    print("Loading EasyOCR model...")
    reader = easyocr.Reader(["en"], gpu=True)

    processed = len(ocr_index)
    with_text = sum(1 for v in ocr_index.values() if v)

    for i, h in enumerate(hashes):
        if h in ocr_index:
            continue

        img_path = IMAGES_DIR / f"{h}.jpg"
        if not img_path.exists():
            continue

        try:
            texts = extract_text(reader, img_path)
        except Exception as e:
            print(f"\n  ERROR on {h}: {e}", file=sys.stderr)
            texts = []

        ocr_index[h] = texts
        if texts:
            with_text += 1

        processed += 1
        if processed % 100 == 0:
            print(f"  {processed:,} / {total:,} processed, {with_text:,} with text", flush=True)
            with open(ocr_path, "w") as f:
                json.dump(ocr_index, f)

    with open(ocr_path, "w") as f:
        json.dump(ocr_index, f)

    print(f"\nDone. {processed:,} images processed, {with_text:,} with text.")
    print(f"Wrote {ocr_path}")


if __name__ == "__main__":
    main()
