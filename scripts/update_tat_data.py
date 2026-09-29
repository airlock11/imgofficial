from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "tat-official.json"
ASSETS_PATH = ROOT / "tat-assets.json"
NEWS_DIR = ROOT / "assets" / "tat" / "news"
HIGHLIGHTS_DIR = ROOT / "assets" / "tat" / "highlights"
NEWS_DIR.mkdir(parents=True, exist_ok=True)
HIGHLIGHTS_DIR.mkdir(parents=True, exist_ok=True)

TAT_URL = "https://www.theasiantournament.com/"
TAT_TEAMS_URL = urljoin(TAT_URL, "all-teams")
TAT_NEWS_URL = urljoin(TAT_URL, "news")
SOFASCORE_TOURNAMENT_ID = 31390
SOFASCORE_BASE = "https://api.sofascore.com/api/v1"
RAW_TAT_BASE = "https://raw.githubusercontent.com/airlock11/imgofficial/tat-data"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
MANILA = ZoneInfo("Asia/Manila")

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "IMG-Sports-Data/1.0 (+https://www.imgofficial.com/)",
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    }
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone(MANILA).isoformat(timespec="seconds")


def parse_game_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MANILA)
        return dt.astimezone(MANILA)
    except Exception:
        return None


def schedule_summary(data):
    now = datetime.now(timezone.utc).astimezone(MANILA)
    today = now.date()
    today_games = []
    future = []
    for game in data.get("games") or []:
        dt = parse_game_datetime(game.get("date"))
        if not dt:
            continue
        if dt.date() == today:
            today_games.append(game)
        if dt > now and str(game.get("state") or "").lower() == "scheduled":
            future.append(dt)
    return {
        "mode": "game-day" if today_games else "idle",
        "gameDay": bool(today_games),
        "todayGameCount": len(today_games),
        "todayGames": [str(x.get("eventId") or "") for x in today_games if x.get("eventId")],
        "nextGameAt": min(future).isoformat(timespec="seconds") if future else "",
    }


def get_json(url: str, *, timeout: int = 25):
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_text(url: str, *, timeout: int = 25) -> str:
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def local_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return deepcopy(default)


def prior_remote_data():
    try:
        data = get_json(f"{RAW_TAT_BASE}/tat-official.json?ts={int(datetime.now().timestamp())}", timeout=12)
        return data if isinstance(data, dict) else None
    except Exception as ex:
        print("Previous tat-data unavailable:", ex)
        return None


def raw_asset_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return f"{RAW_TAT_BASE}/{rel}"


def safe_slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return value[:80] or "item"


def download_image(url: str, directory: Path, basename: str) -> str:
    if not url:
        return ""
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.content
        if len(data) < 3500:
            return ""
        content_type = (r.headers.get("content-type") or "").lower()
        parsed = urlparse(r.url)
        ext = Path(parsed.path).suffix.lower()
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        path = directory / f"{safe_slug(basename)}{ext}"
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
        return raw_asset_url(path)
    except Exception as ex:
        print("Image download failed:", url, ex)
        return ""


def choose_season(seasons):
    if not seasons:
        return None
    preferred = [
        x
        for x in seasons
        if "2026" in str(x.get("name", "")) or str(x.get("year", "")) == "2026"
    ]
    pool = preferred or seasons
    return sorted(pool, key=lambda x: int(x.get("id") or 0), reverse=True)[0]


def score_value(score):
    if not isinstance(score, dict):
        return "—"
    for key in ("current", "display", "normaltime", "period4"):
        value = score.get(key)
        if value is not None:
            return str(value)
    return "—"


def sofa_state(status):
    stype = str((status or {}).get("type") or "").lower()
    description = str((status or {}).get("description") or "")
    if stype in {"inprogress", "live"}:
        return "live", description or "Live"
    if stype in {"finished"}:
        return "final", "Final"
    if stype in {"canceled", "cancelled"}:
        return "scheduled", description or "Canceled"
    if stype in {"postponed"}:
        return "scheduled", description or "Postponed"
    return "scheduled", description or "Scheduled"


