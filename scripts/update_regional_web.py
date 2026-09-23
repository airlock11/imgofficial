#!/usr/bin/env python3
import html
import io
import json
import re
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import pytesseract

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "regional-web.json"
PBA_OFFICIAL_OUT = ROOT / "pba-official.json"
UAAP_OFFICIAL_OUT = ROOT / "uaap-official.json"
UA = "Mozilla/5.0 (compatible; IMG-Sports-WebUpdater/1.0; +https://imgofficial.com)"
PHT = timezone(timedelta(hours=8))

URLS = {
    "pba": "https://skedcheck.com/pba-games-schedule-scores/",
    "pba_news": "https://www.pba.ph/news",
    "uaap": "https://skedcheck.com/uaap-mens-basketball-schedule-scores/",
    "uaap_stats": "https://uaap.org/stats/uaap-season-89-men-s-basketball",
    "uaap_live_stats": "https://uaap.livestats.ph/tournaments/uaap-season-89-men-s-basketball",
    "uaap_basketball": "https://uaap.org/sports/basketball",
    "uaap_articles": "https://uaap.org/posts/articles",
    "uaap_photos": "https://uaap.org/posts/photo_gallery",
    "uaap_videos": "https://uaap.org/posts/video_gallery",
    "mpbl_fixtures": "https://www.forebet.com/en/basketball/philippines/mpbl/fixtures",
    "mpbl_results": "https://www.forebet.com/en/basketball/philippines/mpbl/results",
    "mpbl_standings": "https://live2sport.com/Basketball.php/Philippines_MBPL/1/2026/",
    "nbl_official": "http://nblp.web.geniussports.com/",
    "nbl_facebook": "https://www.facebook.com/nblpilipinas",
    "nbl_facebook_share": "https://www.facebook.com/share/18tLhjYjUv/",
    "nbl_updates": "https://www.findglocal.com/PH/Cabuyao/1997682720482608/NBL-Pilipinas",
    "nblaus": "https://www.nbl.com.au/",
    "vba_results": "https://www.forebet.com/en/basketball/vietnam/results",
    "vba_betexplorer": "https://www.betexplorer.com/basketball/vietnam/vba/",
    "vba_ticket": "https://ticket.vba.vn/team/5",
    "nbl_youtube_feed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCJDBLldRGVJPEvyjJdSHefw",
    "tap": "https://tapdmv.com/tapsports/"
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def lines(url):
    soup = BeautifulSoup(fetch(url), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return [re.sub(r"\s+", " ", x).strip() for x in soup.get_text("\n").splitlines() if re.sub(r"\s+", " ", x).strip()]

def load():
    try:
        return json.loads(OUT.read_text("utf-8"))
    except Exception:
        return {"leagues": {}}

def pht_iso_from_dmy(dmy):
    dt = datetime.strptime(dmy, "%d/%m/%Y").replace(hour=12, tzinfo=PHT)
    return dt.isoformat()

def pht_iso_from_month(text, tm=None):
    text = re.sub(r"\s*\|\s*[A-Za-z]+$", "", text).strip()
    dt = datetime.strptime(text, "%B %d, %Y")
    if tm:
        m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", tm, re.I)
        if m:
            h, minute = int(m.group(1)), int(m.group(2))
            if m.group(3).upper() == "PM" and h < 12: h += 12
            if m.group(3).upper() == "AM" and h == 12: h = 0
            dt = dt.replace(hour=h, minute=minute)
    else:
        dt = dt.replace(hour=12)
    return dt.replace(tzinfo=PHT).isoformat()

def clean_team(s):
    return re.sub(r"\s+[A-Z]{2,5}$", "", s.strip()).strip()

def parse_pba():
    xs = lines(URLS["pba"])
    games, day = [], None
    date_re = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2026(?:\s*\|\s*[A-Za-z]+)?$")
    i = 0
    while i < len(xs):
        if date_re.match(xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if i + 3 < len(xs) and re.fullmatch(r"\d{2,3}\s*\|\s*\d{2,3}", xs[i+1]) and xs[i+2].upper() == "FINAL":
            first, second = clean_team(xs[i]), clean_team(xs[i+3])
            a, b = [v.strip() for v in xs[i+1].split("|")]
            iso = pht_iso_from_month(day)
            games.append({"eventId":"web-pba-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":second,"home":first,"awayScore":b,"homeScore":a,"status":"Final","state":"final","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 4; continue
        if i + 2 < len(xs) and re.fullmatch(r"VS\s+\d{1,2}:\d{2}\s*(AM|PM)", xs[i+1], re.I):
            first, second = clean_team(xs[i]), clean_team(xs[i+2])
            tm = xs[i+1][2:].strip()
            iso = pht_iso_from_month(day, tm)
            games.append({"eventId":"web-pba-scheduled-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · %I:%M %p").replace(" 0"," "),"away":first,"home":second,"awayScore":"—","homeScore":"—","status":"Scheduled","state":"scheduled","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 3; continue
        i += 1
    if not games:
        existing = load().get("leagues", {}).get("pba", {})
        if existing:
            return existing
        raise RuntimeError("No PBA games parsed")

    # Preserve a verified recent final when the public page scraper temporarily
    # exposes only the two Aug 14 results. dedupe_games removes this seed
    # automatically once the same matchup is parsed directly from the source.
    verified_recent = [{
        "eventId":"verified-pba-20260812-magnolia-phoenix",
        "date":"2026-08-12T19:30:00+08:00",
        "displayTime":"Aug 12 · Final",
        "away":"Phoenix",
        "home":"Magnolia Chicken Timplados Hotshots",
        "awayScore":"101",
        "homeScore":"115",
        "status":"Final",
        "state":"final",
        "sourceName":"SkedCheck",
        "sourceUrl":URLS["pba"]
    }]
    games = dedupe_games(games + verified_recent)
    return {"league":"PBA","season":"2026 Governors' Cup","coverage":"Schedule and final scores","note":"Automatically refreshed from public web schedule/results.","sources":[{"name":"SkedCheck","url":URLS["pba"]},{"name":"PBA Official","url":"https://www.pba.ph/"}],"games":games[:40]}


PBA_PHOTO_FEEDS = [
    {"name":"Philstar Sports","url":"https://www.philstar.com/rss/sports"},
    {"name":"Inquirer Sports","url":"https://sports.inquirer.net/feed"},
    {"name":"Tiebreaker Times","url":"https://tiebreakertimes.com.ph/feed"},
    {"name":"GMA News Sports","url":"https://data.gmanetwork.com/gno/rss/sports/feed.xml"},
]

PBA_TEAM_ALIASES = {
    "Barangay Ginebra": ["barangay ginebra", "ginebra", "gin kings"],
    "Barangay Ginebra San Miguel": ["barangay ginebra", "ginebra", "gin kings"],
    "Meralco Bolts": ["meralco", "bolts"],
    "NLEX Road Warriors": ["nlex", "road warriors"],
    "Converge FiberXers": ["converge", "fiberxers", "fiber xers"],
    "Phoenix": ["phoenix", "fuel masters"],
    "Magnolia Chicken Timplados Hotshots": ["magnolia", "hotshots"],
    "San Miguel Beermen": ["san miguel", "beermen"],
    "TNT Tropang 5G": ["tnt", "tropang 5g", "tropang giga"],
    "Terrafirma Dyip": ["terrafirma", "dyip"],
    "Rain or Shine Elasto Painters": ["rain or shine", "elasto painters", "painters"],
    "Blackwater Bossing": ["blackwater", "bossing"],
    "Macau Giant Pandas": ["macau giant pandas", "giant pandas"],
    "Titan Ultra Giant Risers": ["titan ultra", "giant risers", "titan"],
}

def _photo_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

def _team_aliases(team):
    aliases = PBA_TEAM_ALIASES.get(str(team or "").strip())
    if aliases:
        return [_photo_text(x) for x in aliases]
    value = _photo_text(team)
    return [value] if value else []

def _team_in_text(team, text):
    hay = " " + _photo_text(text) + " "
    return any((" " + alias + " ") in hay for alias in _team_aliases(team) if alias)

def _rss_image(item):
    for tag_name in ("media:content", "media:thumbnail", "enclosure"):
        tag = item.find(tag_name)
        if tag:
            value = tag.get("url") or tag.get("href")
            if value and str(value).startswith("http"):
                return str(value)
    desc = item.find("description")
    if desc:
        soup = BeautifulSoup(desc.get_text(" ", strip=False), "html.parser")
        img = soup.find("img")
        if img:
            value = img.get("src") or img.get("data-src")
            if value and str(value).startswith("http"):
                return str(value)
    return ""

def _rss_date(item):
    for name in ("pubDate", "published", "updated"):
        tag = item.find(name)
        if not tag:
            continue
        value = tag.get_text(" ", strip=True)
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                pass
    return None

def pba_photo_feed_items():
    rows = []
    for cfg in PBA_PHOTO_FEEDS:
        try:
            xml = fetch(cfg["url"])
            soup = BeautifulSoup(xml, "xml")
            for item in soup.find_all("item")[:40]:
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                title_text = title.get_text(" ", strip=True) if title else ""
                link_text = link.get_text(" ", strip=True) if link else ""
                desc_text = BeautifulSoup(desc.get_text(" ", strip=False), "html.parser").get_text(" ", strip=True) if desc else ""
                if not title_text or not link_text:
                    continue
                rows.append({
                    "sourceName": cfg["name"],
                    "title": title_text,
                    "url": link_text,
                    "description": desc_text,
                    "published": _rss_date(item),
                    "feedImage": _rss_image(item),
                })
        except Exception as ex:
            print("PBA photo feed", cfg["name"], type(ex).__name__, str(ex)[:120])
    return rows

def article_game_photo(url):
    try:
        page = fetch(url)
        soup = BeautifulSoup(page, "html.parser")
        image = ""
        for attrs in (
            {"property":"og:image"},
            {"name":"twitter:image"},
            {"property":"twitter:image"},
        ):
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                image = str(tag.get("content")).strip()
                if image.startswith("http"):
                    break
        page_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        return image, page_text
    except Exception:
        return "", ""

def discover_pba_game_photo(game, feed_items):
    try:
        game_dt = datetime.fromisoformat(str(game.get("date") or "").replace("Z","+00:00"))
    except Exception:
        return None
    if game_dt.tzinfo is None:
        game_dt = game_dt.replace(tzinfo=PHT)

    away = game.get("away") or ""
    home = game.get("home") or ""
    candidates = []
    for item in feed_items:
        published = item.get("published")
        if published:
            try:
                delta_days = abs((published.astimezone(PHT).date() - game_dt.astimezone(PHT).date()).days)
            except Exception:
                delta_days = 99
            if delta_days > 2:
                continue
        combined = (item.get("title") or "") + " " + (item.get("description") or "")
        away_hit = _team_in_text(away, combined)
        home_hit = _team_in_text(home, combined)
        if not (away_hit and home_hit):
            continue
        title = item.get("title") or ""
        score = 100
        if _team_in_text(away, title) and _team_in_text(home, title):
            score += 25
        if "pba" in _photo_text(combined):
            score += 5
        candidates.append((score, item))

    for _, item in sorted(candidates, key=lambda row: row[0], reverse=True):
        image, page_text = article_game_photo(item["url"])
        # Final verification: the article itself must mention both teams/aliases.
        if page_text and not (_team_in_text(away, page_text) and _team_in_text(home, page_text)):
            continue
        image = image or item.get("feedImage") or ""
        if not image.startswith("http"):
            continue
        return {
            "eventId": game.get("eventId") or game.get("id") or "",
            "date": str(game.get("date") or "")[:10],
            "away": away,
            "home": home,
            "image": image,
            "credit": item["sourceName"],
            "sourceName": item["sourceName"],
            "sourceUrl": item["url"],
        }
    return None

def update_pba_previous_game_photos(pba_league):
    try:
        official = json.loads(PBA_OFFICIAL_OUT.read_text("utf-8"))
    except Exception:
        official = {}

    games = list((pba_league or {}).get("games") or [])
    finals = sorted(
        [g for g in games if g.get("state") == "final"],
        key=lambda g: g.get("date", ""),
        reverse=True,
    )[:3]
    existing = list(official.get("previousGamePhotos") or [])
    feed_items = None
    updated = []

    def prior_for(game):
        event_id = str(game.get("eventId") or game.get("id") or "")
        day = str(game.get("date") or "")[:10]
        for item in existing:
            if event_id and str(item.get("eventId") or "") == event_id:
                return item
            if (
                str(item.get("date") or "") == day
                and _photo_text(item.get("away")) == _photo_text(game.get("away"))
                and _photo_text(item.get("home")) == _photo_text(game.get("home"))
            ):
                return item
        return None

    for game in finals:
        prior = prior_for(game)
        if prior and str(prior.get("image") or "").startswith("http"):
            updated.append(prior)
            continue
        if feed_items is None:
            feed_items = pba_photo_feed_items()
        found = discover_pba_game_photo(game, feed_items)
        if found:
            updated.append(found)

    old_compact = json.dumps(existing, sort_keys=True, ensure_ascii=False)
    new_compact = json.dumps(updated, sort_keys=True, ensure_ascii=False)
    if old_compact != new_compact:
        official["previousGamePhotos"] = updated
        official["previousGamePhotosUpdatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        PBA_OFFICIAL_OUT.write_text(json.dumps(official, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(json.dumps({
            "pba_previous_game_photos": len(updated),
            "games": [x.get("eventId") for x in updated],
        }, ensure_ascii=False))




def _pba_news_image(soup, article_url):
    for attrs in (
        {"property":"og:image"},
        {"name":"twitter:image"},
        {"property":"twitter:image"},
    ):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            value = urllib.parse.urljoin(article_url, str(tag.get("content")).strip())
            if value.startswith("http"):
                return value

    # PBA article photos are currently served from dashboard.pba.ph/assets/news/.
    for tag in soup.find_all(["img", "a"]):
        value = tag.get("src") or tag.get("data-src") or tag.get("href")
        if not value:
            continue
        value = urllib.parse.urljoin(article_url, str(value).strip())
        if "/assets/news/" in value and value.startswith("http"):
            return value
    return ""


def _pba_news_date(soup):
    time_tag = soup.find("time")
    if time_tag:
        raw = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
        if raw:
            try:
                return datetime.fromisoformat(str(raw).replace("Z","+00:00")).isoformat()
            except Exception:
                pass

    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    m = re.search(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),\s+(20\d{2})\b",
        text,
        re.I,
    )
    if not m:
        return ""
    raw = " ".join(m.groups())
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=PHT).isoformat()
        except Exception:
            pass
    return ""


def fetch_pba_official_news(limit=6):
    page = fetch(URLS["pba_news"])
    soup = BeautifulSoup(page, "html.parser")
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(URLS["pba_news"], str(a.get("href") or "").strip())
        parsed = urllib.parse.urlparse(href)
        if parsed.netloc.lower() not in ("pba.ph", "www.pba.ph"):
            continue
        path = parsed.path.rstrip("/")
        if not path.startswith("/news/") or path == "/news":
            continue
        title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
        if len(title) < 12:
            continue
        canonical = "https://www.pba.ph" + path
        if canonical in seen:
            continue
        seen.add(canonical)
        links.append((title, canonical))
        if len(links) >= limit:
            break

    rows = []
    for fallback_title, url in links:
        try:
            article = BeautifulSoup(fetch(url), "html.parser")
            h1 = article.find("h1")
            title = re.sub(r"\s+", " ", h1.get_text(" ", strip=True) if h1 else fallback_title).strip()
            image = _pba_news_image(article, url)
            published = _pba_news_date(article)
        except Exception as ex:
            print("PBA news article", url, type(ex).__name__, str(ex)[:120])
            title, image, published = fallback_title, "", ""

        rows.append({
            "title": title or fallback_title,
            "url": url,
            "image": image,
            "published": published,
            "sourceName": "PBA Official",
        })
    return rows


def update_pba_official_news():
    try:
        official = json.loads(PBA_OFFICIAL_OUT.read_text("utf-8"))
    except Exception:
        official = {}

    previous = list(official.get("headlines") or [])
    previous_by_url = {str(x.get("url") or ""): x for x in previous if x.get("url")}

    try:
        fresh = fetch_pba_official_news(6)
    except Exception as ex:
        print("PBA official news", type(ex).__name__, str(ex)[:180])
        fresh = []

    # Keep a previously verified photo/date when one article fetch is temporarily blocked.
    for row in fresh:
        prior = previous_by_url.get(str(row.get("url") or ""))
        if prior:
            if not str(row.get("image") or "").startswith("http"):
                row["image"] = prior.get("image") or ""
            if not row.get("published"):
                row["published"] = prior.get("published") or ""

    # Never erase known-good news because the PBA site temporarily blocks the runner.
    if not fresh:
        return len(previous)

    old_compact = json.dumps(previous, sort_keys=True, ensure_ascii=False)
    new_compact = json.dumps(fresh, sort_keys=True, ensure_ascii=False)
    if old_compact != new_compact:
        official["headlines"] = fresh
        official["headlinesSource"] = {
            "name": "PBA Official",
            "url": URLS["pba_news"],
        }
        official["headlinesUpdatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        PBA_OFFICIAL_OUT.write_text(json.dumps(official, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(json.dumps({
            "pba_headlines": len(fresh),
            "photos": sum(1 for x in fresh if str(x.get("image") or "").startswith("http")),
        }, ensure_ascii=False))
    return len(fresh)


