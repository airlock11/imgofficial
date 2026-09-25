#!/usr/bin/env python3
import json, os, re, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"laliga-highlights.json"
UA="IMG-LaLiga-Highlights/2.0"
CACHE=ROOT/"football-espn-cache.json"
YT="https://www.googleapis.com/youtube/v3"
PROFILES=[
    ("beINSPORTS","beIN SPORTS"),
    ("beinsports-ph","beIN SPORTS Philippines"),
    ("Beinsports-AU","beIN SPORTS Australia"),
]
# Current verified beIN/Dailymotion examples are retained only as a discovery
# fallback; they are still required to match a recent La Liga fixture.
SEED_IDS=["xa97i0o","xbam0qm","xbaqtxm","xbaobem","xbak4ou","xbaoc0m"]

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

def yt(path, params):
    key=os.environ.get("YOUTUBE_API_KEY","").strip()
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY missing")
    p=dict(params); p["key"]=key
    return get_json(YT+"/"+path+"?"+urllib.parse.urlencode(p))

def youtube_channel_id():
    rows=yt("channels",{"part":"snippet,contentDetails","forHandle":"LaLiga"}).get("items",[])
    return str(rows[0].get("id") or "") if rows else ""

def youtube_recent(channel_id):
    ch=yt("channels",{"part":"contentDetails","id":channel_id}).get("items",[])
    if not ch:return []
    uploads=ch[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads","")
    if not uploads:return []
    pis=yt("playlistItems",{"part":"contentDetails","playlistId":uploads,"maxResults":50}).get("items",[])
    ids=[x.get("contentDetails",{}).get("videoId") for x in pis]
    ids=[x for x in ids if x]
    if not ids:return []
    return yt("videos",{"part":"snippet,status,contentDetails","id":",".join(ids[:50])}).get("items",[])

def youtube_global(meta):
    if not bool(meta.get("status",{}).get("embeddable")):
        return False
    restriction=meta.get("contentDetails",{}).get("regionRestriction")
    # Any explicit allow/block country list means the video is not truly global.
    if restriction:
        if restriction.get("allowed") or restriction.get("blocked"):
            return False
    return True

def youtube_embed_ok(video_id):
    url="https://www.youtube.com/embed/"+urllib.parse.quote(video_id)+"?playsinline=1&rel=0"
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Safari/537.36",
        "Accept-Language":"en-US,en;q=0.9",
        "Referer":"https://www.imgofficial.com/",
        "Origin":"https://www.imgofficial.com"
    })
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            page=r.read().decode("utf-8","ignore")
    except Exception as ex:
        print("YouTube embed fetch",video_id,ex)
        return False
    ok=bool(re.search(r'"playabilityStatus"\s*:\s*\{[^{}]{0,500}"status"\s*:\s*"OK"',page,re.S))
    if not ok:
        m=re.search(r'"playabilityStatus"\s*:\s*\{.{0,700}?\}',page,re.S)
        print("YouTube embed blocked",video_id,(m.group(0)[:350] if m else "no playability status"))
    return ok

def collect_youtube(fixtures):
    try:
        cid=youtube_channel_id()
    except Exception as ex:
        print("YouTube channel",ex)
        return []
    if not cid:return []
    try:
        rows=youtube_recent(cid)
    except Exception as ex:
        print("YouTube uploads",ex)
        return []
    cutoff=now()-timedelta(days=30)
    out=[]
    seen=set()
    for v in rows:
        sn=v.get("snippet",{})
        if sn.get("channelId")!=cid:
            continue
        title=str(sn.get("title") or "")
        if not title_matches_fixture(title,fixtures):
            continue
        pub=str(sn.get("publishedAt") or "")
        try:
            if datetime.fromisoformat(pub.replace("Z","+00:00"))<cutoff:
                continue
        except Exception:
            pass
        if not youtube_global(v):
            print("YouTube not global",v.get("id"),v.get("contentDetails",{}).get("regionRestriction"))
            continue
        vid=str(v.get("id") or "")
        if not vid or vid in seen:
            continue
        if not youtube_embed_ok(vid):
            continue
        th=sn.get("thumbnails",{})
        thumb=(th.get("maxres") or th.get("standard") or th.get("high") or {}).get("url","")
        seen.add(vid)
        out.append({
            "id":vid,
            "title":title,
            "url":"",
            "embedUrl":"https://www.youtube.com/embed/"+vid,
            "thumbnail":thumb,
            "publishedAt":pub,
            "provider":"YouTube",
            "sourceName":sn.get("channelTitle") or "LALIGA",
            "verified":True,
            "verification":"official-laliga-youtube-global-domain-embed",
            "playback":"internal"
        })
    out.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
    return out[:12]

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

def dailymotion_meta(video_id):
    fields="id,title,geoblocking,allow_embed,owner.username"
    url="https://api.dailymotion.com/video/"+urllib.parse.quote(video_id)+"?"+urllib.parse.urlencode({"fields":fields})
    return get_json(url)

def globally_available(meta):
    # Dailymotion documents an empty geoblocking list (or just "allow") as
    # accessible from everywhere. Any country list means territory rules apply.
    geo=meta.get("geoblocking")
    if geo is None:
        return False
    if isinstance(geo,str):
        parts=[x.strip().lower() for x in geo.split(",") if x.strip()]
    else:
        parts=[str(x).strip().lower() for x in (geo or []) if str(x).strip()]
    if parts not in ([],["allow"]):
        return False
    if meta.get("allow_embed") is False:
        return False
    return True

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

def collect_dailymotion(fixtures):
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
            meta=dailymotion_meta(vid)
            oe=dailymotion_oembed(vid)
        except Exception as ex:
            print("Dailymotion verify",vid,ex)
            continue
        if not globally_available(meta):
            print("Dailymotion not global",vid,meta.get("geoblocking"))
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
            "verification":"official-beIN-dailymotion-global-embed",
            "playback":"internal"
        })
    out.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
    return out[:12]

def collect():
    fixtures=recent_laliga_matches()
    youtube_items=collect_youtube(fixtures)
    dm_items=collect_dailymotion(fixtures)
    out=[]; seen_titles=set()
    for item in youtube_items+dm_items:
        key=norm(item.get("title"))
        if not key or key in seen_titles:
            continue
        seen_titles.add(key)
        out.append(item)
    out.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
    return out[:12]

def main():
    try:
        items=collect()
        err=""
    except Exception as ex:
        items=[]
        err=str(ex)
        print("La Liga global embed scan",ex)

    # On transient total failure, retain only previously verified internal
    # Dailymotion embeds. Never restore the blocked LaLiga YouTube iframes.
    if not items and err and OUT.exists():
        try:
            old=json.loads(OUT.read_text("utf-8"))
            items=[x for x in old.get("highlights",[]) if x.get("embedUrl") and x.get("verified") is True and "global" in str(x.get("verification") or "")]
        except Exception:
            pass

    payload={
        "version":3,
        "leagueKey":"laliga",
        "league":"La Liga",
        "updatedAt":iso(),
        "source":{
            "mode":"global-internal-embeds",
            "name":"Official LALIGA YouTube + verified global Dailymotion",
            "url":""
        },
        "highlights":items,
        "count":len(items),
        "error":err,
        "playbackPolicy":"internal-only"
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("La Liga global internal highlights",len(items),err or "ok")

if __name__=="__main__":
    main()