def normalize_sofa_event(event, known_assets):
    if not isinstance(event, dict):
        return None
    event_id = event.get("id")
    ts = event.get("startTimestamp")
    if not event_id or not ts:
        return None
    try:
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone(MANILA)
    except Exception:
        return None

    home = event.get("homeTeam") or {}
    away = event.get("awayTeam") or {}
    home_name = str(home.get("name") or "").strip()
    away_name = str(away.get("name") or "").strip()
    if not home_name or not away_name:
        return None

    state, status = sofa_state(event.get("status"))
    date_iso = dt.isoformat(timespec="seconds")
    display = dt.strftime("%b %-d · %-I:%M %p") if sys.platform != "win32" else dt.strftime("%b %d · %I:%M %p").replace(" 0", " ")
    if state == "final":
        display = dt.strftime("%b %-d · Final") if sys.platform != "win32" else dt.strftime("%b %d · Final").replace(" 0", " ")
    elif state == "live":
        display = "LIVE"

    def logo_for(team, name):
        local = (known_assets.get("teams") or {}).get(name)
        if local:
            return local
        tid = team.get("id")
        return f"https://api.sofascore.app/api/v1/team/{tid}/image" if tid else ""

    return {
        "eventId": f"tat-sofa-{event_id}",
        "providerEventId": str(event_id),
        "date": date_iso,
        "displayTime": display,
        "away": away_name,
        "home": home_name,
        "awayLogo": logo_for(away, away_name),
        "homeLogo": logo_for(home, home_name),
        "awayScore": score_value(event.get("awayScore")) if state in {"live", "final"} else "—",
        "homeScore": score_value(event.get("homeScore")) if state in {"live", "final"} else "—",
        "status": status,
        "state": state,
        "sourceName": "Sofascore",
        "sourceUrl": "https://www.sofascore.com/basketball/tournament/international/the-asian-tournament/31390",
    }


def fetch_sofascore(current, assets):
    seasons = get_json(f"{SOFASCORE_BASE}/unique-tournament/{SOFASCORE_TOURNAMENT_ID}/seasons").get("seasons", [])
    season = choose_season(seasons)
    if not season:
        raise RuntimeError("No SofaScore TAT season found")
    season_id = season.get("id")
    print("SofaScore season:", season.get("name"), season_id)

    raw_events = []
    for direction, max_pages in (("last", 3), ("next", 2)):
        for page in range(max_pages):
            try:
                payload = get_json(
                    f"{SOFASCORE_BASE}/unique-tournament/{SOFASCORE_TOURNAMENT_ID}/season/{season_id}/events/{direction}/{page}"
                )
            except Exception as ex:
                print("SofaScore events", direction, page, ex)
                break
            events = payload.get("events") or []
            raw_events.extend(events)
            if not events or payload.get("hasNextPage") is False:
                break

    by_id = {}
    for event in raw_events:
        if event.get("id"):
            by_id[str(event["id"])] = event

    games = []
    for event in by_id.values():
        normalized = normalize_sofa_event(event, assets)
        if normalized:
            games.append(normalized)

    def dt_value(game):
        try:
            return datetime.fromisoformat(game["date"]).timestamp()
        except Exception:
            return 0

    live = sorted((g for g in games if g["state"] == "live"), key=dt_value)
    upcoming = sorted((g for g in games if g["state"] == "scheduled"), key=dt_value)[:20]
    finals = sorted((g for g in games if g["state"] == "final"), key=dt_value, reverse=True)[:30]
    merged = live + upcoming + finals
    print("SofaScore games:", len(live), "live", len(upcoming), "upcoming", len(finals), "final")

    standings = []
    try:
        payload = get_json(
            f"{SOFASCORE_BASE}/unique-tournament/{SOFASCORE_TOURNAMENT_ID}/season/{season_id}/standings/total"
        )
        groups = payload.get("standings") or []
        rows = []
        for group in groups:
            rows.extend(group.get("rows") or [])
        for row in rows:
            team = row.get("team") or {}
            name = str(team.get("name") or "").strip()
            if not name:
                continue
            standings.append(
                {
                    "position": row.get("position"),
                    "team": name,
                    "logo": (assets.get("teams") or {}).get(name)
                    or (f"https://api.sofascore.app/api/v1/team/{team.get('id')}/image" if team.get("id") else ""),
                    "played": row.get("matches") if row.get("matches") is not None else row.get("played"),
                    "wins": row.get("wins"),
                    "losses": row.get("losses"),
                    "points": row.get("points"),
                    "percentage": row.get("percentage"),
                }
            )
        print("SofaScore standings rows:", len(standings))
    except Exception as ex:
        print("SofaScore standings unavailable:", ex)
        standings = current.get("standings") or []

    discovered_teams = {}
    for event in by_id.values():
        for side in ("homeTeam", "awayTeam"):
            team = event.get(side) or {}
            name = str(team.get("name") or "").strip()
            if name:
                discovered_teams[name] = team

    return {
        "season": {"id": season_id, "name": season.get("name") or "2026"},
        "games": merged or current.get("games") or [],
        "standings": standings,
        "discoveredTeams": discovered_teams,
    }


