#!/usr/bin/env python3
import html as html_lib
import json, re, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"laliga-highlights.json"
CACHE=ROOT/"football-espn-cache.json"
UA="Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/140 Safari/537.36"
LIST_URL="https://www.laliga.com/videos?competitionslug=laliga-easports&page=1"
BASE="https://www.laliga.com"
MAX_PAGES=24
ATHLETIC_EMBED_SEEDS=[
    ("Highlights | Athletic Club 0-0 Deportivo Alavés | LaLiga 2026/27 MD7",
     "https://play.athletic-club.eus/en/embed/video/highlights-athletic-club-0-0-deportivo-alaves-laliga-2026-27-md7"),
    ("Highlights | Athletic Club 3-0 Atlético de Madrid | LaLiga 2026/27 MD4",
     "https://play.athletic-club.eus/en/embed/video/highlights-athletic-club-3-0-atletico-de-madrid-laliga-2026-27-md4"),
]

def now():
    return datetime.now(timezone.utc)

def iso(dt=None):
    return (dt or now()).replace(microsecond=0).isoformat().replace("+00:00","Z")

def get_text(url, attempts=3):
    last=None
    for n in range(attempts):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":UA,
                "Accept-Language":"en-US,en;q=0.9",
                "Accept":"text/html,application/xhtml+xml"
            })
            with urllib.request.urlopen(req,timeout=30) as r:
                return r.read().decode("utf-8","replace")
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

def recent_laliga_matches(days=28):
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
        au=at-bt or at
        bu=bt-at or bt
        if au and bu and (au & title_tokens) and (bu & title_tokens):
            return True
    return False

def clean_text(value):
    value=html_lib.unescape(str(value or ""))
    value=re.sub(r"<[^>]+>"," ",value)
    return re.sub(r"\s+"," ",value).strip()

def meta(html,name=None,prop=None):
    attr="name" if name else "property"
    key=name or prop
    pats=[
        rf'<meta[^>]+{attr}=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+{attr}=["\']{re.escape(key)}["\']'
    ]
    for p in pats:
        m=re.search(p,html,re.I)
        if m:return html_lib.unescape(m.group(1))
    return ""

def listing_pages():
    html=get_text(LIST_URL)
    hrefs=re.findall(r'href=["\']([^"\']*/videos/[^"\']+)["\']',html,re.I)
    out=[]
    seen=set()
    for href in hrefs:
        href=html_lib.unescape(href)
        url=urllib.parse.urljoin(BASE,href)
        parsed=urllib.parse.urlparse(url)
        if parsed.netloc not in {"www.laliga.com","laliga.com","iaas-public-front-pro.laliga.com"}:
            continue
        if parsed.path.rstrip("/")=="/videos":
            continue
        canonical=BASE+parsed.path
        if canonical in seen:
            continue
        seen.add(canonical); out.append(canonical)
        if len(out)>=MAX_PAGES:
            break
    return out

def explicit_embed_urls(page):
    raw=[]
    raw += re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']',page,re.I)
    # LALIGA is a Next.js app; player configuration can also be serialized in scripts.
    for pat in [
        r'"(?:embedUrl|embed_url|embedURL)"\s*:\s*"([^"]+)"',
        r'"(?:playerUrl|player_url|playerURL)"\s*:\s*"([^"]+)"',
        r'((?:https?:)?\\?/\\?/[^"\s]+/(?:embed|player)[^"\s]*)'
    ]:
        raw += re.findall(pat,page,re.I)
    out=[]
    seen=set()
    for value in raw:
        value=html_lib.unescape(str(value or "")).replace("\\/","/").replace("\u0026","&")
        if value.startswith("//"): value="https:"+value
        if not value.startswith("https://"): continue
        u=urllib.parse.urlparse(value)
        host=(u.hostname or "").lower()
        if not host or host.endswith("laliga.com"):
            # LALIGA pages themselves use SAMEORIGIN framing protection, so only
            # an explicit third-party player URL can be embedded by IMG.
            continue
        if host=="www.googletagmanager.com":
            continue
        if re.search(r"\.(?:m3u8|mp4)(?:\?|$)",u.path,re.I):
            # Never hotlink raw media streams; IMG only uses sanctioned player embeds.
            continue
        low=value.lower()
        if not any(token in low for token in [
            "/embed","/player","player.","youtube.com/embed","youtu.be/",
            "dailymotion.com/player","vimeo.com/video","brightcove"
        ]):
            continue
        if value not in seen:
            seen.add(value); out.append(value)
    return out

