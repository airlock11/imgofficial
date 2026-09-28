#!/usr/bin/env python3
from __future__ import annotations

import io
import json
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "pba-official.json"
OUT = ROOT / "assets" / "pba" / "highlights"
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IMG-Sports-Data/1.0; +https://www.imgofficial.com/)"
}

# YouTube Shorts can expose their full vertical cover/frame separately from
# the standard landscape maxresdefault.jpg. Prefer the true 9:16 files.
CANDIDATES = (
    "oardefault.jpg",
    "oar2.jpg",
    "oar1.jpg",
    "oar3.jpg",
)

def fetch_candidate(session: requests.Session, video_id: str, name: str):
    url = f"https://i.ytimg.com/vi/{video_id}/{name}"
    r = session.get(url, headers=HEADERS, timeout=35)
    r.raise_for_status()
    data = r.content

    with Image.open(io.BytesIO(data)) as im:
        width, height = im.size
        fmt = (im.format or "").upper()
        # Only accept a real portrait Shorts image. This rejects YouTube's
        # tiny placeholder/error images and standard landscape thumbnails.
        if height <= width:
            raise RuntimeError(f"not portrait: {width}x{height}")
        if height < 1000 or width < 500:
            raise RuntimeError(f"too small: {width}x{height}")
        rgb = im.convert("RGB")
        return {
            "url": url,
            "name": name,
            "width": width,
            "height": height,
            "pixels": width * height,
            "image": rgb.copy(),
            "format": fmt,
        }

def build_one(session: requests.Session, video_id: str):
    valid = []
    errors = {}
    for name in CANDIDATES:
        try:
            valid.append(fetch_candidate(session, video_id, name))
        except Exception as e:
            errors[name] = str(e)

    if not valid:
        raise RuntimeError("no HD portrait Shorts thumbnail available: " + json.dumps(errors))

    # Pick the largest real portrait source.
    best = max(valid, key=lambda x: x["pixels"])
    out = OUT / f"{video_id}.jpg"

    # Preserve the full vertical composition and use a high JPEG quality.
    best["image"].save(
        out,
        format="JPEG",
        quality=94,
        subsampling=0,
        optimize=True,
        progressive=True,
    )

    if out.stat().st_size < 30_000:
        raise RuntimeError(f"saved poster unexpectedly small: {out.stat().st_size} bytes")

    return {
        "local": "/" + out.relative_to(ROOT).as_posix(),
        "source": best["url"],
        "sourceName": best["name"],
        "width": best["width"],
        "height": best["height"],
        "bytes": out.stat().st_size,
    }

def main():
    obj = json.loads(DATA.read_text(encoding="utf-8"))
    shorts = [x for x in (obj.get("shorts") or []) if x.get("id")][:10]

    if not shorts:
        print("No PBA Shorts found.")
        return 0

    session = requests.Session()
    posters = {}
    failures = {}

    for item in shorts:
        video_id = str(item["id"]).strip()
        try:
            meta = build_one(session, video_id)
            posters[video_id] = meta
            print(
                f"POSTER {video_id}: {meta['width']}x{meta['height']} "
                f"{meta['local']} ({meta['bytes']} bytes)"
            )
        except Exception as e:
            failures[video_id] = str(e)
            print(f"FAILED {video_id}: {e}")

    report = {
        "requested": len(shorts),
        "created": len(posters),
        "failed": failures,
        "posters": posters,
    }
    (OUT / "posters.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
