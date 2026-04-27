#!/usr/bin/env python3
"""Scrape photo hashes from the Eugene Marathon lost-and-found photo pages."""

import json
import sys
import time

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://results.laurelt.com/eug/photos/claim"
S3_PREFIX = "https://brookseeevents.s3.amazonaws.com/participant/"

LOCATIONS = {
    "all": "all",
    "E": "489896",
    "F": "489897",
    "G": "489898",
    "H": "489899",
    "I": "489900",
}


def scrape_page(client: httpx.Client, race: str, page: int, location: str = "all") -> tuple[list[str], int]:
    params = {"race": race, "page": str(page)}
    if location != "all":
        params["location"] = location
    resp = client.get(BASE_URL, params=params)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    hashes = []
    for el in soup.select("[data-url]"):
        url = el["data-url"]
        if "_thumb.jpg" in url:
            h = url.split("/")[-1].replace("_thumb.jpg", "")
            hashes.append(h)

    total_el = soup.select_one("#photo_count_inner")
    total = int(total_el.text.strip()) if total_el else 0
    return hashes, total


def scrape_race(race: str) -> dict:
    with httpx.Client(timeout=30) as client:
        first_hashes, total = scrape_page(client, race, 1)
        per_page = len(first_hashes)
        if per_page == 0:
            print("No photos found.", file=sys.stderr)
            sys.exit(1)

        total_pages = (total + per_page - 1) // per_page
        print(f"{total} photos across {total_pages} pages ({per_page}/page)")

        all_hashes = list(first_hashes)
        for page in range(2, total_pages + 1):
            hashes, _ = scrape_page(client, race, page)
            all_hashes.extend(hashes)
            print(f"  page {page}/{total_pages} — {len(hashes)} photos (total: {len(all_hashes)})")
            time.sleep(0.25)

    return {
        "race": race,
        "total": total,
        "s3_prefix": f"{S3_PREFIX}{race}/",
        "locations": LOCATIONS,
        "hashes": all_hashes,
    }


def main():
    race = sys.argv[1] if len(sys.argv) > 1 else "167913"
    data = scrape_race(race)
    out = "photos.json"
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"Wrote {len(data['hashes'])} hashes to {out}")


if __name__ == "__main__":
    main()
