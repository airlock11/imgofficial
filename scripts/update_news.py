#!/usr/bin/env python3
import calendar
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "news-data.json"
UA = "IMG-Sports-News-Updater/1.0 (+https://imgofficial.com)"

FEEDS = [
    {"region":"International","sport":"Sports","name":"BBC Sport","url":"https://feeds.bbci.co.uk/sport/rss.xml"},
    {"region":"International","sport":"Sports","name":"ESPN","url":"https://www.espn.com/espn/rss/news"},
    {"region":"International","sport":"Sports","name":"Sky Sports","url":"https://www.skysports.com/rss/12040"},
    {"region":"International","sport":"Sports","name":"The Guardian Sport","url":"https://www.theguardian.com/uk/sport/rss"},
    {"region":"International","sport":"Football","name":"The Guardian Football","url":"https://www.theguardian.com/football/rss"},
    {"region":"International","sport":"Tennis","name":"The Guardian Tennis","url":"https://www.theguardian.com/sport/tennis/rss"},
    {"region":"Philippines","sport":"Sports","name":"Inquirer Sports","url":"https://sports.inquirer.net/feed"},
    {"region":"Philippines","sport":"Sports","name":"Philstar Sports","url":"https://www.philstar.com/rss/sports"},
    {"region":"Philippines","sport":"Sports","name":"GMA News Sports","url":"https://data.gmanetwork.com/gno/rss/sports/feed.xml"},
    {"region":"Philippines","sport":"Sports","name":"Tiebreaker Times","url":"https://tiebreakertimes.com.ph/feed"},
]

def clean_html(value, limit=320):
    soup = BeautifulSoup(value or "", "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return re.sub(r"Continue reading.*$", "", text, flags=re.I)[:limit]

def image_from_entry(entry):
    for attr in ("media_content", "media_thumbnail"):
        values = entry.get(attr) or []
        for item in values:
            url = item.get("url") if isinstance(item, dict) else None
            if url and url.startswith("http"):
                return url
    for enc in entry.get("enclosures") or []:
        url = enc.get("href") or enc.get("url")
        typ = str(enc.get("type") or "")
        if url and url.startswith("http") and (not typ or typ.startswith("image/")):
            return url
    html = entry.get("summary") or entry.get("description") or ""
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    if img:
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http"):
            return src
    return ""

def published_iso(entry):
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            try:
                return datetime.fromtimestamp(calendar.timegm(value), timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()

def timestamp(value):
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()
    except Exception:
        return 0

def normalize_link(value):
    value = (value or "").strip()
    if not value:
        return ""
    p = urlparse(value)
    return (p.netloc.lower() + p.path.rstrip("/")).lower()

def fetch_feed(cfg):
    parsed = feedparser.parse(
        cfg["url"],
        agent=UA,
        request_headers={"Accept":"application/rss+xml, application/xml, text/xml, */*"},
    )
    items = []
    for entry in parsed.entries[:18]:
        title = clean_html(entry.get("title"), 180)
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "description": clean_html(entry.get("summary") or entry.get("description"), 260),
            "source": cfg["name"],
            "sport": cfg["sport"],
            "region": cfg["region"],
            "image": image_from_entry(entry),
            "published": published_iso(entry),
        })
    return items

def main():
    collected = []
    errors = {}
    for cfg in FEEDS:
        try:
            rows = fetch_feed(cfg)
            if rows:
                collected.extend(rows)
            else:
                errors[cfg["name"]] = "No articles returned"
        except Exception as exc:
            errors[cfg["name"]] = str(exc)[:180]

    collected.sort(key=lambda x: timestamp(x.get("published","")), reverse=True)

    unique = []
    seen = set()
    source_counts = {}
    for item in collected:
        key = normalize_link(item.get("link"))
        if not key or key in seen:
            continue
        source = item["source"]
        if source_counts.get(source, 0) >= 6:
            continue
        seen.add(key)
        source_counts[source] = source_counts.get(source, 0) + 1
        unique.append(item)

    # Keep a balanced current mix: at least a few Philippine stories when
    # available, without allowing one region/source to dominate.
    ph = [x for x in unique if x["region"] == "Philippines"]
    intl = [x for x in unique if x["region"] == "International"]
    selected = []
    selected.extend(ph[:8])
    selected.extend(intl[:22])

    # Sort the mixed set by recency for predictable presentation.
    selected.sort(key=lambda x: timestamp(x.get("published","")), reverse=True)
    selected = selected[:30]

    if not selected:
        raise RuntimeError("No sports news articles could be parsed")

    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "refresh_minutes": 30,
        "counts": {
            "total": len(selected),
            "philippines": sum(1 for x in selected if x["region"] == "Philippines"),
            "international": sum(1 for x in selected if x["region"] == "International"),
        },
        "errors": errors,
        "items": selected,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated_at": out["updated_at"],
        "counts": out["counts"],
        "errors": errors,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
