#!/usr/bin/env python3
import json
import math
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"stats-data.json"
UAAP_BASE="https://uaap.livestats.ph/tournaments/uaap-season-89-men-s-basketball"
UA="Mozilla/5.0 (compatible; IMG-Sports-Stats/1.0; +https://www.imgofficial.com)"

UAAP_TEAMS={
    "ADU":"Adamson","ATENEO":"Ateneo","FEU":"FEU","NU":"NU","UE":"UE","UP":"UP","UST":"UST",
    "LA SALLE":"La Salle","DLSU":"La Salle"
}

def fetch(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":UA,
        "Accept":"text/html,application/xhtml+xml",
        "Accept-Language":"en-US,en;q=0.9",
        "Cache-Control":"no-cache"
    })
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.read().decode("utf-8","replace")

def clean(value):
    return re.sub(r"\s+"," ",str(value or "")).strip()

def num(value):
    try:return float(str(value).replace("%","").strip())
    except:return None

def intnum(value):
    try:return int(float(str(value).strip()))
    except:return None

def parse_made_attempted(value):
    m=re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*",str(value or ""))
    return (int(m.group(1)),int(m.group(2))) if m else (0,0)

def table_headers(table):
    rows=table.find_all("tr")
    if not rows:return []
    best=[]
    for row in rows[:4]:
        vals=[clean(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"])]
        if len(vals)>len(best):best=vals
    return best

def previous_team_label(table):
    aliases=sorted(UAAP_TEAMS.keys(),key=len,reverse=True)
    count=0
    for s in table.find_all_previous(string=True):
        t=clean(s).upper()
        if not t:continue
        count+=1
        t=re.sub(r"\s*\(M\)\s*$","",t).strip()
        for alias in aliases:
            if t==alias:
                return "LA SALLE" if alias=="DLSU" else alias
        if count>80:break
    return ""

def parse_player_table(table):
    rows=table.find_all("tr")
    header_row=None
    headers=[]
    for row in rows:
        vals=[clean(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"])]
        upper=[v.upper() for v in vals]
        if "PLAYER" in upper and "PTS" in upper and ("REB" in upper or "AST" in upper):
            header_row=row
            headers=vals
            break
    if not header_row:return [],None
    index={clean(h).upper():i for i,h in enumerate(headers)}
    def at(cells,*names):
        for name in names:
            i=index.get(name.upper())
            if i is not None and i<len(cells):return cells[i]
        return ""
    players=[]
    team_total=None
    active=False
    for row in rows:
        if row is header_row:
            active=True
            continue
        if not active:continue
        cells=[clean(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"])]
        if not cells:continue
        joined=" ".join(cells).upper()
        if "TEAM TOTALS" in joined:
            team_total={
                "pts":intnum(at(cells,"PTS")),
                "fg":at(cells,"FG"),"fgPct":num(at(cells,"FG %","FG%")),
                "twoPt":at(cells,"2P"),"twoPtPct":num(at(cells,"2P %","2P%")),
                "threePt":at(cells,"3P"),"threePtPct":num(at(cells,"3P %","3P%")),
                "ft":at(cells,"FT"),"ftPct":num(at(cells,"FT %","FT%")),
                "off":intnum(at(cells,"OFF")),"def":intnum(at(cells,"DEF")),
                "reb":intnum(at(cells,"REB")),"ast":intnum(at(cells,"AST")),
                "to":intnum(at(cells,"TO")),"stl":intnum(at(cells,"STL")),
                "blk":intnum(at(cells,"BLK")),"pf":intnum(at(cells,"PF"))
            }
            continue
        player=at(cells,"PLAYER")
        if not player or player.lower() in {"player","team / coach"}:continue
        pts=intnum(at(cells,"PTS"))
        if pts is None:continue
        players.append({
            "no":at(cells,"NO.","NO"),"player":player,"mins":at(cells,"MINS"),
            "pts":pts,"fg":at(cells,"FG"),"fgPct":num(at(cells,"FG %","FG%")),
            "twoPt":at(cells,"2P"),"twoPtPct":num(at(cells,"2P %","2P%")),
            "threePt":at(cells,"3P"),"threePtPct":num(at(cells,"3P %","3P%")),
            "ft":at(cells,"FT"),"ftPct":num(at(cells,"FT %","FT%")),
            "off":intnum(at(cells,"OFF")) or 0,"def":intnum(at(cells,"DEF")) or 0,
            "reb":intnum(at(cells,"REB")) or 0,"ast":intnum(at(cells,"AST")) or 0,
            "to":intnum(at(cells,"TO")) or 0,"stl":intnum(at(cells,"STL")) or 0,
            "blk":intnum(at(cells,"BLK")) or 0,"pf":intnum(at(cells,"PF")) or 0,
            "plusMinus":at(cells,"+/-")
        })
    return players,team_total

def discover_game_ids(html):
    ids=[]
    for value in re.findall(r"[?&]game_id=(\d+)",html):
        if value not in ids:ids.append(value)
    soup=BeautifulSoup(html,"html.parser")
    for a in soup.find_all("a",href=True):
        q=urllib.parse.parse_qs(urllib.parse.urlsplit(a["href"]).query)
        for value in q.get("game_id",[]):
            if value.isdigit() and value not in ids:ids.append(value)
    return ids

def find_meta(text):
    venue=""
    date=""
    m=re.search(r"Venue\s+(.+?)\s+Game Details\s+([0-9/]+\s+[0-9:]+\s+[AP]M)",text,re.I)
    if m:
        venue=clean(m.group(1));date=clean(m.group(2))
    return venue,date

def parse_team_stats_tables(soup,teams):
    out={}
    for table in soup.find_all("table"):
        text=clean(table.get_text(" ",strip=True)).upper()
        if "FIELD GOAL %" not in text or "REBOUNDS" not in text or "ASSISTS" not in text:
            continue
        rows=[]
        for tr in table.find_all("tr"):
            cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            if len(cells)<3:continue
            label=""
            li=-1
            for i,c in enumerate(cells):
                u=c.upper()
                if any(k in u for k in ["POINTS","FIELD GOAL","3-PT","FREE THROW","REBOUNDS","ASSISTS","STEALS","BLOCKS","TURNOVERS","BENCH POINTS","POINTS IN THE PAINT","FASTBREAK"]):
                    label=c;li=i;break
            if li<=0 or li>=len(cells)-1:continue
            left=next((num(x) for x in reversed(cells[:li]) if num(x) is not None),None)
            right=next((num(x) for x in cells[li+1:] if num(x) is not None),None)
            if left is not None and right is not None:
                rows.append((clean(label),left,right))
        if rows and len(teams)>=2:
            out={teams[0]:{},teams[1]:{}}
            for label,left,right in rows:
                out[teams[0]][label]=left
                out[teams[1]][label]=right
            break
    return out

def parse_game(game_id):
    url=f"{UAAP_BASE}?game_id={game_id}"
    html=fetch(url)
    soup=BeautifulSoup(html,"html.parser")
    text=clean(soup.get_text(" ",strip=True))
    if "UAAP Season 89 MEN'S BASKETBALL" not in text:
        return None

    teams=[]
    player_sets={}
    totals={}
    for table in soup.find_all("table"):
        players,total=parse_player_table(table)
        if not players:continue
        team=previous_team_label(table)
        if not team or team in player_sets:continue
        teams.append(team)
        player_sets[team]=players
        totals[team]=total or {}
        if len(teams)>=2:break
    if len(teams)<2:return None

    venue,date_text=find_meta(text)
    date_iso=""
    if date_text:
        try:
            dt=datetime.strptime(date_text,"%m/%d/%y %I:%M %p").replace(tzinfo=timezone.utc)
            date_iso=dt.isoformat()
        except:pass

    team_stats=parse_team_stats_tables(soup,teams)
    scores={t:(totals.get(t) or {}).get("pts") for t in teams}
    return {
        "gameId":str(game_id),"url":url,"date":date_iso,"dateText":date_text,
        "venue":venue,"teams":teams,"scores":scores,
        "players":player_sets,"teamTotals":totals,"teamStats":team_stats
    }

def aggregate(games):
    agg={}
    for game in games:
        for team,players in game.get("players",{}).items():
            for p in players:
                key=(team,p["player"])
                row=agg.setdefault(key,{
                    "team":team,"player":p["player"],"gp":0,
                    "pts":0,"reb":0,"ast":0,"stl":0,"blk":0,"to":0,
                    "fgm":0,"fga":0,"tpm":0,"tpa":0,"ftm":0,"fta":0
                })
                row["gp"]+=1
                for k in ["pts","reb","ast","stl","blk","to"]:
                    row[k]+=int(p.get(k) or 0)
                a,b=parse_made_attempted(p.get("fg"));row["fgm"]+=a;row["fga"]+=b
                a,b=parse_made_attempted(p.get("threePt"));row["tpm"]+=a;row["tpa"]+=b
                a,b=parse_made_attempted(p.get("ft"));row["ftm"]+=a;row["fta"]+=b
    rows=[]
    for row in agg.values():
        gp=max(1,row["gp"])
        rows.append({
            "team":row["team"],"player":row["player"],"gp":row["gp"],
            "ppg":round(row["pts"]/gp,1),"rpg":round(row["reb"]/gp,1),
            "apg":round(row["ast"]/gp,1),"spg":round(row["stl"]/gp,1),
            "bpg":round(row["blk"]/gp,1),"topg":round(row["to"]/gp,1),
            "fgPct":round(row["fgm"]*100/row["fga"],1) if row["fga"] else 0,
            "threePtPct":round(row["tpm"]*100/row["tpa"],1) if row["tpa"] else 0,
            "ftPct":round(row["ftm"]*100/row["fta"],1) if row["fta"] else 0
        })
    def leaders(key):
        return sorted(rows,key=lambda x:(x.get(key,0),x.get("gp",0)),reverse=True)[:8]
    return {
        "points":leaders("ppg"),"rebounds":leaders("rpg"),"assists":leaders("apg"),
        "steals":leaders("spg"),"blocks":leaders("bpg")
    }

def main():
    landing=fetch(UAAP_BASE)
    ids=discover_game_ids(landing)
    if not ids:
        ids=[str(i) for i in range(1,25)]
    # Keep a practical current-season sample and avoid hammering the source.
    ids=ids[-20:]
    games=[]
    for gid in ids:
        try:
            game=parse_game(gid)
            if game:games.append(game)
        except Exception as ex:
            print("UAAP game",gid,type(ex).__name__,str(ex)[:120])
    if not games:
        raise SystemExit("No UAAP statistics parsed")
    games.sort(key=lambda g:g.get("date") or "",reverse=True)
    payload={
        "updatedAt":datetime.now(timezone.utc).isoformat(),
        "leagues":{
            "uaap":{
                "league":"UAAP",
                "season":"Season 89 Men's Basketball",
                "sourceName":"UAAP Basketball Live Stats",
                "sourceUrl":UAAP_BASE,
                "gameCount":len(games),
                "leaders":aggregate(games),
                "latestGame":games[0],
                "games":games[:12]
            }
        }
    }
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("UAAP games",len(games),"latest",games[0]["gameId"],games[0]["teams"])

if __name__=="__main__":
    main()