def clean_strings(node):
    return [" ".join(x.split()) for x in node.stripped_strings if " ".join(x.split())]


def fetch_official_teams(current):
    html = get_text(TAT_TEAMS_URL)
    soup = BeautifulSoup(html, "html.parser")
    old = {str(x.get("team")): x for x in current.get("teams") or [] if x.get("team")}
    names = []
    for h in soup.find_all(["h2", "h3"]):
        name = " ".join(h.stripped_strings).strip()
        if not name or name.lower() in {"all teams", "teams", "meet the teams"}:
            continue
        parent = h
        card = None
        for _ in range(6):
            parent = getattr(parent, "parent", None)
            if parent is None:
                break
            strings = clean_strings(parent)
            if "Learn more" in strings and len(strings) <= 30:
                card = parent
                break
        if card is None:
            continue
        strings = clean_strings(card)
        if name not in strings:
            continue
        country = ""
        legs = []
        try:
            idx = strings.index(name)
        except ValueError:
            idx = -1
        for value in strings[idx + 1 :]:
            if value.startswith("2026 Leg"):
                legs.append(value)
                continue
            if value.lower() in {"image", "learn more", "estabilished", "established"}:
                continue
            if re.fullmatch(r"\d{4}", value):
                continue
            if not country and not value.startswith("202"):
                country = value
        names.append(
            {
                "team": name,
                "country": country or old.get(name, {}).get("country", ""),
                "legs": " · ".join(dict.fromkeys(legs)) or old.get(name, {}).get("legs", ""),
            }
        )

    dedup = []
    seen = set()
    for item in names:
        if item["team"] in seen:
            continue
        seen.add(item["team"])
        dedup.append(item)
    print("Official teams parsed:", len(dedup))
    return dedup or current.get("teams") or []


def fetch_official_legs(current):
    try:
        html = get_text(TAT_URL)
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.select('a[href*="/legs/"]'):
            href = urljoin(TAT_URL, a.get("href") or "")
            if href not in links:
                links.append(href)
        result = []
        for href in links[:10]:
            try:
                page = BeautifulSoup(get_text(href), "html.parser")
                title_node = page.find("h1")
                title = " ".join(title_node.stripped_strings).strip() if title_node else ""
                if not title:
                    continue
                strings = clean_strings(page)
                dates = ""
                venue = ""
                if "dates:" in [x.lower() for x in strings]:
                    low = [x.lower() for x in strings]
                    idx = low.index("dates:")
                    bits = []
                    for x in strings[idx + 1 : idx + 6]:
                        if x.lower() in {"no of teams:", "venue:", "location:"}:
                            break
                        bits.append(x)
                    dates = " ".join(bits).replace(" - ", "–")
                if "venue:" in [x.lower() for x in strings]:
                    low = [x.lower() for x in strings]
                    idx = low.index("venue:")
                    if idx + 1 < len(strings):
                        venue = strings[idx + 1]
                result.append(
                    {
                        "leg": title.replace("2026 ", ""),
                        "dates": dates,
                        "status": "Completed" if "completed" in " ".join(strings[:30]).lower() else ("Upcoming" if "upcoming" in " ".join(strings[:30]).lower() else "Listed"),
                        "url": href,
                        "venue": venue,
                    }
                )
            except Exception as ex:
                print("Leg page failed:", href, ex)
        print("Official legs parsed:", len(result))
        return result or current.get("legs") or []
    except Exception as ex:
        print("Official legs unavailable:", ex)
        return current.get("legs") or []