def slugify_athletic(title):
    text=unicodedata.normalize("NFKD",str(title or ""))
    text="".join(ch for ch in text if not unicodedata.combining(ch))
    text=re.sub(r"\bJ(\d+)\b",r"MD\1",text,flags=re.I)
    text=text.lower()
    text=re.sub(r"[^a-z0-9]+","-",text).strip("-")
    return text

def athletic_play_item(title, fixtures):
    if not title or "HIGHLIGHT" not in title.upper() or "LALIGA" not in title.upper():
        return None
    if not title_matches_fixture(title,fixtures):
        return None

    slug=slugify_athletic(title)
    embed="https://play.athletic-club.eus/en/embed/video/"+slug
    page_url="https://play.athletic-club.eus/en/video/"+slug

    # The /embed/video/ route is the club's explicit iframe endpoint. Verify it
    # is reachable before publishing it to IMG.
    try:
        embed_page=get_text(embed)
    except Exception as ex:
        print("Athletic embed unavailable",embed,ex)
        return None
    low=clean_text(embed_page).lower()
    if "exclusive content" in low or "contenido exclusivo" in low:
        return None

    image=""
    try:
        normal=get_text(page_url)
        image=meta(normal,prop="og:image") or meta(normal,name="twitter:image")
    except Exception:
        pass

    return {
        "id":"athletic-"+slug,
        "title":title,
        "url":"",
        "sourcePage":page_url,
        "embedUrl":embed,
        "thumbnail":image,
        "publishedAt":"",
        "provider":"Athletic Play",
        "sourceName":"Athletic Club Official",
        "verified":True,
        "verification":"official-athletic-club-explicit-embed",
        "playback":"internal"
    }

def collect_athletic_play(fixtures):
    # Start with verified public embed routes already discovered from Athletic
    # Club's official site, then augment from the media index when accessible.
    out=[]
    seen_urls=set()
    for title,embed in ATHLETIC_EMBED_SEEDS:
        if not title_matches_fixture(title,fixtures):
            continue
        try:
            page=get_text(embed)
        except Exception as ex:
            print("Athletic seed unavailable",embed,ex)
            continue
        low=clean_text(page).lower()
        if "exclusive content" in low or "contenido exclusivo" in low:
            continue
        slug=embed.rstrip("/").split("/")[-1]
        page_url="https://play.athletic-club.eus/en/video/"+slug
        image=""
        try:
            normal=get_text(page_url)
            image=meta(normal,prop="og:image") or meta(normal,name="twitter:image")
        except Exception:
            pass
        out.append({
            "id":"athletic-"+slug,
            "title":title,
            "url":"",
            "sourcePage":page_url,
            "embedUrl":embed,
            "thumbnail":image,
            "publishedAt":"",
            "provider":"Athletic Play",
            "sourceName":"Athletic Club Official",
            "verified":True,
            "verification":"official-athletic-club-explicit-embed",
            "playback":"internal"
        })
        seen_urls.add(embed)

    index="https://www.athletic-club.eus/media/"
    try:
        page=get_text(index)
    except Exception as ex:
        print("Athletic media index",ex)
        return out

    flat=clean_text(page)
    titles=[]
    patterns=[
        r"Highlights\s*\|\s*[^|]{3,120}\s*\|\s*LaLiga\s+2026/27\s+J\d+",
        r"Highlights\s*\|\s*[^|]{3,120}\s*\|\s*LaLiga\s+2026/27\s+MD\d+"
    ]
    for pat in patterns:
        for title in re.findall(pat,flat,re.I):
            title=re.sub(r"\s+"," ",title).strip()
            if title not in titles:
                titles.append(title)

    for title in titles[:30]:
        try:
            item=athletic_play_item(title,fixtures)
        except Exception as ex:
            print("Athletic candidate",title,ex)
            continue
        if item and item.get("embedUrl") not in seen_urls:
            seen_urls.add(item.get("embedUrl"))
            out.append(item)
        if len(out)>=8:
            break
    return out

