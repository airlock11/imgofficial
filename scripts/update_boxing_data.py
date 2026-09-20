#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "boxing-data.json"
API_HOST = "boxing-data-api.p.rapidapi.com"
BASE = f"https://{API_HOST}/v2"
API_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
PAGE_SIZE = 100

if not API_KEY:
    raise RuntimeError("RAPIDAPI_KEY environment variable is required")

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST,
    "Accept": "application/json",
    "User-Agent": "IMG-Boxing-Data-Updater/1.0",
}

def normalized_api_url(value):
    parts = urlsplit(value)
    return urlunsplit(("https", API_HOST, parts.path, parts.query, ""))

def api_get(url, retries=5):
    url = normalized_api_url(url)
    last_error = None
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=45) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw)
                if payload.get("error"):
                    raise RuntimeError(f"API error: {payload['error']}")
                return payload
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                detail = exc.read().decode("utf-8", "replace")[:500]
                raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == retries - 1:
                raise
        time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(str(last_error))

def compact_fighter(f):
    stats = f.get("stats") or {}
    division = f.get("division") or {}
    titles = f.get("titles") or []
    return {
        "id": f.get("id"),
        "name": f.get("name") or f.get("full_name"),
        "nickname": f.get("nickname") or f.get("alias"),
        "age": f.get("age"),
        "gender": f.get("gender"),
        "nationality": f.get("nationality"),
        "nationality_code": f.get("nationality_code"),
        "stance": f.get("stance"),
        "height": f.get("height"),
        "height_cm": f.get("height_cm"),
        "height_ft": f.get("height_ft"),
        "reach": f.get("reach"),
        "reach_cm": f.get("reach_cm"),
        "reach_in": f.get("reach_in"),
        "debut": f.get("debut"),
        "division": {
            "id": division.get("id"),
            "name": division.get("name"),
            "weight_lb": division.get("weight_lb"),
            "weight_kg": division.get("weight_kg"),
        } if division else None,
        "stats": {
            "wins": stats.get("wins", 0),
            "losses": stats.get("losses", 0),
            "draws": stats.get("draws", 0),
            "total_bouts": stats.get("total_bouts", 0),
            "total_rounds": stats.get("total_rounds"),
            "ko_wins": stats.get("ko_wins", 0),
            "stopped": stats.get("stopped"),
        },
        "titles": [
            {
                "id": t.get("id"),
                "name": t.get("name") or t.get("title"),
            }
            for t in titles if isinstance(t, dict)
        ],
    }

def fetch_all_fighters():
    url = f"{BASE}/fighters/?page_size={PAGE_SIZE}"
    fighters = []
    seen_ids = set()
    seen_urls = set()
    pages = 0

    while url:
        normalized = normalized_api_url(url)
        if normalized in seen_urls:
            raise RuntimeError("Pagination repeated the same URL")
        seen_urls.add(normalized)

        payload = api_get(normalized)
        rows = payload.get("data") or []
        for row in rows:
            fighter = compact_fighter(row)
            fighter_id = fighter.get("id")
            if not fighter_id or fighter_id in seen_ids:
                continue
            seen_ids.add(fighter_id)
            fighters.append(fighter)

        pages += 1
        pagination = payload.get("pagination") or {}
        next_page = pagination.get("next_page")
        if next_page:
            url = next_page
        else:
            current = int(pagination.get("page") or 1)
            total = int(pagination.get("total_pages") or 1)
            url = f"{BASE}/fighters/?page_size={PAGE_SIZE}&page_num={current + 1}" if current < total else None

        if pages > 5000:
            raise RuntimeError("Pagination safety limit exceeded")

        if url:
            time.sleep(0.08)

    fighters.sort(key=lambda x: (str(x.get("name") or "").casefold(), str(x.get("id") or "")))
    return fighters, pages

def build_divisions(fighters):
    divisions = {}
    for fighter in fighters:
        d = fighter.get("division") or {}
        key = d.get("id") or d.get("name")
        if not key:
            continue
        divisions[key] = {
            "id": d.get("id"),
            "name": d.get("name"),
            "weight_lb": d.get("weight_lb"),
            "weight_kg": d.get("weight_kg"),
        }
    return sorted(divisions.values(), key=lambda d: (d.get("weight_lb") is None, -(d.get("weight_lb") or 0), d.get("name") or ""))

def main():
    fighters, pages = fetch_all_fighters()
    if not fighters:
        raise RuntimeError("Boxing API returned no fighters; refusing to overwrite the existing cache")

    divisions = build_divisions(fighters)
    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Boxing Data API",
        "refresh_hours": 12,
        "total_fighters": len(fighters),
        "pages_fetched": pages,
        "divisions": divisions,
        "fighters": fighters,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "updated_at": out["updated_at"],
        "fighters": out["total_fighters"],
        "divisions": len(divisions),
        "pages_fetched": pages,
    }))

if __name__ == "__main__":
    main()
