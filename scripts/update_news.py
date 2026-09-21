#!/usr/bin/env python3
import calendar
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import feedparser
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "news-data.json"
UA = "IMG-Sports-News-Updater/1.0 (+https://imgofficial.com)"

VIDEO_FEEDS = [
    {"name":"BBC Sport","channel_id":"UCW6-BQWFA70Dyyc7ZpZ9Xlg"},
    {"name":"ESPN","channel_id":"UCiWLfSweyRNmLpgEHekhoAg"},
    {"name":"NBA","channel_id":"UCWJ2lWNubArHWmf3FIHbfcQ"},
    {"name":"NFL","channel_id":"UCDVYQ4Zhbm3S2dlz7P1GBDg"},
    {"name":"Formula 1","channel_id":"UCB_qr75-ydFVKSF9Dmo6izg"},
    {"name":"UFC","channel_id":"UCvgfXK4nTYKudb0rFR6noLA"},
    {"name":"Volleyball World","channel_id":"UCNMg6XDhRZI2QzL4pWOvP_w"},
    {"name":"NBL-Pilipinas","channel_id":"UCJDBLldRGVJPEvyjJdSHefw"},
]

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


def _extract_json_object(text, marker):
    start = text.find(marker)
    if start < 0:
        return None
    start = text.find("{", start + len(marker))
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


def _video_title(renderer):
    title = renderer.get("title") or {}
    if isinstance(title, dict):
        simple = title.get("simpleText")
        if simple:
            return clean_html(simple, 180)
        runs = title.get("runs") or []
        value = " ".join(str(x.get("text") or "") for x in runs if isinstance(x, dict)).strip()
        if value:
            return clean_html(value, 180)
    return ""


def _walk_video_renderers(node, found):
    if isinstance(node, dict):
        if "videoRenderer" in node and isinstance(node["videoRenderer"], dict):
            found.append(node["videoRenderer"])
        if "gridVideoRenderer" in node and isinstance(node["gridVideoRenderer"], dict):
            found.append(node["gridVideoRenderer"])
        for value in node.values():
            _walk_video_renderers(value, found)
    elif isinstance(node, list):
        for value in node:
            _walk_video_renderers(value, found)


def fetch_ytdlp_channel_videos(cfg):
    url = "https://www.youtube.com/channel/" + cfg["channel_id"] + "/videos"
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--playlist-end", "3",
        "--dump-json",
        "--no-warnings",
        "--quiet",
        url,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError((proc.stderr or "yt-dlp failed")[:180])

    rows = []
    seen = set()
    now = datetime.now(timezone.utc)
    for idx, line in enumerate(proc.stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        video_id = str(item.get("id") or "")
        title = clean_html(item.get("title"), 180)
        if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id) or not title or video_id in seen:
            continue
        seen.add(video_id)
        ts = item.get("timestamp") or item.get("release_timestamp")
        if ts:
            try:
                published = datetime.fromtimestamp(float(ts), timezone.utc).isoformat()
            except Exception:
                published = (now - timedelta(seconds=idx)).isoformat()
        else:
            published = (now - timedelta(seconds=idx)).isoformat()
        rows.append({
            "id": video_id,
            "title": title,
            "source": cfg["name"],
            "link": "https://www.youtube.com/watch?v=" + video_id,
            "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
            "published": published,
        })
        if len(rows) >= 3:
            break
    return rows


def fetch_youtube_channel_page(cfg):
    url = "https://www.youtube.com/channel/" + cfg["channel_id"] + "/videos?hl=en&gl=US"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(req, timeout=25) as response:
        html = response.read().decode("utf-8", "replace")

    data = (
        _extract_json_object(html, "var ytInitialData =")
        or _extract_json_object(html, "window[\"ytInitialData\"] =")
        or _extract_json_object(html, "ytInitialData =")
    )

    rows = []
    seen = set()
    if data:
        renderers = []
        _walk_video_renderers(data, renderers)
        for idx, renderer in enumerate(renderers):
            video_id = str(renderer.get("videoId") or "")
            title = _video_title(renderer)
            if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id) or not title or video_id in seen:
                continue
            seen.add(video_id)
            rows.append({
                "id": video_id,
                "title": title,
                "source": cfg["name"],
                "link": "https://www.youtube.com/watch?v=" + video_id,
                "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
                "published": (datetime.now(timezone.utc) - timedelta(seconds=idx)).isoformat(),
            })
            if len(rows) >= 3:
                return rows

    # Last-resort extraction for channel pages where ytInitialData is embedded differently.
    for idx, match in enumerate(re.finditer(r'\\?"videoId\\?"\s*:\s*\\?"([A-Za-z0-9_-]{6,})', html)):
        video_id = match.group(1)
        if video_id in seen:
            continue
        window = html[match.start():match.start() + 2500]
        title_match = re.search(r'\\?"title\\?"\s*:\s*\{.*?\\?"text\\?"\s*:\s*\\?"([^"\\]{3,180})', window)
        title = clean_html(title_match.group(1), 180) if title_match else ""
        if not title:
            continue
        seen.add(video_id)
        rows.append({
            "id": video_id,
            "title": title,
            "source": cfg["name"],
            "link": "https://www.youtube.com/watch?v=" + video_id,
            "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
            "published": (datetime.now(timezone.utc) - timedelta(seconds=idx)).isoformat(),
        })
        if len(rows) >= 3:
            break

    return rows