def page_data(url, fixtures):
    page=get_text(url)
    title=meta(page,prop="og:title")
    if not title:
        m=re.search(r"<h1[^>]*>(.*?)</h1>",page,re.I|re.S)
        title=clean_text(m.group(1)) if m else ""
    title=re.sub(r"\s*\|\s*LALIGA\s*$","",title,flags=re.I).strip()
    if not title or not title_matches_fixture(title,fixtures):
        return None

    image=meta(page,prop="og:image") or meta(page,name="twitter:image")
    published=""
    m=re.search(r'(\d{2})-(\d{2})-(20\d{2})\s*\|\s*Resumen de Partido',clean_text(page),re.I)
    if m:
        try:
            published=datetime(int(m.group(3)),int(m.group(2)),int(m.group(1)),tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
        except Exception:
            pass

    embeds=explicit_embed_urls(page)
    if not embeds:
        print("LALIGA page has no sanctioned third-party embed",url)
        return None

    src=embeds[0]
    return {
        "id":url.rstrip("/").split("/")[-1],
        "title":title,
        "url":"",
        "sourcePage":url,
        "embedUrl":src,
        "thumbnail":image,
        "publishedAt":published,
        "provider":"LALIGA.com",
        "sourceName":"LALIGA Official Website",
        "verified":True,
        "verification":"official-laliga-page-explicit-embed",
        "playback":"internal"
    }

def collect():
    fixtures=recent_laliga_matches()
    out=[]
    seen=set()

    # Primary source: LALIGA's own official video pages when they expose a
    # sanctioned third-party embed.
    for url in listing_pages():
        try:
            item=page_data(url,fixtures)
        except Exception as ex:
            print("LALIGA page",url,ex)
            continue
        if not item: continue
        key=norm(item.get("title"))
        if not key or key in seen: continue
        seen.add(key); out.append(item)
        if len(out)>=12: break

    # Supplemental official source: Athletic Club's public Athletic Play embed
    # endpoint, which is explicitly intended for iframe playback.
    for item in collect_athletic_play(fixtures):
        key=norm(item.get("title"))
        if not key or key in seen: continue
        seen.add(key); out.append(item)
        if len(out)>=12: break

    return out

def main():
    try:
        items=collect()
        err=""
    except Exception as ex:
        items=[]
        err=str(ex)
        print("LALIGA official website scan",ex)

    # Retain only previously verified official-LALIGA explicit embeds on a
    # transient scanner failure. Never restore YouTube/Dailymotion fallbacks.
    if not items and err and OUT.exists():
        try:
            old=json.loads(OUT.read_text("utf-8"))
            items=[
                x for x in old.get("highlights",[])
                if x.get("embedUrl") and x.get("verified") is True
                and x.get("verification")=="official-laliga-page-explicit-embed"
            ]
        except Exception:
            pass

    payload={
        "version":5,
        "leagueKey":"laliga",
        "league":"La Liga",
        "updatedAt":iso(),
        "source":{
            "mode":"official-laliga-website",
            "name":"LALIGA Official Website + official club embed sources",
            "url":"https://www.laliga.com/videos?competitionslug=laliga-easports&page=1"
        },
        "highlights":items,
        "count":len(items),
        "error":err,
        "playbackPolicy":"internal-only-explicit-embed"
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("LALIGA official internal highlights",len(items),err or "ok")

if __name__=="__main__":
    main()