def fetch_official_news(current):
    html = get_text(TAT_NEWS_URL)
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen = set()
    for a in soup.select("a[href]"):
        href = urljoin(TAT_URL, a.get("href") or "")
        parsed = urlparse(href)
        if parsed.netloc not in {"www.theasiantournament.com", "theasiantournament.com"}:
            continue
        if "/news/" not in parsed.path.rstrip("/"):
            continue
        if href in seen:
            continue
        card = a
        for _ in range(5):
            parent = getattr(card, "parent", None)
            if parent is None:
                break
            if parent.find("img") or parent.find(["h2", "h3", "h4"]):
                card = parent
                break
            card = parent
        heading = card.find(["h2", "h3", "h4"]) if card else None
        title = " ".join(heading.stripped_strings).strip() if heading else " ".join(a.stripped_strings).strip()
        title = re.sub(r"^\d{1,2}\s+\w+\s+news\s+", "", title, flags=re.I).strip()
        if not title or len(title) < 5:
            continue
        strings = clean_strings(card) if card else []
        published = ""
        for s in strings:
            m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3,9})$", s)
            if m:
                try:
                    dt = datetime.strptime(f"{m.group(1)} {m.group(2)} 2026", "%d %b %Y").replace(tzinfo=MANILA)
                    published = dt.isoformat(timespec="seconds")
                except Exception:
                    pass
                break
        img = card.find("img") if card else None
        image_url = urljoin(TAT_URL, img.get("src") or img.get("data-src") or "") if img else ""
        local_image = download_image(image_url, NEWS_DIR, "auto-" + hashlib.sha1(href.encode()).hexdigest()[:12]) if image_url else ""
        items.append(
            {
                "title": title,
                "url": href,
                "published": published,
                "sourceName": "The Asian Tournament",
                "image": local_image or image_url,
            }
        )
        seen.add(href)
    print("Official news parsed:", len(items))
    return items[:12] or current.get("headlines") or []


def youtube_api(endpoint, params):
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")
    params = dict(params)
    params["key"] = YOUTUBE_API_KEY
    r = session.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=params, timeout=25)
    r.raise_for_status()
    return r.json()


