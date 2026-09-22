#!/usr/bin/env python3
import json, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"wta-live-data.json"
URL="https://www.wtatennis.com/scores/"

NAME_RE=re.compile(r"^(?:[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’-]*\.?\s+){0,3}[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+(?:\s*\(\d+\))?$")
ROUND_RE=re.compile(r"^(?:ROUND OF \d+|QUARTERFINALS?|SEMIFINALS?|FINAL|QUALIFYING.*)$",re.I)
COURT_RE=re.compile(r"^(?:COURT\s*\w+|CENTER COURT|CENTRE COURT|GRANDSTAND|STADIUM.*)$",re.I)
LIVE_RE=re.compile(r"(?:MEDICAL TIMEOUT|\b\d+(?:ST|ND|RD|TH) SET:\s*\d+:\d+|\bSET\s*\d+|LIVE|SUSPENDED)",re.I)
SCORE_TOKEN_RE=re.compile(r"^(?:AD|\d{1,2}|\d{1,2}-\d{1,2}|\d{1,2}\(\d+\)|[•·])$",re.I)

def clean_line(s):
    return re.sub(r"\s+"," ",str(s or "")).strip()

def chrome_dump():
    candidates=[
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ]
    last=None
    for chrome in candidates:
        try:
            p=subprocess.run([
                chrome,"--headless=new","--no-sandbox","--disable-gpu",
                "--disable-dev-shm-usage","--hide-scrollbars",
                "--window-size=1440,3000","--virtual-time-budget=22000",
                "--dump-dom",URL
            ],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
            if p.returncode==0 and len(p.stdout)>2000:
                return p.stdout
            last=(chrome,p.returncode,p.stderr[-500:])
        except Exception as ex:
            last=(chrome,type(ex).__name__,str(ex))
    raise RuntimeError(f"Chrome render failed: {last}")

def smallest_live_blocks(soup):
    blocks=[]
    seen=set()
    for node in soup.find_all(string=LIVE_RE):
        el=node.parent
        best=None
        for _ in range(8):
            if not el or not getattr(el,"get_text",None):
                break
            text="\n".join(clean_line(x) for x in el.stripped_strings if clean_line(x))
            lines=text.splitlines()
            if 5<=len(lines)<=40 and any(ROUND_RE.match(x) for x in lines):
                best=el
                if len(text)<900:
                    break
            el=el.parent
        if best is None:
            continue
        text="\n".join(clean_line(x) for x in best.stripped_strings if clean_line(x))
        key=re.sub(r"\s+"," ",text)
        if key in seen:
            continue
        seen.add(key)
        blocks.append(text)
    return blocks

def player_candidates(lines):
    out=[]
    banned=("WTA","ROUND","COURT","SET","LIVE","TIMEOUT","HARD","SINGAPORE","KOREA","OPEN","SEOUL")
    for line in lines:
        s=clean_line(line)
        up=s.upper()
        if not s or any(b in up for b in banned):
            continue
        if re.fullmatch(r"[A-Z]{2,3}",s):
            continue
        if SCORE_TOKEN_RE.match(s):
            continue
        if re.fullmatch(r"[\d\s•·()-]+",s):
            continue
        if NAME_RE.match(s) and any(ch.islower() for ch in s):
            out.append(s)
    # de-duplicate while preserving order
    ded=[]
    for x in out:
        if x not in ded:
            ded.append(x)
    return ded[:2]

def score_after_name(lines,name):
    try:
        i=lines.index(name)
    except ValueError:
        return "—"
    vals=[]
    for s in lines[i+1:i+8]:
        s=clean_line(s)
        if not s:
            continue
        if LIVE_RE.search(s) or ROUND_RE.match(s) or COURT_RE.match(s):
            break
        if SCORE_TOKEN_RE.match(s):
            vals.append(s)
        elif NAME_RE.match(s) and any(ch.islower() for ch in s):
            break
    vals=[v for v in vals if v not in {"•","·"}]
    return " ".join(vals) if vals else "—"

def parse_blocks(blocks):
    games=[]
    for idx,text in enumerate(blocks):
        lines=[clean_line(x) for x in text.splitlines() if clean_line(x)]
        names=player_candidates(lines)
        if len(names)<2:
            continue
        round_name=next((x for x in lines if ROUND_RE.match(x)),"")
        court=next((x for x in lines if COURT_RE.match(x)),"")
        live_status=next((x for x in lines if LIVE_RE.search(x) and not ROUND_RE.match(x)),"Live")
        tournament=""
        # nearby block often includes tournament name; keep only if obvious.
        for x in lines[:8]:
            if re.search(r"(OPEN|MASTERS|CLASSIC|CHAMPIONSHIPS|TROPHY)",x,re.I) and not ROUND_RE.match(x):
                tournament=x
                break
        games.append({
            "eventId":f"wta-scrape-{idx}-"+re.sub(r"[^a-z0-9]+","-",("-".join(names)).lower()).strip("-")[:70],
            "date":datetime.now(timezone.utc).isoformat(),
            "displayTime":tournament or "WTA Live",
            "away":names[0],
            "home":names[1],
            "awayScore":score_after_name(lines,names[0]),
            "homeScore":score_after_name(lines,names[1]),
            "status":" · ".join(x for x in [live_status,round_name,court] if x),
            "state":"live",
            "eventOnly":False,
            "title":tournament or "WTA",
            "sourceName":"WTA Official Scores scrape",
            "sourceUrl":URL,
        })
    # unique by players
    unique=[]
    seen=set()
    for g in games:
        k="|".join(sorted([g["away"].lower(),g["home"].lower()]))
        if k in seen: continue
        seen.add(k); unique.append(g)
    return unique

def main():
    html=chrome_dump()
    soup=BeautifulSoup(html,"lxml")
    blocks=smallest_live_blocks(soup)
    games=parse_blocks(blocks)
    payload={
        "league":"WTA Tour",
        "sourceName":"WTA Official Scores",
        "sourceUrl":URL,
        "updatedAt":datetime.now(timezone.utc).isoformat(),
        "games":games,
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("WTA rendered blocks:",len(blocks))
    print("WTA live matches scraped:",len(games))
    for g in games[:10]:
        print("LIVE",g["away"],g["awayScore"],"vs",g["home"],g["homeScore"],"|",g["status"])
    if not games:
        # A zero-match result is valid only if WTA itself has no rendered live cards.
        body=" ".join(clean_line(x) for x in soup.stripped_strings)
        if re.search(r"Live\s+[1-9]\d*",body,re.I):
            raise RuntimeError("WTA page indicates live matches but scraper parsed none")

if __name__=="__main__":
    main()
