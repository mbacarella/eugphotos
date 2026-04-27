#!/usr/bin/env python3
"""Build bib index from ocr_index.json and merge into photos.json."""

import json
import re

BIB_PATTERN = re.compile(r"^\d{1,5}$")
MIN_BIB_CONF = 0.3

OCR_FIXES = str.maketrans({
    "I": "1", "l": "1", "i": "1",
    "O": "0", "o": "0",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "B": "8",
    "G": "6",
    "T": "7",
    "'": "", '"': "", " ": "",
})


def normalize_bib(text: str) -> str | None:
    # Only try normalization if the text already has some digits
    if not re.search(r"\d", text):
        return None
    # Must be short enough to plausibly be a bib
    if len(text) > 7:
        return None
    fixed = text.translate(OCR_FIXES).strip()
    fixed = re.sub(r"^[^0-9]+", "", fixed)
    fixed = re.sub(r"[^0-9]+$", "", fixed)
    if BIB_PATTERN.match(fixed) and len(fixed) >= 2:
        return fixed
    return None


def main():
    with open("photos.json") as f:
        data = json.load(f)

    with open("ocr_index.json") as f:
        ocr_index = json.load(f)

    bib_to_indices: dict[str, list[int]] = {}
    for i, h in enumerate(data["hashes"]):
        texts = ocr_index.get(h, [])
        for entry in texts:
            text = entry["text"]
            conf = entry["conf"]
            if conf < MIN_BIB_CONF:
                continue
            # Try exact match first
            if BIB_PATTERN.match(text):
                bib_to_indices.setdefault(text, []).append(i)
            else:
                # Try normalized match
                fixed = normalize_bib(text)
                if fixed:
                    bib_to_indices.setdefault(fixed, []).append(i)

    data["bibs"] = bib_to_indices

    with open("photos.json", "w") as f:
        json.dump(data, f)

    print(f"Added {len(bib_to_indices):,} unique bibs to photos.json")
    top = sorted(bib_to_indices.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print("Top 10 most-seen bibs:")
    for bib, indices in top:
        print(f"  #{bib}: {len(indices)} photos")


if __name__ == "__main__":
    main()
