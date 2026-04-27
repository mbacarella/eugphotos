#!/usr/bin/env python3
"""Build bib index from ocr_index.json and merge into photos.json."""

import json
import re

BIB_PATTERN = re.compile(r"^\d{1,5}$")
MIN_BIB_CONF = 0.3


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
            if BIB_PATTERN.match(text) and conf >= MIN_BIB_CONF:
                bib_to_indices.setdefault(text, []).append(i)

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
