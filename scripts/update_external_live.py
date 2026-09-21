#!/usr/bin/env python3
import html
import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parents[1]/"external-live.json"
UA="Mozilla/5.0 (compatible; IMG-Sports-Live/1.0; +https://www.imgofficial.com)"
SERIES_PATH="/live-sport/20th-asian-games-aichi-nagoya-2026-1790007854/"
SONY_HOST="www.sonyliv.com"
SEEDS=[
    "https://www.sonyliv.com/sports/cricket-20th-asian-games-aichi-nagoya-2026-1590016519",
    "https://www.sonyliv.com/live-sport/20th-asian-games-aichi-nagoya-2026-1790007854/sports-stream-3-21-sep-2026-1090541385",
]
SPORTS=[
    ("3x3 Basketball","3x3 Basketball"),
    ("Artistic Gymnastics","Artistic Gymnastics"),
    ("Beach Volleyball","Beach Volleyball"),
    ("Table Tennis","Table Tennis"),
    ("Sepaktakraw","Sepaktakraw"),
    ("Badminton","Badminton"),
    ("Basketball","Basketball"),
    ("Baseball","Baseball"),
    ("Football","Football"),
    ("Handball","Handball"),
    ("Volleyball","Volleyball"),
    ("Swimming","Swimming"),
    ("Gymnastics","Gymnastics"),
    ("Hockey","Hockey"),
    ("Kabaddi","Kabaddi"),
    ("Karate","Karate"),
    ("Boxing","Boxing"),
    ("Shooting","Shooting"),
    ("Wrestling","Wrestling"),
    ("Athletics","Athletics"),
    ("Cycling","Cycling"),
    ("Judo","Judo"),
]

def fetch_text(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":UA,
        "Accept":"text/html,application/xhtml+xml",
        "Accept-Language":"en-US,en;q=0.9",
        "Cache-Control":"no-cache",
    })
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.read().decode("utf-8","ignore")

def normalise_embedded(text):
    text=html.unescape(text or "")
    text=text.replace("\\/","/").replace("\u002F","/").replace("\u002f","/")
    text=text.replace("\u003A",":").replace("\u003a",":")
    return text

