#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "logos" / "external"
OUT.mkdir(parents=True, exist_ok=True)

ITEMS = [
    {
        "key": "euroleague",
        "wiki": "commons",
        "filename": "EuroLeague_logo.svg",
        "target": "euroleague.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/EuroLeague_logo.svg",
    },
    {
        "key": "formulae",
        "wiki": "commons",
        "filename": "FIA_Formula_E_World_Championship_Logo.svg",
        "target": "formula-e.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/FIA_Formula_E_World_Championship_Logo.svg",
    },
    {
        "key": "cricket_world_cup",
        "wiki": "commons",
        "filename": "ICC_Men’s_Cricket_World_Cup_logo.svg",
        "target": "cricket-world-cup.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/ICC_Men%E2%80%99s_Cricket_World_Cup_logo.svg",
    },
    {
        "key": "iihf",
        "wiki": "commons",
        "filename": "IIHF_text_logo.svg",
        "target": "iihf.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/IIHF_text_logo.svg",
    },
    {
        "key": "ucl_women",
        "wiki": "commons",
        "filename": "UEFA Women's Champions League logo.svg",
        "target": "uefa-womens-champions-league.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/UEFA%20Women%27s%20Champions%20League%20logo.svg",
    },
    {
        "key": "us_open",
        "wiki": "commons",
        "filename": "Usopen-header-logo.svg",
        "target": "us-open.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Usopen-header-logo.svg",
    },
    {
        "key": "vleague_jp",
        "wiki": "commons",
        "filename": "V.League_Japan_logo.png",
        "target": "vleague-japan.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/V.League_Japan_logo.png",
    },
    {
        "key": "wimbledon",
        "wiki": "commons",
        "filename": "WB-Logo.png",
        "target": "wimbledon.png",
        "old": "https://commons.wikimedia.org/wiki/Special:Redirect/file/WB-Logo.png",
    },
    {
        "key": "fiba",
        "wiki": "commons",
        "filename": "FIBA_logo.svg",
        "target": "fiba.png",
        "old": "https://upload.wikimedia.org/wikipedia/commons/e/e4/FIBA_logo.svg",
    },
    {
        "key": "pba",
        "wiki": "en",
        "filename": "Philippine Basketball Association (logo).svg",
        "target": "pba.png",
        "old": "https://upload.wikimedia.org/wikipedia/en/thumb/d/dd/Philippine_Basketball_Association_%28logo%29.svg/1280px-Philippine_Basketball_Association_%28logo%29.svg.png",
    },
]

HEADERS = {
    "User-Agent": "IMG-Sports-Data/1.0 (https://www.imgofficial.com/; local logo cache)"
}

def host_for(wiki: str) -> str:
    return "commons.wikimedia.org" if wiki == "commons" else "en.wikipedia.org"

def valid_png(data: bytes) -> bool:
    return len(data) > 100 and data.startswith(b"\x89PNG\r\n\x1a\n")

def get_thumbnail_url(session: requests.Session, item: dict) -> str:
    host = host_for(item["wiki"])
    api = f"https://{host}/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": "512",
        "titles": "File:" + item["filename"],
        "origin": "*",
    }
    r = session.get(api, params=params, timeout=45)
    r.raise_for_status()
    data = r.json()
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        raise RuntimeError("No imageinfo pages returned")
    page = next(iter(pages.values()))
    info = (page.get("imageinfo") or [{}])[0]
    url = info.get("thumburl") or info.get("url")
    if not url:
        raise RuntimeError("No thumbnail URL returned")
    return url

def download_one(session: requests.Session, item: dict) -> Path:
    host = host_for(item["wiki"])
    file_url = f"https://{host}/wiki/Special:FilePath/{quote(item['filename'])}?width=512"
    candidates = [file_url]

    # API-derived thumbnail is Wikimedia's recommended lower-bandwidth route.
    try:
        candidates.append(get_thumbnail_url(session, item))
    except Exception as e:
        print(f"API thumbnail lookup warning for {item['key']}: {e}")

    last_error = None
    for url in candidates:
        for attempt in range(1, 7):
            try:
                r = session.get(url, timeout=60, allow_redirects=True)
                if r.status_code == 429:
                    delay = min(30, 4 * attempt)
                    print(f"429 for {item['key']}; retrying after {delay}s")
                    time.sleep(delay)
                    continue
                r.raise_for_status()
                data = r.content
                ctype = (r.headers.get("content-type") or "").lower()
                if "svg" in ctype or data.lstrip().startswith(b"<svg"):
                    # Ask the API route for a PNG thumb if Special:FilePath returned original SVG.
                    raise RuntimeError("received SVG instead of PNG thumbnail")
                if not valid_png(data):
                    raise RuntimeError(f"not a PNG thumbnail ({ctype}, {len(data)} bytes)")
                out = OUT / item["target"]
                out.write_bytes(data)
                print(f"CACHED {item['key']} -> {out.relative_to(ROOT)} ({len(data)} bytes)")
                return out
            except Exception as e:
                last_error = e
                time.sleep(min(10, 2 * attempt))
    raise RuntimeError(f"unable to cache {item['key']}: {last_error}")

def rewrite_sources(mapping: dict[str, str]) -> list[str]:
    changed = []
    exts = {".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json"}
    skip_prefixes = ("backups/", "assets/logos/external/")
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(skip_prefixes):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        original = text
        for old, local in mapping.items():
            text = text.replace(old, local)
        if text != original:
            p.write_text(text, encoding="utf-8")
            changed.append(rel)
    return changed

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    mapping = {}
    downloaded = {}
    failures = {}

    for i, item in enumerate(ITEMS):
        try:
            out = download_one(session, item)
            local = "/" + out.relative_to(ROOT).as_posix()
            mapping[item["old"]] = local
            downloaded[item["key"]] = {
                "source_filename": item["filename"],
                "source_reference": item["old"],
                "local": local,
            }
        except Exception as e:
            failures[item["key"]] = str(e)
        time.sleep(3)

    changed = rewrite_sources(mapping)

    # Verify all original problem URLs are gone if their downloads succeeded.
    remaining = {}
    for item in ITEMS:
        found_in = []
        for p in ROOT.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".html",".htm",".css",".js",".mjs",".cjs",".json"}:
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel.startswith(("backups/","assets/logos/external/")):
                continue
            try:
                t = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if item["old"] in t:
                found_in.append(rel)
        if found_in:
            remaining[item["key"]] = found_in

    report = {
        "downloaded": downloaded,
        "failures": failures,
        "changed_files": changed,
        "remaining_original_urls": remaining,
    }
    (OUT / "REMAINING_SOURCES.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "downloaded": len(downloaded),
        "failures": failures,
        "changed_files": len(changed),
        "remaining": remaining,
    }, indent=2, ensure_ascii=False))

    if failures or remaining:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