PBA_YOUTUBE_CHANNEL_ID = "UC9WkScCyThtumtf9XVO4eWQ"
PBA_YOUTUBE_SHORTS_URL = "https://www.youtube.com/@PBAOfficial/shorts"

def fetch_pba_youtube_shorts(limit=12):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--playlist-end", str(limit),
        "--dump-json",
        "--no-warnings",
        "--quiet",
        PBA_YOUTUBE_SHORTS_URL,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError((proc.stderr or "Unable to read PBA Shorts")[:220])

    rows = []
    seen = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        video_id = str(item.get("id") or "").strip()
        title = re.sub(r"\s+", " ", str(item.get("title") or "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id) or video_id in seen:
            continue
        seen.add(video_id)
        upload_date = str(item.get("upload_date") or "")
        published = ""
        if re.fullmatch(r"\d{8}", upload_date):
            try:
                published = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                published = ""
        rows.append({
            "id": video_id,
            "title": title or "PBA Short",
            "channel": "PBA Official",
            "channelId": PBA_YOUTUBE_CHANNEL_ID,
            "watchUrl": "https://www.youtube.com/shorts/" + video_id,
            "embedUrl": "https://www.youtube.com/embed/" + video_id + "?playsinline=1&rel=0",
            "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/hqdefault.jpg",
            "published": published,
            "source": "PBA Official YouTube Shorts",
        })
        if len(rows) >= limit:
            break
    return rows

def update_pba_shorts():
    try:
        official = json.loads(PBA_OFFICIAL_OUT.read_text("utf-8"))
    except Exception:
        official = {}
    previous = list(official.get("shorts") or [])
    try:
        fresh = fetch_pba_youtube_shorts(12)
    except Exception as ex:
        print("PBA shorts", type(ex).__name__, str(ex)[:180])
        fresh = []

    # Never erase a known-good Shorts row because YouTube temporarily blocks a runner.
    if not fresh:
        return len(previous)

    old_compact = json.dumps(previous, sort_keys=True, ensure_ascii=False)
    new_compact = json.dumps(fresh, sort_keys=True, ensure_ascii=False)
    if old_compact != new_compact:
        official["shorts"] = fresh
        official["shortsSource"] = {
            "name": "PBA Official YouTube",
            "channelId": PBA_YOUTUBE_CHANNEL_ID,
            "url": PBA_YOUTUBE_SHORTS_URL,
        }
        official["shortsUpdatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        PBA_OFFICIAL_OUT.write_text(json.dumps(official, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(json.dumps({"pba_shorts": len(fresh)}, ensure_ascii=False))
    return len(fresh)



UAAP_TEAM_NAMES = [
    "Adamson", "Ateneo", "De La Salle", "DLSU", "Far Eastern", "FEU",
    "National University", "NU", "University of the East", "UE",
    "University of the Philippines", "UP", "University of Santo Tomas", "UST",
]

def _uaap_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def _uaap_number(value):
    m = re.search(r"-?\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(m.group(0)) if m else None

def _uaap_article_image(soup, base_url):
    for attrs in (
        {"property":"og:image"},
        {"name":"twitter:image"},
        {"property":"twitter:image"},
    ):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            value = urllib.parse.urljoin(base_url, str(tag.get("content")).strip())
            if value.startswith("http"):
                return value
    img = soup.find("img")
    if img:
        value = img.get("src") or img.get("data-src")
        if value:
            value = urllib.parse.urljoin(base_url, str(value).strip())
            if value.startswith("http"):
                return value
    return ""

def _uaap_published(soup):
    time_tag = soup.find("time")
    if time_tag:
        raw = time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
        if raw:
            try:
                return datetime.fromisoformat(str(raw).replace("Z","+00:00")).isoformat()
            except Exception:
                pass
    text = _uaap_text(soup.get_text(" ", strip=True))
    m = re.search(
        r"Published on\s+(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(20\d{2})(?:,\s+(\d{1,2}):(\d{2})\s*(AM|PM))?",
        text, re.I
    )
    if not m:
        return ""
    day, month, year, hh, mm, ap = m.groups()
    try:
        dt = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
        if hh and mm and ap:
            hour = int(hh)
            if ap.upper()=="PM" and hour < 12: hour += 12
            if ap.upper()=="AM" and hour == 12: hour = 0
            dt = dt.replace(hour=hour, minute=int(mm))
        return dt.replace(tzinfo=PHT).isoformat()
    except Exception:
        return ""

def _uaap_is_mens_basketball(text):
    t = _uaap_text(text).lower()
    if "basketball" not in t:
        return False
    if any(x in t for x in ("women's basketball", "womens basketball", "girls basketball", "boys basketball", "jhs basketball", "junior high school")):
        return False
    return (
        "men's basketball" in t
        or "mens basketball" in t
        or "collegiate men's basketball" in t
        or "collegiate mens basketball" in t
        or ("season 89" in t and any(name.lower() in t for name in UAAP_TEAM_NAMES))
    )

def fetch_uaap_stats():
    result = {"standings": [], "topPlayers": []}
    page = fetch(URLS["uaap_stats"])
    soup = BeautifulSoup(page, "html.parser")

    # Support server-rendered tables from UAAP. If the page later changes its
    # table order, header matching keeps the parser tied to labels, not positions.
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [_uaap_text(x.get_text(" ", strip=True)).lower() for x in rows[0].find_all(["th","td"])]
        if not headers:
            continue

        def col(*names):
            for idx, header in enumerate(headers):
                compact = re.sub(r"[^a-z0-9]+", "", header)
                for name in names:
                    if compact == re.sub(r"[^a-z0-9]+", "", name.lower()):
                        return idx
            return -1

        team_i = col("team", "school", "participant")
        win_i = col("w", "win", "wins")
        loss_i = col("l", "loss", "losses")
        if team_i >= 0 and win_i >= 0 and loss_i >= 0:
            standing_rows = []
            for tr in rows[1:]:
                cells = [_uaap_text(x.get_text(" ", strip=True)) for x in tr.find_all(["td","th"])]
                if max(team_i, win_i, loss_i) >= len(cells):
                    continue
                wins, losses = _uaap_number(cells[win_i]), _uaap_number(cells[loss_i])
                if wins is None or losses is None or not cells[team_i]:
                    continue
                standing_rows.append({"team":cells[team_i],"wins":int(wins),"losses":int(losses)})
            if standing_rows:
                result["standings"] = standing_rows

        player_i = col("player", "name")
        team_i = col("team", "school")
        pts_i = col("pts", "ppg", "points")
        reb_i = col("reb", "rpg", "rebounds")
        ast_i = col("ast", "apg", "assists")
        if player_i >= 0 and any(i >= 0 for i in (pts_i, reb_i, ast_i)):
            players = []
            for tr in rows[1:]:
                cells = [_uaap_text(x.get_text(" ", strip=True)) for x in tr.find_all(["td","th"])]
                if player_i >= len(cells) or not cells[player_i]:
                    continue
                row = {
                    "player": cells[player_i],
                    "team": cells[team_i] if team_i >= 0 and team_i < len(cells) else "",
                    "pts": _uaap_number(cells[pts_i]) if pts_i >= 0 and pts_i < len(cells) else None,
                    "reb": _uaap_number(cells[reb_i]) if reb_i >= 0 and reb_i < len(cells) else None,
                    "ast": _uaap_number(cells[ast_i]) if ast_i >= 0 and ast_i < len(cells) else None,
                }
                players.append(row)
            if players:
                players.sort(key=lambda x: (x.get("pts") is not None, x.get("pts") or -1), reverse=True)
                result["topPlayers"] = players[:8]

    return result


UAAP_TEAM_FULL = {
    "ATENEO":"Ateneo Blue Eagles",
    "ADMU":"Ateneo Blue Eagles",
    "ADU":"Adamson Soaring Falcons",
    "ADAMSON":"Adamson Soaring Falcons",
    "LA SALLE":"De La Salle Green Archers",
    "DLSU":"De La Salle Green Archers",
    "FEU":"FEU Tamaraws",
    "NU":"NU Bulldogs",
    "UE":"UE Red Warriors",
    "UP":"UP Fighting Maroons",
    "UST":"UST Growling Tigers",
}

def _uaap_full_team(value):
    key = _uaap_text(value).upper()
    return UAAP_TEAM_FULL.get(key, _uaap_text(value))

def _uaap_livestats_card(label):
    label = _uaap_text(label)
    m = re.fullmatch(r"(.+?)\s+(\d{1,3})\s+(Final|Live)\s+(.+?)\s+(\d{1,3})", label, re.I)
    if not m:
        return None
    first, first_score, status, second, second_score = m.groups()
    return {
        "first": _uaap_full_team(first),
        "firstScore": int(first_score),
        "second": _uaap_full_team(second),
        "secondScore": int(second_score),
        "status": status.title(),
        "state": "final" if status.lower()=="final" else "in",
    }

def _uaap_boxscore_players(soup, teams):
    out = []
    tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [_uaap_text(x.get_text(" ", strip=True)).upper() for x in rows[0].find_all(["th","td"])]
        compact = [re.sub(r"[^A-Z0-9]+", "", x) for x in headers]
        if "PLAYER" in compact and "PTS" in compact and "REB" in compact and "AST" in compact:
            tables.append((table, compact))
    for table_index, (table, headers) in enumerate(tables[:2]):
        team = teams[table_index] if table_index < len(teams) else ""
        player_i, pts_i, reb_i, ast_i = headers.index("PLAYER"), headers.index("PTS"), headers.index("REB"), headers.index("AST")
        for tr in table.find_all("tr")[1:]:
            cells = [_uaap_text(x.get_text(" ", strip=True)) for x in tr.find_all(["td","th"])]
            if max(player_i, pts_i, reb_i, ast_i) >= len(cells):
                continue
            player = cells[player_i]
            if not player or "TEAM TOTAL" in player.upper() or player.lower() in ("starters","bench","team / coach"):
                continue
            pts, reb, ast = _uaap_number(cells[pts_i]), _uaap_number(cells[reb_i]), _uaap_number(cells[ast_i])
            if pts is None:
                continue
            out.append({
                "player": player,
                "team": team,
                "pts": pts,
                "reb": reb or 0,
                "ast": ast or 0,
            })
    return out

def fetch_uaap_livestats():
    base = URLS["uaap_live_stats"]
    soup = BeautifulSoup(fetch(base), "html.parser")
    games = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(base, str(a.get("href") or "").strip())
        parsed = urllib.parse.urlparse(href)
        query = urllib.parse.parse_qs(parsed.query)
        game_ids = query.get("game_id") or []
        if not game_ids:
            continue
        game_id = str(game_ids[0])
        if game_id in seen:
            continue
        card = _uaap_livestats_card(a.get_text(" ", strip=True))
        if not card:
            continue
        seen.add(game_id)
        card["gameId"] = game_id
        card["url"] = base + "?game_id=" + urllib.parse.quote(game_id)
        games.append(card)

    # Standings are computed from all final game cards currently exposed by the
    # official live-stat tournament page, so one bad third-party table cannot
    # overwrite them.
    records = {}
    for game in games:
        if game.get("state") != "final":
            continue
        a, b = game["first"], game["second"]
        records.setdefault(a, {"team":a,"wins":0,"losses":0})
        records.setdefault(b, {"team":b,"wins":0,"losses":0})
        if game["firstScore"] > game["secondScore"]:
            records[a]["wins"] += 1
            records[b]["losses"] += 1
        elif game["secondScore"] > game["firstScore"]:
            records[b]["wins"] += 1
            records[a]["losses"] += 1
    standings = sorted(records.values(), key=lambda x:(-x["wins"],x["losses"],x["team"]))

    # Build current player leaders from the latest official box scores. This is
    # a live-stats fallback until the UAAP season aggregate stats page exposes
    # stable machine-readable tables.
    aggregates = {}
    detail_games = sorted(
        games,
        key=lambda x:int(x["gameId"]) if str(x["gameId"]).isdigit() else -1,
        reverse=True,
    )[:12]
    for game in detail_games:
        try:
            game_soup = BeautifulSoup(fetch(game["url"]), "html.parser")
            players = _uaap_boxscore_players(game_soup, [game["first"], game["second"]])
        except Exception as ex:
            print("UAAP livestats game", game.get("gameId"), type(ex).__name__, str(ex)[:100])
            continue
        for row in players:
            key = (row["team"], row["player"])
            agg = aggregates.setdefault(key, {
                "player":row["player"],"team":row["team"],"games":0,
                "ptsTotal":0.0,"rebTotal":0.0,"astTotal":0.0,
            })
            agg["games"] += 1
            agg["ptsTotal"] += row["pts"]
            agg["rebTotal"] += row["reb"]
            agg["astTotal"] += row["ast"]

    leaders = []
    for agg in aggregates.values():
        gp = max(1, agg["games"])
        leaders.append({
            "player": agg["player"],
            "team": agg["team"],
            "games": gp,
            "ppg": round(agg["ptsTotal"]/gp, 1),
            "rpg": round(agg["rebTotal"]/gp, 1),
            "apg": round(agg["astTotal"]/gp, 1),
        })
    leaders.sort(key=lambda x:(x["ppg"],x["rpg"],x["apg"]), reverse=True)
    return {"standings":standings,"topPlayers":leaders[:8],"games":games}


def _uaap_listing_links(url, prefix, limit=80):
    soup = BeautifulSoup(fetch(url), "html.parser")
    found, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(url, str(a.get("href") or "").strip())
        parsed = urllib.parse.urlparse(href)
        if parsed.netloc.lower() not in ("uaap.org", "www.uaap.org"):
            continue
        if prefix not in parsed.path:
            continue
        canonical = "https://uaap.org" + parsed.path.rstrip("/")
        if canonical in seen:
            continue
        title = _uaap_text(a.get_text(" ", strip=True))
        if len(title) < 8:
            continue
        seen.add(canonical)
        found.append((title, canonical))
        if len(found) >= limit:
            break
    return found

def fetch_uaap_headlines(limit=6):
    rows = []
    links = _uaap_listing_links(URLS["uaap_articles"], "/posts/articles/", 60)
    for fallback_title, url in links:
        if len(rows) >= limit:
            break
        try:
            soup = BeautifulSoup(fetch(url), "html.parser")
            page_text = _uaap_text(soup.get_text(" ", strip=True))
            if not _uaap_is_mens_basketball(page_text):
                continue
            h1 = soup.find("h1")
            title = _uaap_text(h1.get_text(" ", strip=True) if h1 else fallback_title)
            rows.append({
                "title": title or fallback_title,
                "url": url,
                "image": _uaap_article_image(soup, url),
                "published": _uaap_published(soup),
                "sourceName": "UAAP Official",
            })
        except Exception as ex:
            print("UAAP article", url, type(ex).__name__, str(ex)[:100])
    return rows

def fetch_uaap_photo_gallery(limit=8):
    rows = []
    links = _uaap_listing_links(URLS["uaap_photos"], "/posts/photo_gallery/", 80)
    for title, url in links:
        compact = title.lower()
        if not (
            ("89" in compact and ("bbm" in compact or "basketball" in compact))
            or "season 89" in compact
        ):
            continue
        try:
            soup = BeautifulSoup(fetch(url), "html.parser")
            page_text = _uaap_text(soup.get_text(" ", strip=True))
            if "basketball" not in page_text.lower() and "bbm" not in compact:
                continue
            image = _uaap_article_image(soup, url)
            rows.append({
                "title": title,
                "url": url,
                "image": image,
                "published": _uaap_published(soup),
                "sourceName": "UAAP Official",
            })
            if len(rows) >= limit:
                break
        except Exception:
            continue
    return rows

def fetch_uaap_video_gallery(limit=10):
    rows = []
    soup = BeautifulSoup(fetch(URLS["uaap_videos"]), "html.parser")
    seen = set()
    for a in soup.find_all("a", href=True):
        text = _uaap_text(a.get_text(" ", strip=True))
        lower = text.lower()
        if not text or "basketball" not in lower:
            continue
        if not ("season 89" in lower or "89" in lower):
            continue
        if any(x in lower for x in ("women", "girls", "boys", "jhs", "junior")):
            continue
        href = urllib.parse.urljoin(URLS["uaap_videos"], str(a.get("href") or "").strip())
        if href in seen:
            continue
        seen.add(href)
        img = a.find("img")
        thumb = ""
        if img:
            thumb = img.get("src") or img.get("data-src") or ""
            if thumb:
                thumb = urllib.parse.urljoin(URLS["uaap_videos"], str(thumb))
        rows.append({
            "title": text,
            "url": href,
            "thumbnail": thumb,
            "sourceName": "UAAP Official",
        })
        if len(rows) >= limit:
            break
    return rows

def _uaap_match_game_photo(game, galleries):
    away = _photo_text(game.get("away"))
    home = _photo_text(game.get("home"))
    aliases = {
        "adamson soaring falcons":["adamson","adu"],
        "ateneo blue eagles":["ateneo","admu"],
        "de la salle green archers":["la salle","dlsu"],
        "feu tamaraws":["feu","far eastern"],
        "nu bulldogs":["nu","national university"],
        "ue red warriors":["ue","university of the east"],
        "up fighting maroons":["up","university of the philippines"],
        "ust growling tigers":["ust","santo tomas"],
    }
    def team_hit(team, text):
        options = aliases.get(team, [team])
        return any(x and x in text for x in options)
    for item in galleries:
        text = _photo_text(item.get("title"))
        if team_hit(away, text) and team_hit(home, text) and str(item.get("image") or "").startswith("http"):
            return {
                "eventId": game.get("eventId") or "",
                "date": str(game.get("date") or "")[:10],
                "away": game.get("away") or "",
                "home": game.get("home") or "",
                "image": item.get("image"),
                "credit": "UAAP Official",
                "sourceName": "UAAP Official",
                "sourceUrl": item.get("url") or URLS["uaap_photos"],
            }
    return None

def update_uaap_official(uaap_league):
    try:
        official = json.loads(UAAP_OFFICIAL_OUT.read_text("utf-8"))
    except Exception:
        official = {}

    changed = False

    try:
        stats = fetch_uaap_stats()
    except Exception as ex:
        print("UAAP stats", type(ex).__name__, str(ex)[:180])
        stats = {}

    try:
        livestats = fetch_uaap_livestats()
    except Exception as ex:
        print("UAAP livestats", type(ex).__name__, str(ex)[:180])
        livestats = {}

    standings = stats.get("standings") or livestats.get("standings") or []
    top_players = stats.get("topPlayers") or livestats.get("topPlayers") or []
    if standings:
        official["standings"] = standings
        changed = True
    if top_players:
        official["topPlayers"] = top_players
        official["topPlayersMode"] = "season" if stats.get("topPlayers") else "recent-official-boxscores"
        changed = True
    if livestats.get("games"):
        official["liveStatsGames"] = livestats["games"]
        changed = True

    try:
        headlines = fetch_uaap_headlines(6)
    except Exception as ex:
        print("UAAP headlines", type(ex).__name__, str(ex)[:180])
        headlines = []
    if headlines:
        official["headlines"] = headlines
        changed = True

    try:
        galleries = fetch_uaap_photo_gallery(12)
    except Exception as ex:
        print("UAAP photos", type(ex).__name__, str(ex)[:180])
        galleries = []
    if galleries:
        official["photoGallery"] = galleries
        changed = True

    try:
        videos = fetch_uaap_video_gallery(10)
    except Exception as ex:
        print("UAAP videos", type(ex).__name__, str(ex)[:180])
        videos = []
    if videos:
        official["highlights"] = videos
        changed = True

    games = list((uaap_league or {}).get("games") or [])
    finals = sorted(
        [g for g in games if g.get("state") == "final"],
        key=lambda g: g.get("date", ""),
        reverse=True,
    )[:3]
    previous = list(official.get("previousGamePhotos") or [])
    photos = []
    for game in finals:
        found = _uaap_match_game_photo(game, galleries)
        if found:
            photos.append(found)
            continue
        # Preserve last verified match photo during source outages.
        event_id = str(game.get("eventId") or "")
        prior = next((x for x in previous if event_id and str(x.get("eventId") or "") == event_id), None)
        if prior and str(prior.get("image") or "").startswith("http"):
            photos.append(prior)
    if photos:
        official["previousGamePhotos"] = photos
        changed = True

    official["season"] = "Season 89 Men's Basketball"
    official["sources"] = {
        "stats": URLS["uaap_stats"],
        "liveStats": URLS["uaap_live_stats"],
        "basketball": URLS["uaap_basketball"],
        "articles": URLS["uaap_articles"],
        "photos": URLS["uaap_photos"],
        "videos": URLS["uaap_videos"],
    }
    official["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    UAAP_OFFICIAL_OUT.write_text(json.dumps(official, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "uaap_official": {
            "standings": len(official.get("standings") or []),
            "topPlayers": len(official.get("topPlayers") or []),
            "headlines": len(official.get("headlines") or []),
            "photos": len(official.get("previousGamePhotos") or []),
            "highlights": len(official.get("highlights") or []),
        }
    }, ensure_ascii=False))
    return changed


def parse_uaap():
    xs = lines(URLS["uaap"])
    games, day = [], None
    date_re = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2026(?:\s*\|\s*.*)?$")
    teams = {
        "ADMU":"Ateneo Blue Eagles",
        "ADU":"Adamson Soaring Falcons",
        "DLSU":"De La Salle Green Archers",
        "FEU":"FEU Tamaraws",
        "NU":"NU Bulldogs",
        "UE":"UE Red Warriors",
        "UP":"UP Fighting Maroons",
        "UST":"UST Growling Tigers",
    }
    def team_name(value):
        value = value.strip()
        return teams.get(value.upper(), clean_team(value))

    for i, x in enumerate(xs):
        if x == "Discover More":
            break
        if date_re.match(x):
            day = x
            continue
        if not day:
            continue

        # SkedCheck renders final scores as:
        # TEAM, SCORE, |, SCORE, FINAL, TEAM
        if x.upper() == "FINAL" and i >= 4 and i + 1 < len(xs):
            if xs[i-2] == "|" and re.fullmatch(r"\d{2,3}", xs[i-3]) and re.fullmatch(r"\d{2,3}", xs[i-1]):
                home, away = team_name(xs[i-4]), team_name(xs[i+1])
                hs, as_ = xs[i-3], xs[i-1]
                tm = xs[i+3] if i+3 < len(xs) and re.fullmatch(r"\d{1,2}:\d{2}\s*(AM|PM)", xs[i+3], re.I) else None
                iso = pht_iso_from_month(day, tm)
                games.append({
                    "eventId":"web-uaap-final-"+str(len(games)+1),
                    "date":iso,
                    "displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),
                    "away":away,"home":home,"awayScore":as_,"homeScore":hs,
                    "status":"Final","state":"final",
                    "sourceName":"SkedCheck","sourceUrl":URLS["uaap"]
                })
            continue

        # Upcoming rows render as: TEAM, VS, TIME, TEAM.
        if x.upper() == "VS" and i >= 1 and i + 2 < len(xs):
            tm = xs[i+1]
            if re.fullmatch(r"\d{1,2}:\d{2}\s*(AM|PM)", tm, re.I):
                home, away = team_name(xs[i-1]), team_name(xs[i+2])
                iso = pht_iso_from_month(day, tm)
                games.append({
                    "eventId":"web-uaap-scheduled-"+str(len(games)+1),
                    "date":iso,
                    "displayTime":datetime.fromisoformat(iso).strftime("%b %d · %I:%M %p").replace(" 0"," "),
                    "away":away,"home":home,"awayScore":"—","homeScore":"—",
                    "status":"Scheduled","state":"scheduled",
                    "sourceName":"SkedCheck","sourceUrl":URLS["uaap"]
                })

    games = dedupe_games(games)
    if not games:
        existing = load().get("leagues", {}).get("uaap", {})
        if existing:
            return existing
        raise RuntimeError("No UAAP games parsed")
    scheduled = sorted([g for g in games if g.get("state")=="scheduled"], key=lambda x:x.get("date",""))
    finals = sorted([g for g in games if g.get("state")=="final"], key=lambda x:x.get("date",""), reverse=True)

    # Preserve the last verified standings snapshot until a reliable machine-readable
    # standings source is available in the updater.
    existing = load().get("leagues", {}).get("uaap", {})
    standings = existing.get("standings", []) if isinstance(existing, dict) else []

    return {
        "league":"UAAP",
        "season":"Season 89 Men's Basketball",
        "coverage":"Schedule, final scores and standings",
        "note":"Automatically refreshed from the current UAAP Season 89 public schedule/results page. Live One Sports broadcasts are handled separately by the YouTube live scanner.",
        "sources":[
            {"name":"UAAP Official Stats","url":URLS["uaap_stats"]},
            {"name":"UAAP Official Basketball","url":URLS["uaap_basketball"]},
            {"name":"UAAP Live Stats","url":"https://uaap.livestats.ph/tournaments/uaap-season-89-men-s-basketball"},
            {"name":"SkedCheck Fallback","url":URLS["uaap"]},
            {"name":"One Sports","url":"https://www.youtube.com/@OneSportsPHL"}
        ],
        "standings": standings,
        "games": scheduled[:20] + finals[:30]
    }

def parse_forebet(url, state):
    xs = lines(url)
    games, day = [], None
    i = 0
    while i < len(xs):
        if re.fullmatch(r"\d{2}/\d{2}/2026", xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if state == "final" and i + 2 < len(xs) and re.fullmatch(r"\d{1,3}\s*:\s*\d{1,3}", xs[i+1]):
            a, b = [v.strip() for v in xs[i+1].split(":")]
            iso = pht_iso_from_dmy(day)
            games.append({"eventId":"web-mpbl-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":xs[i+2],"home":xs[i],"awayScore":b,"homeScore":a,"status":"Final","state":"final","sourceName":"Forebet","sourceUrl":url})
            i += 3; continue
        if state == "scheduled" and i + 2 < len(xs) and xs[i+1] == "-":
            iso = pht_iso_from_dmy(day)
            games.append({"eventId":"web-mpbl-scheduled-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d").replace(" 0"," "),"away":xs[i],"home":xs[i+2],"awayScore":"—","homeScore":"—","status":"Scheduled","state":"scheduled","sourceName":"Forebet","sourceUrl":url})
            i += 3; continue
        i += 1
    return games

def parse_mpbl_standings():
    previous = load().get("leagues", {}).get("mpbl", {}).get("standings", {})
    try:
        html = fetch(URLS["mpbl_standings"])
        soup = BeautifulSoup(html, "html.parser")
        groups = {"northDivision": [], "southDivision": []}
        current = None
        for tr in soup.find_all("tr"):
            cells = [re.sub(r"\s+", " ", x.get_text(" ", strip=True)).strip() for x in tr.find_all(["th","td"])]
            if not cells:
                continue
            joined = " ".join(cells).lower()
            if "north division" in joined:
                current = "northDivision"
                continue
            if "south division" in joined:
                current = "southDivision"
                continue
            if current is None:
                prev = tr.find_previous(string=re.compile(r"(North|South) Division", re.I))
                if prev:
                    current = "northDivision" if "north" in str(prev).lower() else "southDivision"
            # Expected row: rank, team, played, wins, losses, points for:against, pct.
            if current and len(cells) >= 6 and re.fullmatch(r"\d{1,2}", cells[0]):
                nums = [x for x in cells[2:] if re.fullmatch(r"\d+", x)]
                if len(nums) >= 3:
                    groups[current].append({
                        "rank": int(cells[0]),
                        "team": cells[1],
                        "played": int(nums[0]),
                        "wins": int(nums[1]),
                        "losses": int(nums[2]),
                    })
        if not groups["northDivision"] or not groups["southDivision"]:
            # Text fallback for layouts that flatten the tables.
            text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
            for key, start_label, end_label in (
                ("northDivision", "North Division", "South Division"),
                ("southDivision", "South Division", "Promotion"),
            ):
                a = text.find(start_label)
                b = text.find(end_label, a + len(start_label)) if a >= 0 else -1
                segment = text[a:b if b > a else len(text)] if a >= 0 else ""
                rows = []
                pat = re.compile(r"(\d{1,2})\s+([A-Za-z][A-Za-z0-9 .'-]+?)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+\d{3,4}:\d{3,4}\s+0\.\d{3}")
                for m in pat.finditer(segment):
                    rows.append({"rank":int(m.group(1)),"team":m.group(2).strip(),"played":int(m.group(3)),"wins":int(m.group(4)),"losses":int(m.group(5))})
                if rows:
                    groups[key] = rows
        if groups["northDivision"] and groups["southDivision"]:
            return groups
    except Exception as ex:
        print("MPBL standings", type(ex).__name__, str(ex)[:160])
    return previous if isinstance(previous, dict) else {}

def parse_mpbl():
    try:
        games = parse_forebet(URLS["mpbl_fixtures"], "scheduled")[:24] + parse_forebet(URLS["mpbl_results"], "final")[:32]
    except Exception:
        games = []
    existing = load().get("leagues", {}).get("mpbl", {})
    standings = parse_mpbl_standings()
    if not games:
        games = existing.get("games", []) if existing else []
    if not games and not standings:
        raise RuntimeError("No MPBL games or standings parsed")
    return {
        "league":"MPBL",
        "season":"2026 Season",
        "coverage":"Upcoming fixtures, recent final scores, and North/South standings",
        "note":"Automatically refreshed from public MPBL fixture/result and standings pages.",
        "sources":[
            {"name":"MPBL Official","url":"https://mpbl.com.ph/"},
            {"name":"Forebet","url":"https://www.forebet.com/en/basketball/philippines/mpbl"},
            {"name":"Live2Sport","url":URLS["mpbl_standings"]}
        ],
        "standings":standings,
        "games":games
    }

def nbl_source_lines():
    # Official Facebook first. A block/login wall must never abort NBL updates.
    for url, name in (
        (URLS["nbl_facebook"], "NBL-Pilipinas Official Facebook"),
        (URLS["nbl_facebook_share"], "NBL-Pilipinas Official Facebook"),
        (URLS["nbl_updates"], "NBL-Pilipinas Facebook mirror"),
    ):
        try:
            xs = lines(url)
            joined = " ".join(xs).upper()
            if len(xs) >= 10 and ("NBL" in joined or "PILIPINAS" in joined):
                return xs, name, url
        except Exception:
            continue
    return [], "NBL-Pilipinas Official Facebook", URLS["nbl_facebook"]

NBL_TEAM_ALIASES = {
    "Batangas Barako - Venom Art": ["BATANGAS BARAKO VENOM ART", "BATANGAS BARAKO", "VENOM ART", "BATANGAS"],
    "CamSur Express": ["CAM SUR EXPRESS", "CAMSUR EXPRESS", "CAM SUR", "CAMSUR"],
    "Manila MLB": ["MANILA MLB", "MANILA"],
    "Nueva Ecija Granary Buffalos": ["NUEVA ECIJA GRANARY BUFFALOS", "GRANARY BUFFALOS", "NUEVA ECIJA"],
    "Pangasinan Asinderos": ["PANGASINAN ASINDEROS", "ASINDEROS", "PANGASINAN"],
    "Quezon City Titans": ["QUEZON CITY TITANS", "QUEZON CITY", "QC TITANS"],
    "Quezon Starhorse": ["QUEZON STARHORSE", "QUEZON STAR HORSE", "STARHORSE", "STAR HORSE"],
    "Taguig City Generals": ["TAGUIG CITY GENERALS", "TAGUIG GENERALS", "TAGUIG"],
    "Tikas Kapampangan": ["TIKAS KAPAMPANGAN", "TIKAS KAPANGAN", "KAPAMPANGAN", "PAMPANGA"],
    "Zamboanga Valientes": ["ZAMBOANGA VALIENTES", "VALIENTES", "ZAMBOANGA"]
}

def canonical_nbl_team(value):
    normalized = normalize_ocr_text(value)
    best = None
    best_len = 0
    for team, aliases in NBL_TEAM_ALIASES.items():
        for alias in [team] + aliases:
            a = normalize_ocr_text(alias)
            if not a:
                continue
            if normalized == a or a in normalized or normalized in a:
                if len(a) > best_len:
                    best = team
                    best_len = len(a)
    return best or str(value or "").strip()

def nbl_verified_seed_games():
    # High-confidence 2026 results verified from NBL-Pilipinas Facebook
    # score graphics/posts or official team/local-government Facebook posts.
    # These persist until a newer equally verified source supersedes them.
    return [
        {
            "eventId": "verified-nbl-20260920-tikas-batangas",
            "date": "2026-09-20T18:00:00+08:00",
            "displayTime": "Sep 20 · Final",
            "away": "Batangas Barako - Venom Art",
            "home": "Tikas Kapampangan",
            "awayScore": "92",
            "homeScore": "110",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official Facebook",
            "sourceUrl": "https://www.facebook.com/nblpilipinas/posts/glutamax-men-best-player-of-the-game-renzo-victoria-made-a-huge-impact-off-the-b/1499767768850060/",
        },
        {
            "eventId": "verified-nbl-20260920-camsur-nueva-ecija",
            "date": "2026-09-20T18:00:00+08:00",
            "displayTime": "Sep 20 · Final",
            "away": "CamSur Express",
            "home": "Nueva Ecija Granary Buffalos",
            "awayScore": "154",
            "homeScore": "121",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official Facebook",
            "sourceUrl": "https://www.facebook.com/nblpilipinas/posts/glutamax-men-best-player-of-the-game-medwin-ariate-was-as-efficient-as-he-can-be/1499661952193975/",
        },
        {
            "eventId": "verified-nbl-20260918-batangas-zamboanga",
            "date": "2026-09-18T18:00:00+08:00",
            "displayTime": "Sep 18 · Final",
            "away": "Zamboanga Valientes",
            "home": "Batangas Barako - Venom Art",
            "awayScore": "90",
            "homeScore": "92",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official Facebook",
            "sourceUrl": "https://www.facebook.com/nblpilipinas/posts/wow-what-an-ending-glutamax-men-best-player-of-the-game-jem-carlos-de-ocampos-of/1498111535682350/",
        },
        {
            "eventId": "verified-nbl-20260918-qc-manila",
            "date": "2026-09-18T18:00:00+08:00",
            "displayTime": "Sep 18 · Final",
            "away": "Manila MLB",
            "home": "Quezon City Titans",
            "awayScore": "103",
            "homeScore": "113",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official Facebook",
            "sourceUrl": "https://www.facebook.com/nblpilipinas/posts/glutamax-men-best-player-of-the-game-angelo-canetes-versatility-on-both-ends-of-/1497915645701939/",
        },
        {
            "eventId": "verified-nbl-20260913-taguig-tikas",
            "date": "2026-09-13T18:00:00+08:00",
            "displayTime": "Sep 13 · Final",
            "away": "Tikas Kapampangan",
            "home": "Taguig City Generals",
            "awayScore": "84",
            "homeScore": "86",
            "status": "Final",
            "state": "final",
            "sourceName": "Taguig City Official Facebook",
            "sourceUrl": "https://www.facebook.com/taguigcity/posts/1531288389037526/",
        },
        {
            "eventId": "verified-nbl-20260830-starhorse-tikas",
            "date": "2026-08-30T18:00:00+08:00",
            "displayTime": "Aug 30 · Final",
            "away": "Tikas Kapampangan",
            "home": "Quezon Starhorse",
            "awayScore": "84",
            "homeScore": "87",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas public update",
            "sourceUrl": URLS["nbl_updates"],
        },
        {
            "eventId": "verified-nbl-20260817-pangasinan-nueva-ecija",
            "date": "2026-08-17T18:00:00+08:00",
            "displayTime": "Aug 17 · Final",
            "away": "Nueva Ecija Granary Buffalos",
            "home": "Pangasinan Asinderos",
            "awayScore": "110",
            "homeScore": "129",
            "status": "Final",
            "state": "final",
            "sourceName": "Province of Pangasinan",
            "sourceUrl": "https://www.pangasinan.gov.ph/asinderos-crush-granary-buffalos-129-110-in-nbl-pilipinas-governors-cup/",
        },
    ]

def score_is_known(value):
    return bool(re.fullmatch(r"\d{1,3}", str(value or "").strip()))

def nbl_game_quality(game):
    score = int(score_is_known(game.get("homeScore"))) + int(score_is_known(game.get("awayScore")))
    source = str(game.get("sourceName") or "").lower()
    verified = 2 if ("province of pangasinan" in source or "public update" in source or "facebook image" in source) else 0
    status = 1 if str(game.get("status") or "").strip() else 0
    return score * 10 + verified + status

def dedupe_nbl_games(games):
    # Keep the most informative record for a matchup/day. In particular, a
    # blank-score YouTube replay must never replace a verified scored final.
    chosen = {}
    order = []
    for game in games:
        game = dict(game)
        game["home"] = canonical_nbl_team(game.get("home"))
        game["away"] = canonical_nbl_team(game.get("away"))
        teams = tuple(sorted([normalize_ocr_text(game.get("home")), normalize_ocr_text(game.get("away"))]))
        day = str(game.get("date") or "")[:10]
        key = (teams, day)
        if key not in chosen:
            chosen[key] = game
            order.append(key)
        elif nbl_game_quality(game) > nbl_game_quality(chosen[key]):
            chosen[key] = game
    return [chosen[key] for key in order]

def parse_nbl_official_site():
    # Genius Sports is the league's published official website. Some deployments
    # render data client-side; if usable game rows are present in HTML, collect
    # them. Otherwise log a compact diagnostic and fall back to verified sources.
    try:
        html = fetch(URLS["nbl_official"])
    except Exception as ex:
        print("NBL official site unavailable", type(ex).__name__, str(ex)[:120])
        return []
    soup = BeautifulSoup(html, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    print("NBL official site fetched", len(html), "bytes", "text", text[:180])
    games = []
    # Conservative parser for explicit date + team + score rows only.
    date_pat = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+2026"
    for dm in re.finditer(date_pat, text, re.I):
        window = text[dm.start():dm.start()+700]
        found = []
        for team, aliases in NBL_TEAM_ALIASES.items():
            pos = min([window.upper().find(a) for a in aliases if window.upper().find(a) >= 0] or [99999])
            if pos < 99999:
                found.append((pos, team))
        found.sort()
        if len(found) < 2:
            continue
        score_match = re.search(r"\b(\d{2,3})\s*[-–:]\s*(\d{2,3})\b", window)
        if not score_match:
            continue
        dt = datetime.strptime(f"{dm.group(1)} {dm.group(2)} 2026", "%B %d %Y").replace(hour=18, tzinfo=PHT)
        home, away = found[0][1], found[1][1]
        a, b = score_match.groups()
        games.append({
            "eventId": "official-nbl-" + dt.strftime("%Y%m%d") + "-" + str(len(games)+1),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": b,
            "homeScore": a,
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official",
            "sourceUrl": URLS["nbl_official"],
        })
    return games

def normalize_ocr_text(value):
    value = re.sub(r"[^A-Z0-9 ]+", " ", str(value or "").upper())
    return re.sub(r"\s+", " ", value).strip()

def teams_in_ocr(text):
    normalized = normalize_ocr_text(text)
    found = []
    for team, aliases in NBL_TEAM_ALIASES.items():
        for alias in aliases:
            if normalize_ocr_text(alias) in normalized:
                found.append(team)
                break
    return found

def nbl_image_candidates(limit=18):
    html = fetch(URLS["nbl_updates"])
    soup = BeautifulSoup(html, "html.parser")
    urls = []

    def add_url(value):
        if not value:
            return
        value = value.strip()
        if value.startswith("//"):
            value = "https:" + value
        elif value.startswith("/"):
            value = urllib.parse.urljoin(URLS["nbl_updates"], value)
        if not re.search(r"https?://img\d*\.findglocal\.com/.+\.(?:jpe?g|png|webp)(?:\?.*)?$", value, re.I):
            return
        if value not in urls:
            urls.append(value)

    for img in soup.find_all("img"):
        add_url(img.get("src"))
        add_url(img.get("data-src"))
        srcset = img.get("srcset") or ""
        for part in srcset.split(","):
            add_url(part.strip().split(" ")[0] if part.strip() else "")
    for a in soup.find_all("a", href=True):
        add_url(a.get("href"))

    return urls[:limit]

def download_image(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read(8 * 1024 * 1024)
    image = Image.open(io.BytesIO(data)).convert("RGB")
    if max(image.size) < 1800:
        scale = min(3, max(1, 1800 // max(image.size)))
        if scale > 1:
            image = image.resize((image.width * scale, image.height * scale))
    gray = ImageOps.grayscale(image)
    return ImageOps.autocontrast(gray)

def ocr_image(url):
    image = download_image(url)
    return pytesseract.image_to_string(image, config="--psm 6")

def ocr_date_time(text):
    upper = text.upper()
    now = datetime.now(PHT)
    date_value = None

    m = re.search(r"\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2})(?:,\s*(2026))?\b", upper)
    if m:
        year = int(m.group(3) or now.year)
        date_value = datetime.strptime(f"{m.group(1)} {m.group(2)} {year}", "%B %d %Y")
    else:
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](2026)\b", upper)
        if m:
            month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            date_value = datetime(year, month, day)
        elif "TODAY" in upper:
            date_value = now.replace(tzinfo=None)

    if not date_value:
        return None

    tm = re.search(r"\b(\d{1,2}):(\d{2})\s*(AM|PM)\b", upper)
    if tm:
        hour, minute = int(tm.group(1)), int(tm.group(2))
        if tm.group(3) == "PM" and hour < 12:
            hour += 12
        if tm.group(3) == "AM" and hour == 12:
            hour = 0
        date_value = date_value.replace(hour=hour, minute=minute)
    else:
        date_value = date_value.replace(hour=12, minute=0)

    return date_value.replace(tzinfo=PHT)

def score_near_team(ocr_lines, team):
    aliases = NBL_TEAM_ALIASES.get(team, [team])
    normalized_aliases = [normalize_ocr_text(a) for a in aliases]
    for index, line in enumerate(ocr_lines):
        normalized = normalize_ocr_text(line)
        if not any(alias in normalized for alias in normalized_aliases):
            continue
        for offset in (0, 1, -1, 2):
            pos = index + offset
            if pos < 0 or pos >= len(ocr_lines):
                continue
            nums = [int(x) for x in re.findall(r"\b(\d{2,3})\b", ocr_lines[pos])]
            nums = [x for x in nums if 40 <= x <= 200]
            if nums:
                return str(nums[-1])
    return None

def image_game_records():
    games = []
    scanned = 0
    matched = 0

    for url in nbl_image_candidates():
        try:
            text = ocr_image(url)
        except Exception:
            continue

        scanned += 1
        upper = text.upper()
        teams = teams_in_ocr(text)
        if len(teams) < 2:
            continue

        dt = ocr_date_time(text)
        lines_ocr = [x.strip() for x in text.splitlines() if x.strip()]
        is_final = bool(re.search(r"\b(FINAL|FINAL SCORE|FULL TIME)\b", upper))
        is_schedule = bool(re.search(r"\b(SCHEDULE|GAME ?DAY|GAMEDAY|UPCOMING|TIP ?OFF|MATCHUP|VS\.?)\b", upper))

        if is_final:
            home, away = teams[0], teams[1]
            home_score = score_near_team(lines_ocr, home)
            away_score = score_near_team(lines_ocr, away)
            if not home_score or not away_score or home_score == away_score:
                continue
            if not dt:
                dt = datetime.now(PHT).replace(hour=12, minute=0, second=0, microsecond=0)
            games.append({
                "eventId": "ocr-nbl-final-" + str(len(games) + 1),
                "date": dt.isoformat(),
                "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
                "away": away,
                "home": home,
                "awayScore": away_score,
                "homeScore": home_score,
                "status": "Final",
                "state": "final",
                "sourceName": "NBL-Pilipinas Facebook image",
                "sourceUrl": URLS["nbl_facebook"]
            })
            matched += 1
            continue

        if is_schedule and dt:
            # A schedule graphic may contain several team pairs. Pair teams in
            # reading order; only create records when the graphic includes a date.
            for i in range(0, len(teams) - 1, 2):
                home, away = teams[i], teams[i + 1]
                games.append({
                    "eventId": "ocr-nbl-scheduled-" + str(len(games) + 1),
                    "date": dt.isoformat(),
                    "displayTime": dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
                    "away": away,
                    "home": home,
                    "awayScore": "—",
                    "homeScore": "—",
                    "status": "Scheduled",
                    "state": "scheduled",
                    "sourceName": "NBL-Pilipinas Facebook image",
                    "sourceUrl": URLS["nbl_facebook"]
                })
                matched += 1

    return games, {"images_scanned": scanned, "images_matched": matched}

def dedupe_games(games):
    out = []
    seen = set()
    for game in games:
        teams = tuple(sorted([normalize_ocr_text(game.get("home")), normalize_ocr_text(game.get("away"))]))
        day = str(game.get("date") or "")[:10]
        key = (teams, day, game.get("state"))
        if key in seen:
            continue
        seen.add(key)
        out.append(game)
    return out

def nbl_youtube_public_metadata(video_id):
    if not video_id:
        return {}
    url = "https://www.youtube.com/watch?v=" + urllib.parse.quote(video_id)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=8) as response:
            page = response.read(2 * 1024 * 1024).decode("utf-8", errors="replace")
    except Exception:
        return {"watchUrl": url}
    title = ""
    m = re.search(r'<meta\s+name="title"\s+content="([^"]*)"', page, re.I)
    if not m:
        m = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', page, re.I)
    if m:
        title = html.unescape(m.group(1)).strip()
    description = ""
    dm = re.search(r'"shortDescription":"((?:\\.|[^"\\])*)"', page)
    if dm:
        try:
            description = json.loads('"' + dm.group(1) + '"')
        except Exception:
            description = ""
    if not description:
        dm = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', page, re.I)
        if dm:
            description = html.unescape(dm.group(1)).strip()
    return {"title": title, "description": description, "watchUrl": url}

def nbl_youtube_venue(description, matchup=""):
    lines_ = [re.sub(r"\s+", " ", x).strip() for x in str(description or "").splitlines() if re.sub(r"\s+", " ", x).strip()]
    skip = ("NBL GOVERNOR", "NBL-PILIPINAS", "#NBL", "HTTP")
    matchup_norm = normalize_ocr_text(matchup)
    for line in lines_:
        upper = line.upper()
        if any(token in upper for token in skip):
            continue
        if re.search(r"\b2026\b", line) and re.search(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)", upper):
            continue
        if matchup_norm and normalize_ocr_text(line) == matchup_norm:
            continue
        if re.search(r"\b(?:GYM|ARENA|STADIUM|CONVENTION|SPORTS COMPLEX|COLISEUM|MEMORIAL)\b", upper):
            return line
    return ""

def parse_nbl_youtube_feed():
    games = []
    try:
        xml = fetch(URLS["nbl_youtube_feed"])
    except Exception:
        return games

    soup = BeautifulSoup(xml, "xml")
    for entry in soup.find_all("entry")[:15]:
        feed_title = entry.title.get_text(" ", strip=True) if entry.title else ""
        video_tag = entry.find("videoId")
        video_id = video_tag.get_text(strip=True) if video_tag else ""
        link_tag = entry.find("link", href=True)
        fallback_link = link_tag.get("href") if link_tag else ""
        if not video_id:
            vm = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", fallback_link or "")
            video_id = vm.group(1) if vm else ""
        desc_tag = entry.find("description")
        feed_description = desc_tag.get_text("\n", strip=True) if desc_tag else ""
        metadata = {} if feed_title else nbl_youtube_public_metadata(video_id)
        title = feed_title or metadata.get("title") or ""
        link = ("https://www.youtube.com/watch?v=" + video_id) if video_id else (fallback_link or "https://www.youtube.com/@nblpilipinas")

        m = re.search(
            r"NBL\s+Governor'?s\s+Cup\s+2026\s*\|\s*"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+(\d{1,2}),*\s*2026\s*\|\s*(.+?)\s+vs\.?\s+(.+)$",
            title,
            re.I
        )
        if not m:
            continue

        dt = datetime.strptime(f"{m.group(1)} {m.group(2)} 2026", "%B %d %Y").replace(hour=18, tzinfo=PHT)
        home_raw = m.group(3).strip()
        away_raw = m.group(4).strip()
        home = canonical_nbl_team(home_raw)
        away = canonical_nbl_team(away_raw)
        matchup = home_raw + " vs " + away_raw
        venue = nbl_youtube_venue(feed_description or metadata.get("description"), matchup)
        now = datetime.now(PHT)
        is_past = dt <= now
        status = "Replay available" if is_past else "Scheduled"
        if venue:
            status += " · " + venue

        games.append({
            "eventId": "yt-nbl-" + (video_id or dt.strftime("%Y%m%d") + "-" + str(len(games)+1)),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": "—",
            "homeScore": "—",
            "status": status,
            "state": "final" if is_past else "scheduled",
            "location": venue,
            "sourceName": "NBL-Pilipinas YouTube",
            "sourceUrl": link
        })
    return games

def parse_nbl():
    xs, score_source_name, score_source_url = nbl_source_lines()
    games, day, pair = [], None, []
    known_aliases = [normalize_ocr_text(a) for values in NBL_TEAM_ALIASES.values() for a in values]

    for x in xs:
        if re.fullmatch(r"\d{2}/\d{2}/2026", x):
            day, pair = x, []
            continue
        m = re.fullmatch(r"(.{3,60}?)\s+(\d{2,3})", x)
        if day and m:
            team = m.group(1).strip()
            upper = normalize_ocr_text(team)
            if any(alias in upper or upper in alias for alias in known_aliases):
                pair.append((team, m.group(2)))
                if len(pair) == 2:
                    iso = pht_iso_from_dmy(day)
                    games.append({"eventId":"web-nbl-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":pair[1][0],"home":pair[0][0],"awayScore":pair[1][1],"homeScore":pair[0][1],"status":"Final","state":"final","sourceName":score_source_name,"sourceUrl":score_source_url})
                    pair = []

    image_meta = {"images_scanned": 0, "images_matched": 0, "facebook_blocked": False}
    try:
        image_games, image_meta = image_game_records()
        games.extend(image_games)
    except Exception as image_error:
        image_meta = {"images_scanned": 0, "images_matched": 0, "facebook_blocked": True, "error": str(image_error)[:160]}

    # Prefer the league's official Genius Sports site when it exposes usable rows.
    games.extend(parse_nbl_official_site())

    # Always retain high-confidence scored results; this also protects against
    # a temporary source outage replacing scores with blank replay metadata.
    games.extend(nbl_verified_seed_games())
    existing_nbl = load().get("leagues", {}).get("nbl", {})
    games.extend([
        g for g in existing_nbl.get("games", [])
        if g.get("state") == "final"
        and score_is_known(g.get("homeScore"))
        and score_is_known(g.get("awayScore"))
    ])

    # Official NBL YouTube feed remains usable without an API key and keeps
    # current matchups available even when Facebook blocks GitHub Actions.
    games.extend(parse_nbl_youtube_feed())

    broadcast = []
    try:
        tx = lines(URLS["tap"])
        current = None
        pending_time = None
        date_re = re.compile(
            r"^(September|October|November|December)\s+\d{1,2},\s+2026(?:\s*\|\s*[A-Za-z]+)?$",
            re.I
        )
        time_re = re.compile(r"^(\d{1,2}:\d{2}\s*(?:AM|PM))(?:\s*\|.*)?$", re.I)
        for x in tx:
            if date_re.fullmatch(x):
                current = re.sub(r"\s*\|\s*[A-Za-z]+$", "", x).strip()
                pending_time = None
                continue
            tm = time_re.match(x)
            if tm:
                pending_time = tm.group(1).upper()
                # Some layouts keep the program on the same rendered text line.
                if current and "NBL PILIPINAS" in x.upper():
                    broadcast.append({
                        "date": datetime.strptime(current, "%B %d, %Y").strftime("%Y-%m-%d"),
                        "time": pending_time,
                        "title": "NBL Pilipinas Governor's Cup 2026",
                        "source": "Tap Sports"
                    })
                    pending_time = None
                continue
            if current and pending_time and "NBL PILIPINAS" in x.upper():
                broadcast.append({
                    "date": datetime.strptime(current, "%B %d, %Y").strftime("%Y-%m-%d"),
                    "time": pending_time,
                    "title": re.sub(r"\s+", " ", x).strip(),
                    "source": "Tap Sports"
                })
                pending_time = None
        # Deduplicate repeated page fragments while preserving order.
        seen_broadcast = set()
        broadcast = [
            b for b in broadcast
            if not ((b["date"], b["time"], b.get("title", "")) in seen_broadcast)
            and not seen_broadcast.add((b["date"], b["time"], b.get("title", "")))
        ]
    except Exception as ex:
        print("Tap Sports NBL schedule", type(ex).__name__, str(ex)[:120])


    games = dedupe_nbl_games(games)
    scheduled = sorted([g for g in games if g.get("state") == "scheduled"], key=lambda x: x.get("date", ""))
    finals = sorted([g for g in games if g.get("state") == "final"], key=lambda x: x.get("date", ""), reverse=True)
    games = scheduled[:12] + finals[:30]
    if not games and not broadcast:
        existing = load().get("leagues", {}).get("nbl", {})
        if existing:
            existing["image_scan"] = image_meta
            existing["note"] = "The latest automated scan found no new high-confidence NBL Facebook score/schedule graphics, so the last verified NBL data was preserved."
            return existing
        raise RuntimeError("No NBL data parsed")

    return {
        "league":"NBL-Pilipinas",
        "season":"2026 Governor's Cup",
        "coverage":"Official site, verified public scores, YouTube matchups and broadcast schedule",
        "note":"IMG prioritizes the official NBL-Pilipinas site and verified scored results, preserves confirmed scores through source outages, and uses the official YouTube feed for current matchups when Facebook blocks automated access.",
        "sources":[
            {"name":"NBL-Pilipinas Official","url":URLS["nbl_official"]},
            {"name":"NBL-Pilipinas Official Facebook","url":URLS["nbl_facebook"]},
            {"name":"NBL-Pilipinas Facebook share link","url":URLS["nbl_facebook_share"]},
            {"name":"Facebook-image mirror","url":URLS["nbl_updates"]},
            {"name":"NBL-Pilipinas YouTube","url":"https://www.youtube.com/channel/UCJDBLldRGVJPEvyjJdSHefw"},
            {"name":"Tap Sports","url":URLS["tap"]}
        ],
        "image_scan": image_meta,
        "broadcast":broadcast[:20],
        "games":games
    }


NBL_AUS_TEAMS = {
    "MEL": "Melbourne United",
    "ADL": "Adelaide 36ers",
    "PER": "Perth Wildcats",
    "SEM": "South East Melbourne Phoenix",
    "NZL": "New Zealand Breakers",
    "ILL": "Illawarra Hawks",
    "SYD": "Sydney Kings",
    "CNS": "Cairns Taipans",
    "TAS": "Tasmania JackJumpers",
    "BRI": "Brisbane Bullets",
}

def parse_nbl_australia():
    xs = lines(URLS["nblaus"])
    text = " ".join(xs)
    # Official NBL homepage publishes compact rows such as:
    # RD 1 Sat, Sep 19 7:30 pm AEST MEL 95 ADL 97
    pattern = re.compile(
        r"RD\s+\d+\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"
        r"(\d{1,2}):(\d{2})\s*(am|pm)\s+(?:AEST|AEDT)\s+"
        r"([A-Z]{3})(?:\s+(\d{2,3}))?\s+([A-Z]{3})(?:\s+(\d{2,3}))?",
        re.I,
    )
    games = []
    for m in pattern.finditer(text):
        mon, day, hh, mm, ap, a_code, a_score, b_code, b_score = m.groups()
        a_code, b_code = a_code.upper(), b_code.upper()
        if a_code not in NBL_AUS_TEAMS or b_code not in NBL_AUS_TEAMS:
            continue
        dt = datetime.strptime(f"{mon} {day} 2026 {hh}:{mm} {ap.upper()}", "%b %d %Y %I:%M %p")
        # NBL's published national schedule is displayed in AEST/AEDT. September
        # dates here are AEST (+10); the website shows the supplied displayTime.
        dt = dt.replace(tzinfo=timezone(timedelta(hours=10)))
        final = bool(a_score and b_score)
        games.append({
            "eventId": "web-nblaus-" + dt.strftime("%Y%m%d%H%M") + "-" + a_code + "-" + b_code,
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · Final" if final else "%b %d · %I:%M %p").replace(" 0", " "),
            "away": NBL_AUS_TEAMS[b_code],
            "home": NBL_AUS_TEAMS[a_code],
            "awayScore": b_score or "—",
            "homeScore": a_score or "—",
            "status": "Final" if final else "Scheduled",
            "state": "final" if final else "scheduled",
            "sourceName": "NBL Australia",
            "sourceUrl": "https://www.nbl.com.au/schedule",
        })
    if not games:
        existing = load().get("leagues", {}).get("nblaus", {})
        if existing:
            return existing
        raise RuntimeError("No NBL Australia games parsed")
    return {
        "league": "NBL Australia",
        "season": "2026-27 NBL27",
        "coverage": "Official NBL schedule and results",
        "note": "Automatically refreshed from the official NBL Australia schedule/results pages.",
        "sources": [
            {"name": "NBL Australia Official", "url": "https://www.nbl.com.au/"},
            {"name": "NBL Schedule", "url": "https://schedule.nbl.com.au/nbl"},
        ],
        "games": dedupe_games(games)[:30],
    }

VBA_TEAMS = [
    "Hanoi Buffaloes",
    "Saigon Heat",
    "Nhatrang Dolphins",
    "Nha Trang Dolphins",
    "Ho Chi Minh City Wings",
    "Can Tho Catfish",
    "Cantho Catfish",
    "Da Nang Dragons",
]

def parse_vba_results_from(url):
    xs = lines(url)
    games = []
    day = None
    i = 0
    while i < len(xs):
        if re.fullmatch(r"\d{2}/\d{2}/2026", xs[i]):
            day = xs[i]
            i += 1
            continue
        if day and i + 2 < len(xs) and re.fullmatch(r"\d{1,3}\s*:\s*\d{1,3}", xs[i+1]):
            home, away = xs[i].strip(), xs[i+2].strip()
            if any(t.lower() in home.lower() for t in VBA_TEAMS) and any(t.lower() in away.lower() for t in VBA_TEAMS):
                hs, as_ = [v.strip() for v in xs[i+1].split(":")]
                dt = datetime.strptime(day, "%d/%m/%Y").replace(hour=19, tzinfo=timezone(timedelta(hours=7)))
                games.append({
                    "eventId": "web-vba-final-" + dt.strftime("%Y%m%d") + "-" + str(len(games)+1),
                    "date": dt.isoformat(),
                    "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
                    "away": away,
                    "home": home,
                    "awayScore": as_,
                    "homeScore": hs,
                    "status": "Final",
                    "state": "final",
                    "sourceName": "VBA results",
                    "sourceUrl": url,
                })
                i += 3
                continue
        i += 1
    return games

def parse_vba_ticket_fixtures():
    try:
        xs = lines(URLS["vba_ticket"])
    except Exception:
        return []
    text = " ".join(xs)
    games = []
    pattern = re.compile(
        r"(Saigon Heat)\s+vs\s+(Hanoi Buffaloes)\s+(\d{1,2}):(\d{2})\s+(\d{2}/\d{2}/2026)",
        re.I,
    )
    for m in pattern.finditer(text):
        home, away, hh, mm, day = m.groups()
        dt = datetime.strptime(day + f" {hh}:{mm}", "%d/%m/%Y %H:%M").replace(tzinfo=timezone(timedelta(hours=7)))
        games.append({
            "eventId": "web-vba-scheduled-" + dt.strftime("%Y%m%d%H%M"),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": "—",
            "homeScore": "—",
            "status": "Scheduled",
            "state": "scheduled",
            "sourceName": "VBA Ticket",
            "sourceUrl": URLS["vba_ticket"],
        })
    return games

def parse_vba():
    games = []
    # Public result mirrors are used because vba.vn renders fixtures dynamically.
    for url in (URLS["vba_results"], URLS["vba_betexplorer"]):
        try:
            parsed = parse_vba_results_from(url)
            if parsed:
                games.extend(parsed[:20])
                break
        except Exception:
            continue
    games.extend(parse_vba_ticket_fixtures())

    # If a public results mirror blocks the runner, keep the last verified
    # final scores while still accepting newly parsed official ticket fixtures.
    existing = load().get("leagues", {}).get("vba", {})
    if existing:
        games.extend([
            g for g in existing.get("games", [])
            if g.get("state") == "final"
        ])

    games = dedupe_games(games)
    if not games:
        if existing:
            return existing
        raise RuntimeError("No VBA games parsed")

    games = sorted(games, key=lambda x: x.get("date", ""), reverse=True)
    scheduled = sorted([g for g in games if g.get("state") == "scheduled"], key=lambda x: x.get("date", ""))
    finals = sorted([g for g in games if g.get("state") == "final"], key=lambda x: x.get("date", ""), reverse=True)
    return {
        "league": "VBA",
        "season": "2026 Season",
        "coverage": "2026 VBA Finals fixtures and recent results",
        "note": "Automatically refreshed from public VBA schedule and results sources.",
        "sources": [
            {"name": "VBA Official", "url": "https://vba.vn/fixtures"},
            {"name": "VBA Ticket", "url": URLS["vba_ticket"]},
            {"name": "Forebet Results", "url": URLS["vba_results"]},
        ],
        "games": (scheduled[:10] + finals[:20]),
    }

def main():
    data = load()
    data.setdefault("leagues", {})
    errors = {}
    for key, fn in [("pba", parse_pba), ("uaap", parse_uaap), ("mpbl", parse_mpbl), ("nbl", parse_nbl), ("nblaus", parse_nbl_australia), ("vba", parse_vba)]:
        try:
            fresh = fn()
            if fresh.get("games") or fresh.get("broadcast"):
                data["leagues"][key] = fresh
        except Exception as e:
            errors[key] = str(e)
    try:
        update_uaap_official(data["leagues"].get("uaap", {}))
    except Exception as e:
        errors["uaap_official"] = str(e)
    try:
        update_pba_previous_game_photos(data["leagues"].get("pba", {}))
    except Exception as e:
        errors["pba_photos"] = str(e)
    try:
        update_pba_official_news()
    except Exception as e:
        errors["pba_news"] = str(e)
    try:
        update_pba_shorts()
    except Exception as e:
        errors["pba_shorts"] = str(e)
    data["updated_at"] = datetime.now(PHT).isoformat(timespec="seconds")
    data["refresh_minutes"] = 30
    data["errors"] = errors
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"updated_at":data["updated_at"],"errors":errors,"counts":{k:len(v.get("games",[])) for k,v in data["leagues"].items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