def fetch_youtube_highlights(current):
    if not YOUTUBE_API_KEY:
        print("YouTube highlight automation skipped: no API key")
        return current.get("highlights") or []

    channels = youtube_api("channels", {"part": "snippet,contentDetails", "forHandle": "TheAsianTournament"}).get("items", [])
    if not channels:
        raise RuntimeError("Official TAT YouTube handle could not be resolved")
    channel = channels[0]
    channel_id = channel.get("id")
    uploads = ((channel.get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads")
    if not uploads:
        raise RuntimeError("Official TAT uploads playlist not found")
    print("TAT YouTube channel:", channel_id)

    playlist = youtube_api(
        "playlistItems",
        {"part": "snippet,contentDetails", "playlistId": uploads, "maxResults": 50},
    ).get("items", [])
    ids = [str((x.get("contentDetails") or {}).get("videoId") or "") for x in playlist]
    ids = [x for x in ids if x]
    details = {}
    for i in range(0, len(ids), 50):
        batch = youtube_api(
            "videos",
            {"part": "snippet,status,liveStreamingDetails", "id": ",".join(ids[i : i + 50]), "maxResults": 50},
        ).get("items", [])
        details.update({str(x.get("id")): x for x in batch if x.get("id")})

    selected = []
    for pid in playlist:
        vid = str((pid.get("contentDetails") or {}).get("videoId") or "")
        d = details.get(vid) or {}
        sn = d.get("snippet") or pid.get("snippet") or {}
        title = str(sn.get("title") or "").strip()
        upper = title.upper()
        if not title or any(x in upper for x in ["PRESS CONFERENCE", "INTERVIEW", "PODCAST", "TRAILER", "PROMO"]):
            continue
        if not any(x in upper for x in [" VS ", " V ", "HIGHLIGHT", "THE ASIAN TOURNAMENT", "SUMMER SLAM"]):
            continue
        live = d.get("liveStreamingDetails") or {}
        # Do not put a currently live broadcast into the archived highlight list.
        if live and live.get("actualStartTime") and not live.get("actualEndTime"):
            continue
        thumbs = sn.get("thumbnails") or {}
        thumb = ""
        for key in ("maxres", "standard", "high", "medium", "default"):
            if (thumbs.get(key) or {}).get("url"):
                thumb = thumbs[key]["url"]
                break
        local_thumb = download_image(thumb, HIGHLIGHTS_DIR, vid) if thumb else ""
        selected.append(
            {
                "id": vid,
                "title": title,
                "watchUrl": f"https://www.youtube.com/watch?v={vid}",
                "thumbnail": local_thumb or thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "source": "The Asian Tournament",
                "published": sn.get("publishedAt") or "",
            }
        )
        if len(selected) >= 12:
            break
    print("Official YouTube videos selected:", len(selected))
    return selected or current.get("highlights") or []


def merge_team_directory(official_teams, discovered, current):
    existing = {str(x.get("team")): dict(x) for x in current.get("teams") or [] if x.get("team")}
    out = {}
    for item in official_teams:
        name = str(item.get("team") or "").strip()
        if name:
            out[name] = {**existing.get(name, {}), **item}
    for name in discovered:
        if name not in out:
            out[name] = existing.get(name, {"team": name, "country": "", "legs": ""})
    return list(out.values())


def semantic(data):
    copy = deepcopy(data)
    copy.pop("updatedAt", None)
    auto = copy.get("automation")
    if isinstance(auto, dict):
        auto.pop("lastChangedAt", None)
    return copy


def main():
    local = local_json(DATA_PATH, {})
    prior = prior_remote_data()
    current = prior if isinstance(prior, dict) and prior.get("games") else local

    # Preserve user-owned metadata from main even when the automation branch exists.
    for key in ("source", "previousGamePhotos"):
        if local.get(key):
            current[key] = local[key]

    current_schedule = schedule_summary(current)
    env_game_day = str(os.getenv("TAT_GAME_DAY", "")).strip().lower() == "true"
    game_day = bool(current_schedule["gameDay"] or env_game_day)
    run_slow_env = str(os.getenv("TAT_RUN_SLOW", "")).strip().lower()
    run_slow = True if not run_slow_env else run_slow_env == "true"

    print(
        "TAT automation mode:",
        "game-day" if game_day else "idle",
        "| slow discovery:", run_slow,
        "| known games today:", current_schedule["todayGameCount"],
    )

    assets = local_json(ASSETS_PATH, {"teams": {}})
    candidate = deepcopy(current)
    candidate.setdefault(
        "source",
        {
            "name": "The Asian Tournament",
            "url": TAT_URL,
            "note": "IMG TAT automation uses official TAT pages plus verified score/video sources.",
        },
    )

    # Schedules/scores/standings are checked on game days and during the slower
    # discovery pass. This allows a newly published game date to switch IMG into
    # game-day mode automatically without running every expensive task all day.
    sofa = None
    if game_day or run_slow:
        try:
            sofa = fetch_sofascore(current, assets)
            candidate["games"] = sofa["games"]
            candidate["standings"] = sofa["standings"]
            candidate["season"] = sofa["season"]
        except Exception as ex:
            print("SofaScore automation failed; preserving prior games:", ex)

    # Team directory, leg metadata and news are deliberately slow-path tasks.
    # They do not need a 15-minute refresh when there is no scheduled TAT game.
    if run_slow:
        try:
            official_teams = fetch_official_teams(current)
        except Exception as ex:
            print("Official team refresh failed:", ex)
            official_teams = current.get("teams") or []
    else:
        official_teams = current.get("teams") or []

    discovered = (sofa or {}).get("discoveredTeams") or {}
    candidate["teams"] = merge_team_directory(official_teams, discovered, current)

    if run_slow:
        try:
            candidate["legs"] = fetch_official_legs(current)
        except Exception as ex:
            print("Official leg refresh failed:", ex)

        try:
            candidate["headlines"] = fetch_official_news(current)
        except Exception as ex:
            print("Official news refresh failed:", ex)

    # New replays/highlights can appear soon after a game, so keep this fast on a
    # game day. On idle days it follows the slower discovery cadence.
    if game_day or run_slow:
        try:
            candidate["highlights"] = fetch_youtube_highlights(current)
        except Exception as ex:
            print("YouTube highlight refresh failed:", ex)

    team_logos = dict(candidate.get("teamLogos") or {})
    for name, team in discovered.items():
        if (assets.get("teams") or {}).get(name):
            team_logos[name] = assets["teams"][name]
        elif team.get("id"):
            team_logos[name] = f"https://api.sofascore.app/api/v1/team/{team['id']}/image"
    candidate["teamLogos"] = team_logos

    refreshed_schedule = schedule_summary(candidate)
    # The workflow gate may already know today is a game day from the previous
    # snapshot even if one upstream source is temporarily unavailable.
    final_game_day = bool(refreshed_schedule["gameDay"] or env_game_day)
    final_mode = "game-day" if final_game_day else "idle"

    previous_auto = current.get("automation") or {}
    previous_schedule = previous_auto.get("scheduleAware") or {}
    checked_at = now_iso()

    schedule_aware = {
        "enabled": True,
        "timezone": "Asia/Manila",
        "mode": final_mode,
        "gameDay": final_game_day,
        "todayGameCount": max(
            int(refreshed_schedule.get("todayGameCount") or 0),
            int(os.getenv("TAT_TODAY_GAME_COUNT") or 0),
        ),
        "todayGames": refreshed_schedule.get("todayGames") or [],
        "nextGameAt": refreshed_schedule.get("nextGameAt")
        or str(os.getenv("TAT_NEXT_GAME_AT") or "")
        or previous_schedule.get("nextGameAt")
        or "",
        "idleDiscoveryMinutes": 180,
        "gameDayDataRefreshMinutes": 15,
        "gameDayLivestreamRefreshMinutes": 5,
        "gameDayOnlyTasks": [
            "fast score/result refresh",
            "live-game status",
            "official TAT livestream scan",
            "post-game highlight refresh",
        ],
        "slowTasks": [
            "schedule discovery",
            "teams",
            "legs",
            "news",
            "standings discovery",
        ],
        "lastSlowCheckAt": checked_at if run_slow else previous_schedule.get("lastSlowCheckAt", ""),
    }

    candidate["automation"] = {
        "enabled": True,
        "mode": final_mode,
        "dataRefreshMinutes": 15 if final_game_day else 180,
        "livestreamRefreshMinutes": 5 if final_game_day else 0,
        "scheduleAware": schedule_aware,
        "sources": [
            "The Asian Tournament official website",
            "Sofascore The Asian Tournament tournament feed",
            "The Asian Tournament official YouTube channel",
        ],
        "failClosed": True,
    }

    if semantic(candidate) == semantic(current):
        print("TAT data checked: no publishable changes.")
        return

    candidate["updatedAt"] = checked_at
    candidate["automation"]["lastChangedAt"] = checked_at
    DATA_PATH.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "TAT data changed:",
        len(candidate.get("games") or []),
        "games,",
        len(candidate.get("teams") or []),
        "teams,",
        len(candidate.get("headlines") or []),
        "news,",
        len(candidate.get("highlights") or []),
        "videos,",
        len(candidate.get("standings") or []),
        "standings rows, mode",
        final_mode,
    )

if __name__ == "__main__":
    main()
