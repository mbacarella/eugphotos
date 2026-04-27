#!/usr/bin/env python3
"""Download all _mid.jpg images from S3 for OCR processing."""

import asyncio
import json
import sys
from pathlib import Path

import httpx

CONCURRENCY = 50
OUT_DIR = Path("images")


async def worker(queue: asyncio.Queue, client: httpx.AsyncClient, s3_prefix: str, done: list, total: int):
    while True:
        h = await queue.get()
        try:
            dest = OUT_DIR / f"{h}.jpg"
            if dest.exists() and dest.stat().st_size > 0:
                done[0] += 1
                if done[0] % 500 == 0:
                    print(f"  {done[0]:,} / {total:,}", flush=True)
                continue

            url = f"{s3_prefix}{h}_mid.jpg"
            for attempt in range(3):
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                    break
                except (httpx.HTTPStatusError, httpx.TransportError) as e:
                    if attempt < 2:
                        await asyncio.sleep(1)
                    else:
                        print(f"\n  FAILED {h}: {e}", file=sys.stderr)

            done[0] += 1
            if done[0] % 500 == 0:
                print(f"  {done[0]:,} / {total:,}", flush=True)
        finally:
            queue.task_done()


async def main():
    with open("photos.json") as f:
        data = json.load(f)

    hashes = data["hashes"]
    s3_prefix = data["s3_prefix"]
    total = len(hashes)

    OUT_DIR.mkdir(exist_ok=True)

    existing = sum(1 for h in hashes if (OUT_DIR / f"{h}.jpg").exists() and (OUT_DIR / f"{h}.jpg").stat().st_size > 0)
    if existing:
        print(f"Resuming: {existing:,} already downloaded, {total - existing:,} remaining")

    print(f"Downloading {total:,} images at concurrency={CONCURRENCY}...")

    done = [existing]
    queue: asyncio.Queue[str] = asyncio.Queue()
    for h in hashes:
        queue.put_nowait(h)

    limits = httpx.Limits(max_connections=CONCURRENCY, max_keepalive_connections=CONCURRENCY)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, limits=limits) as client:
        workers = [asyncio.create_task(worker(queue, client, s3_prefix, done, total)) for _ in range(CONCURRENCY)]
        await queue.join()
        for w in workers:
            w.cancel()

    print(f"Done. {done[0]:,} / {total:,} images in {OUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
