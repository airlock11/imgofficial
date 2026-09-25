#!/usr/bin/env python3
import json, re, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"laliga-highlights.json"
UA="IMG-LaLiga-Highlights/2.0"
CACHE=ROOT/"football-espn-cache.json"
PROFILES=[
    ("beinsports-ph","beIN SPORTS Philippines"),
    ("Beinsports-AU","beIN SPORTS Australia"),
]
# Current verified beIN/Dailymotion examples are retained only as a discovery
# fallback; they are still required to match a recent La Liga fixture.
SEED_IDS=["xbam0qm","xbaqtxm","xbaobem","xbak4ou","xbaoc0m"]

def now():
    return datetime.now(timezone.utc)

def iso(dt=None):
    return (dt or now()).replace(microsecond=0).isoformat().replace("+00:00","Z")

def get_json(url, attempts=3):
    last=None
    for n in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Language":"en-US,en;q=0.8"})
            with urllib.request.urlopen(req,timeout=25) as r:
                return json.load(r)
        except Exception as ex:
            last=ex
    raise last

def norm(value):
    s=unicodedata.normalize("NFKD",str(value or ""))
    s="".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+",s))

STOP={"cf","fc","club","futbol","football","de","del","la","el","los","las","ud","rc","cd","sd","ca"}

def team_tokens(name):
    return {x for x in norm(name).split() if len(x)>=3 and x not in STOP}

def recent_laliga_matches(days=24):
    # Use IMG's already-maintained ESPN cache. Direct ESPN calls can reject
    # GitHub-hosted automation traffic even when the same data is valid.
    data=json.loads(CACHE.read_text("utf-8"))
    rows=data.get("leagues",{}).get("laliga",{}).get("games",[])
    cutoff=now()-timedelta(days=days)
    out=[]
    for game in rows:
        if str(game.get("state") or "").lower() not in {"final","live","in"}:
            continue
        try:
            dt=datetime.fromisoformat(str(game.get("date") or "").replace("Z","+00:00")).astimezone(timezone.utc)
            if dt<cutoff:
                continue
        except Exception:
            pass
        home=str(game.get("home") or "").strip()
        away=str(game.get("away") or "").strip()
        if home and away:
            out.append((home,away))
    return out

def title_matches_fixture(title, fixtures):
    title_tokens=set(norm(title).split())
    for a,b in fixtures:
        at=team_tokens(a); bt=team_tokens(b)
        au=at-bt; bu=bt-at
        # Use distinctive tokens for each side, avoiding shared city/name words.
        if not au: au=at
        if not bu: bu=bt
        if au and bu and (au & title_tokens) and (bu & title_tokens):
            return True
    return False

def dailymotion_list(profile):
    fields="id,title,created_time,thumbnail_720_url,thumbnail_480_url"
    params={
        "fields":fields,
        "limit":100,
        "sort":"recent",
        "ams_country":"ph",
        "device_filter":"web",
        "family_filter":"true",
    }
    url="https://api.dailymotion.com/user/"+urllib.parse.quote(profile)+"/videos?"+urllib.parse.urlencode(params)
    data=get_json(url)
    return [x for x in data.get("list",[]) if isinstance(x,dict)]

def dailymotion_oembed(video_id):
    page="https://www.dailymotion.com/video/"+video_id
    url="https://www.dailymotion.com/services/oembed?"+urllib.parse.urlencode({"url":page,"format":"json"})
    return get_json(url)

def embed_src(html):
    m=re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']',str(html or ""),re.I)
    return m.group(1).replace("&amp;","&") if m else ""

def author_matches(oembed, profile):
    author_url=str(oembed.get("author_url") or "").rstrip("/").lower()
    return author_url.endswith("/"+profile.lower())

def to_iso(ts):
    try:
        return datetime.fromtimestamp(int(ts),timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    except Exception:
        return ""

def collect():
    fixtures=recent_laliga_matches()
    candidates=[]
    api_ok=False
    for profile,label in PROFILES:
        try:
            rows=dailymotion_list(profile)
            api_ok=True
        except Exception as ex:
            print("Dailymotion list",profile,ex)
            rows=[]
        for row in rows:
            title=str(row.get("title") or "")
            up=title.upper()
            if "HIGHLIGHT" not in up:
                continue
            if not title_matches_fixture(title,fixtures):
                continue
            candidates.append((str(row.get("id") or ""),profile,label,row))
    # If the listing endpoint is temporarily unavailable, recheck a few exact
    # official IDs instead of falling back to unverified third-party uploads.
    if not candidates and not api_ok:
        for vid in SEED_IDS:
            candidates.append((vid,"Beinsports-AU","beIN SPORTS Australia",{}))

    out=[]
    seen_ids=set()
    seen_titles=set()
    for vid,profile,label,row in candidates:
        if not vid or vid in seen_ids:
            continue
        try:
            oe=dailymotion_oembed(vid)
        except Exception as ex:
            print("Dailymotion oEmbed",vid,ex)
            continue
        if str(oe.get("provider_name") or "").lower()!="dailymotion":
            continue
        if not author_matches(oe,profile):
            continue
        title=str(oe.get("title") or row.get("title") or "")
        if "HIGHLIGHT" not in title.upper() or not title_matches_fixture(title,fixtures):
            continue
        src=embed_src(oe.get("html"))
        if not src.startswith("https://geo.dailymotion.com/"):
            continue
        key=norm(title)
        if key in seen_titles:
            continue
        seen_ids.add(vid); seen_titles.add(key)
        out.append({
            "id":vid,
            "title":title,
            "url":"",
            "embedUrl":src,
            "thumbnail":oe.get("thumbnail_url") or row.get("thumbnail_720_url") or row.get("thumbnail_480_url") or "",
            "publishedAt":to_iso(row.get("created_time")),
            "provider":"Dailymotion",
            "sourceName":str(oe.get("author_name") or label),
            "verified":True,
            "verification":"official-beIN-dailymotion-oembed-ph-web",
            "playback":"internal"
        })
    out.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
    return out[:12]

def main():
    try:
        items=collect()
        err=""
    except Exception as ex:
        items=[]
        err=str(ex)
        print("La Liga Dailymotion scan",ex)

    # On transient total failure, retain only previously verified internal
    # Dailymotion embeds. Never restore the blocked LaLiga YouTube iframes.
    if not items and err and OUT.exists():
        try:
            old=json.loads(OUT.read_text("utf-8"))
            items=[x for x in old.get("highlights",[]) if x.get("provider")=="Dailymotion" and x.get("embedUrl") and x.get("verified") is True]
        except Exception:
            pass

    payload={
        "version":2,
        "leagueKey":"laliga",
        "league":"La Liga",
        "updatedAt":iso(),
        "source":{
            "mode":"dailymotion-oembed",
            "name":"Official beIN SPORTS Dailymotion",
            "url":""
        },
        "highlights":items,
        "count":len(items),
        "error":err,
        "playbackPolicy":"internal-only"
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("La Liga internal highlights",len(items),err or "ok")

if __name__=="__main__":
    main()