def fetch_videos():
    videos = []
    errors = {}
    for cfg in VIDEO_FEEDS:
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + cfg["channel_id"]
        try:
            parsed = feedparser.parse(
                url,
                agent=UA,
                request_headers={"Accept":"application/atom+xml, application/xml, text/xml, */*"},
            )
            added = 0
            for entry in parsed.entries[:6]:
                video_id = (
                    entry.get("yt_videoid")
                    or entry.get("videoid")
                    or ""
                )
                if not video_id:
                    link = entry.get("link") or ""
                    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})", link)
                    video_id = m.group(1) if m else ""
                if not video_id:
                    continue
                title = clean_html(entry.get("title"), 180)
                if not title:
                    continue
                videos.append({
                    "id": video_id,
                    "title": title,
                    "source": cfg["name"],
                    "link": "https://www.youtube.com/watch?v=" + video_id,
                    "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
                    "published": published_iso(entry),
                })
                added += 1
                if added >= 3:
                    break
            if not added:
                fallback = fetch_ytdlp_channel_videos(cfg)
                if not fallback:
                    fallback = fetch_youtube_channel_page(cfg)
                if fallback:
                    videos.extend(fallback)
                    added = len(fallback)
                else:
                    errors[cfg["name"]] = "No videos returned from RSS, yt-dlp, or channel page"
        except Exception as exc:
            fallback_errors = []
            fallback = []
            try:
                fallback = fetch_ytdlp_channel_videos(cfg)
            except Exception as ytdlp_exc:
                fallback_errors.append("yt-dlp: " + str(ytdlp_exc))
            if not fallback:
                try:
                    fallback = fetch_youtube_channel_page(cfg)
                except Exception as page_exc:
                    fallback_errors.append("channel page: " + str(page_exc))
            if fallback:
                videos.extend(fallback)
            else:
                detail = " | ".join([str(exc)] + fallback_errors)
                errors[cfg["name"]] = detail[:180]

    videos.sort(key=lambda x: timestamp(x.get("published","")), reverse=True)
    unique = []
    seen_ids = set()
    seen_titles = set()
    for video in videos:
        title_key = re.sub(r"[^a-z0-9]+", " ", video.get("title","").lower()).strip()
        if video["id"] in seen_ids or (title_key and title_key in seen_titles):
            continue
        seen_ids.add(video["id"])
        if title_key:
            seen_titles.add(title_key)
        unique.append(video)

    # Put different sources first so the two visible video cards are varied.
    selected = []
    used_sources = set()
    for video in unique:
        if video["source"] in used_sources:
            continue
        selected.append(video)
        used_sources.add(video["source"])
        if len(selected) >= 2:
            break
    for video in unique:
        if video not in selected:
            selected.append(video)
        if len(selected) >= 6:
            break

    return selected[:6], errors

def main():
    collected = []
    errors = {}
    videos, video_errors = fetch_videos()
    errors.update({"video:" + k: v for k, v in video_errors.items()})
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
        "refresh_minutes": 20,
        "counts": {
            "total": len(selected),
            "philippines": sum(1 for x in selected if x["region"] == "Philippines"),
            "international": sum(1 for x in selected if x["region"] == "International"),
        },
        "errors": errors,
        "videos": videos,
        "items": selected,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated_at": out["updated_at"],
        "counts": out["counts"],
        "videos": len(videos),
        "errors": errors,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