def extract_urls(page,base):
    page=normalise_embedded(page)
    found=[]
    patterns=[
        r"https?://www\.sonyliv\.com/live-sport/20th-asian-games-aichi-nagoya-2026-1790007854/[^\"'<>\\\s]+",
        r"(?:\"|')(/live-sport/20th-asian-games-aichi-nagoya-2026-1790007854/[^\"'<>\\\s]+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat,page,re.I):
            raw=m.group(1) if m.lastindex else m.group(0)
            raw=raw.rstrip("\\,]}")
            url=urllib.parse.urljoin(base,raw)
            p=urllib.parse.urlsplit(url)
            if p.hostname and p.hostname.lower()==SONY_HOST and p.path.startswith(SERIES_PATH):
                clean=urllib.parse.urlunsplit(("https",SONY_HOST,p.path,p.query,""))
                found.append(clean)
    return list(dict.fromkeys(found))

def meta_value(page,prop):
    tests=[
        rf'''<meta[^>]+(?:property|name)=["']{re.escape(prop)}["'][^>]+content=["']([^"']+)["']''',
        rf'''<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']{re.escape(prop)}["']''',
    ]
    for pat in tests:
        m=re.search(pat,page,re.I|re.S)
        if m:return html.unescape(m.group(1)).strip()
    return ""

def page_title(page):
    value=meta_value(page,"og:title") or meta_value(page,"twitter:title")
    if value:return value
    m=re.search(r"<title[^>]*>(.*?)</title>",page,re.I|re.S)
    return html.unescape(re.sub(r"\s+"," ",m.group(1))).strip() if m else ""

def visible_text(page):
    text=re.sub(r"<script\b[^>]*>.*?</script>"," ",page,flags=re.I|re.S)
    text=re.sub(r"<style\b[^>]*>.*?</style>"," ",text,flags=re.I|re.S)
    text=re.sub(r"<[^>]+>"," ",text)
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def current_date_tokens(now_local):
    return {
        now_local.strftime("%d-%m-%Y").lstrip("0"),
        now_local.strftime("%d-%m-%Y"),
        now_local.strftime("%d %b %Y").lstrip("0"),
        now_local.strftime("%d %B %Y").lstrip("0"),
        now_local.strftime("%b %d, %Y").replace(" 0"," "),
        now_local.strftime("%B %d, %Y").replace(" 0"," "),
    }

def clean_event_title(title):
    title=html.unescape(title or "")
    title=re.sub(r"^Watch\s+","",title,flags=re.I)
    title=re.sub(r"\s+Live Match Streaming.*$","",title,flags=re.I)
    title=re.sub(r"\s+-\s+20th Asian Games.*$","",title,flags=re.I)
    return re.sub(r"\s+"," ",title).strip(" -")

def sport_from_title(title):
    low=title.lower()
    for needle,label in SPORTS:
        if needle.lower() in low:return label
    return "Asian Games"

def teams_from_title(title):
    core=re.sub(r"\s+-\s+\d{1,2}\s+[A-Za-z]{3}\s+2026.*$","",title).strip()
    m=re.search(r"(.+?)\s+vs\.?\s+(.+?)(?:\s+-\s+(?:Women|Men|Women's|Men's|Team|Hockey|Football|Basketball|Volleyball|Kabaddi|Badminton|Table Tennis|Handball|Baseball|Sepaktakraw|Boxing|Karate|Gymnastics|Swimming).*)?$",core,re.I)
    if not m:return []
    a,b=m.group(1).strip(),m.group(2).strip()
    return [a,b] if a and b else []

def page_is_live(page,title,url,now_local):
    raw=normalise_embedded(page)
    lower=raw.lower()
    text=visible_text(raw)
    date_ok=any(tok.lower() in (title+" "+text[:20000]).lower() for tok in current_date_tokens(now_local))
    if not date_ok:return False

    content_id=(re.search(r"(\d{10})/?(?:\?|$)",url) or [None,None])[1]
    strong=[
        '"islive":true','"is_live":true','"livestatus":"live"','"live_status":"live"',
        '"contentstatus":"live"','"status":"live"','"badge":"live"','"badgetype":"live"',
        '"iscurrentlylive":true'
    ]
    if content_id:
        idx=lower.find(content_id.lower())
        if idx>=0:
            nearby=lower[max(0,idx-6000):idx+6000]
            if any(x in nearby for x in strong):return True

    if any(x in lower for x in strong):
        event=clean_event_title(title)
        words=[w for w in re.findall(r"[a-z0-9]+",event.lower()) if len(w)>3][:5]
        if words and sum(1 for w in words if w in lower)>=min(2,len(words)):
            return True

    event=clean_event_title(title)
    if event:
        variants=["LIVE "+event,event+" LIVE"]
        text_low=text.lower()
        if any(v.lower() in text_low for v in variants):
            return True
    return False

def main():
    india=ZoneInfo("Asia/Kolkata")
    now=datetime.now(timezone.utc)
    local=now.astimezone(india)
    candidates=[]
    pages={}
    for seed in SEEDS:
        try:
            page=fetch_text(seed);pages[seed]=page
            candidates.append(seed)
            candidates.extend(extract_urls(page,seed))
        except Exception as ex:
            print("seed",seed,ex)
    candidates=list(dict.fromkeys(candidates))[:80]
    print("sony candidates",len(candidates))

    streams=[]
    for url in candidates:
        try:
            page=pages.get(url) or fetch_text(url)
            title=page_title(page)
            if "asian games" not in title.lower():continue
            if not page_is_live(page,title,url,local):continue
            event=clean_event_title(title)
            sport=sport_from_title(event)
            teams=teams_from_title(event)
            streams.append({
                "eventId":"ag26-sonyliv-"+hashlib.sha1(urllib.parse.urlsplit(url).path.encode("utf-8")).hexdigest()[:12],
                "sport":sport,
                "leagueKey":"asian_games",
                "league":"Asian Games",
                "teams":teams,
                "title":event or title,
                "stream":{
                    "watchUrl":url,
                    "provider":"Sony LIV",
                    "channel":"Sony LIV",
                    "title":event or title,
                    "external":True,
                    "geoRestricted":True,
                    "region":"India"
                }
            })
        except Exception as ex:
            print("candidate",url,ex)


    seen=set();dedup=[]
    for x in streams:
        key=x["stream"]["watchUrl"]
        if key in seen:continue
        seen.add(key);dedup.append(x)

    payload={
        "updatedAt":now.isoformat(),
        "freshForMinutes":20,
        "streams":dedup,
        "sources":[
            {"name":"Sony LIV","region":"India","official":True,"directEventLinksOnly":True}
        ]
    }
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("verified external live streams",len(dedup))
    for x in dedup[:20]:
        print(x["sport"],"-",x["title"],"-",x["stream"]["watchUrl"])

if __name__=="__main__":
    main()
