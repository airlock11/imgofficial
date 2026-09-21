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


def fetch_json(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":UA,
        "Accept":"application/json,text/plain,*/*",
        "Accept-Language":"en-US,en;q=0.9",
        "Cache-Control":"no-cache"
    })
    with urllib.request.urlopen(req,timeout=25) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def display_number(value):
    if value is None:return "—"
    try:
        n=float(value)
        if math.isfinite(n):
            return str(int(n)) if n.is_integer() else f"{n:.1f}"
    except:pass
    return clean(value) or "—"

def generic_groups(rows, definitions):
    groups=[]
    for title,key,suffix in definitions:
        ranked=[r for r in rows if r.get(key) is not None]
        ranked.sort(key=lambda r:(float(r.get(key) or 0),int(r.get("gp") or 0)),reverse=True)
        if not ranked:continue
        out=[]
        for r in ranked[:8]:
            out.append({
                "player":r.get("player",""),
                "team":r.get("team",""),
                "gp":r.get("gp"),
                "value":r.get(key),
                "displayValue":display_number(r.get(key))
            })
        groups.append({"title":title,"suffix":suffix,"rows":out})
    return groups

def stat_from_map(stats,*aliases):
    for alias in aliases:
        if alias in stats:
            item=stats[alias]
            value=item.get("value") if isinstance(item,dict) else item
            if value is None and isinstance(item,dict):value=item.get("displayValue")
            parsed=num(value)
            if parsed is not None:return parsed
    low={str(k).lower():v for k,v in stats.items()}
    for alias in aliases:
        item=low.get(str(alias).lower())
        if item is None:continue
        value=item.get("value") if isinstance(item,dict) else item
        if value is None and isinstance(item,dict):value=item.get("displayValue")
        parsed=num(value)
        if parsed is not None:return parsed
    return None

def espn_athlete_rows(sport,league,season=None,seasontype=None):
    base=f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/statistics/byathlete"
    params={"limit":"250"}
    if season is not None:params["season"]=str(season)
    if seasontype is not None:params["seasontype"]=str(seasontype)
    url=base+"?"+urllib.parse.urlencode(params)
    data=fetch_json(url)
    rows=[]
    for item in data.get("athletes",[]) or []:
        athlete=item.get("athlete") or {}
        player=clean(athlete.get("displayName") or athlete.get("fullName") or athlete.get("shortName"))
        if not player:continue
        team=athlete.get("team") or {}
        team_name=clean(team.get("abbreviation") or team.get("shortDisplayName") or team.get("displayName"))
        stats={}
        for s in item.get("statistics",[]) or []:
            name=clean(s.get("name"))
            if name:stats[name]=s
        gp=stat_from_map(stats,"gamesPlayed","games","appearances")
        row={
            "player":player,
            "team":team_name,
            "gp":int(gp) if gp is not None else None,
            "ppg":stat_from_map(stats,"avgPoints","pointsPerGame","pointsAverage"),
            "rpg":stat_from_map(stats,"avgRebounds","reboundsPerGame","reboundsAverage","avgTotalRebounds"),
            "apg":stat_from_map(stats,"avgAssists","assistsPerGame","assistsAverage"),
            "spg":stat_from_map(stats,"avgSteals","stealsPerGame","stealsAverage"),
            "bpg":stat_from_map(stats,"avgBlocks","blocksPerGame","blocksAverage"),
            "goals":stat_from_map(stats,"goals","totalGoals"),
            "points":stat_from_map(stats,"points","totalPoints"),
            "assists":stat_from_map(stats,"assists","totalAssists"),
            "homeRuns":stat_from_map(stats,"homeRuns"),
            "rbi":stat_from_map(stats,"RBIs","rbi","runsBattedIn"),
            "battingAverage":stat_from_map(stats,"battingAverage","avg"),
            "passingYards":stat_from_map(stats,"passingYards","passYards"),
            "passingTDs":stat_from_map(stats,"passingTouchdowns","passingTDs","passTouchdowns"),
            "rushingYards":stat_from_map(stats,"rushingYards","rushYards"),
            "receivingYards":stat_from_map(stats,"receivingYards","recYards"),
        }
        rows.append(row)
    season_info=data.get("currentSeason") or {}
    return rows,season_info,url

def espn_basketball_stats(key,league,season,season_label):
    rows,season_info,url=espn_athlete_rows("basketball",league,season,2)
    groups=generic_groups(rows,[
        ("Points","ppg","PPG"),("Rebounds","rpg","RPG"),("Assists","apg","APG"),
        ("Steals","spg","SPG"),("Blocks","bpg","BPG")
    ])
    if not groups:
        raise ValueError(f"No {league.upper()} athlete statistics returned")
    return {
        "league":"NBA" if key=="basketball" else "WNBA",
        "season":season_label,
        "sourceName":"ESPN public statistics feed",
        "sourceUrl":url,
        "groups":groups
    }

def espn_hockey_stats():
    rows,season_info,url=espn_athlete_rows("hockey","nhl",2026,2)
    groups=generic_groups(rows,[("Points","points","PTS"),("Goals","goals","G"),("Assists","assists","A")])
    if not groups:raise ValueError("No NHL athlete statistics returned")
    return {"league":"NHL","season":"2025–26 Regular Season","sourceName":"ESPN public statistics feed","sourceUrl":url,"groups":groups}

def espn_baseball_stats():
    rows,season_info,url=espn_athlete_rows("baseball","mlb",2026,2)
    groups=generic_groups(rows,[("Home Runs","homeRuns","HR"),("Runs Batted In","rbi","RBI"),("Batting Average","battingAverage","AVG")])
    if not groups:raise ValueError("No MLB athlete statistics returned")
    return {"league":"MLB","season":"2026 Regular Season","sourceName":"ESPN public statistics feed","sourceUrl":url,"groups":groups}

def espn_football_stats(key,league,label):
    rows,season_info,url=espn_athlete_rows("football",league,2026,2)
    groups=generic_groups(rows,[("Passing Yards","passingYards","YDS"),("Passing TDs","passingTDs","TD"),("Rushing Yards","rushingYards","YDS"),("Receiving Yards","receivingYards","YDS")])
    if not groups:raise ValueError(f"No {label} athlete statistics returned")
    return {"league":label,"season":"2026 Regular Season","sourceName":"ESPN public statistics feed","sourceUrl":url,"groups":groups}

def parse_pba_stats():
    url="https://www.pba.ph/stats"
    soup=BeautifulSoup(fetch(url),"html.parser")
    target=None
    headers=[]
    for table in soup.find_all("table"):
        rows=table.find_all("tr")
        for row in rows[:5]:
            vals=[clean(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"])]
            upper=[v.upper() for v in vals]
            if "PLAYERS" in upper and "PTS" in upper and "APG" in upper and "REB" in upper:
                target=table;headers=vals;break
        if target:break
    if not target:
        raise ValueError("PBA player statistics table not found")
    index={}
    for i,h in enumerate(headers):
        if h:index[h.upper()]=i
    def cell(cells,name):
        i=index.get(name.upper())
        return cells[i] if i is not None and i<len(cells) else ""
    rows=[]
    started=False
    for tr in target.find_all("tr"):
        cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
        upper=[x.upper() for x in cells]
        if "PLAYERS" in upper and "PTS" in upper:
            started=True
            continue
        if not started or not cells:continue
        player=cell(cells,"PLAYERS") or cells[0]
        gp=intnum(cell(cells,"GP"))
        pts=num(cell(cells,"PTS"))
        if not player or gp is None or pts is None:continue
        rows.append({
            "player":player,"team":"","gp":gp,
            "ppg":pts,"rpg":num(cell(cells,"REB")),
            "apg":num(cell(cells,"APG")),"spg":num(cell(cells,"STL")),
            "bpg":num(cell(cells,"BLK"))
        })
    if not rows:raise ValueError("PBA statistics rows not parsed")
    return {
        "league":"PBA",
        "season":"Current PBA player statistics",
        "sourceName":"PBA Official",
        "sourceUrl":url,
        "groups":generic_groups(rows,[
            ("Points","ppg","PPG"),("Rebounds","rpg","RPG"),("Assists","apg","APG"),
            ("Steals","spg","SPG"),("Blocks","bpg","BPG")
        ])
    }

def parse_nbl_australia_stats():
    url="https://www.nbl.com.au/"
    soup=BeautifulSoup(fetch(url),"html.parser")
    text=clean(soup.get_text(" ",strip=True))
    start=text.lower().find("player leaderboard")
    if start>=0:text=text[start:start+2500]
    found=[]
    pattern=re.compile(r"([A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+){1,4})\s+(\d+(?:\.\d+)?)\s+PPG\b")
    for name,value in pattern.findall(text):
        name=clean(re.sub(r"^Player Leaderboard\s+","",name,flags=re.I))
        if not name or any(x["player"]==name for x in found):continue
        found.append({"player":name,"team":"","gp":None,"value":float(value),"displayValue":display_number(value)})
        if len(found)>=8:break
    if not found:raise ValueError("NBL Australia player leaderboard not parsed")
    return {
        "league":"NBL Australia",
        "season":"NBL27 · 2026–27",
        "sourceName":"NBL Official",
        "sourceUrl":url,
        "groups":[{"title":"Points","suffix":"PPG","rows":found}]
    }

def build_uaap_stats():
    landing=fetch(UAAP_BASE)
    ids=discover_game_ids(landing)
    if not ids:ids=[str(i) for i in range(1,25)]
    ids=ids[-20:]
    games=[]
    for gid in ids:
        try:
            game=parse_game(gid)
            if game:games.append(game)
        except Exception as ex:
            print("UAAP game",gid,type(ex).__name__,str(ex)[:120])
    if not games:raise ValueError("No UAAP statistics parsed")
    games.sort(key=lambda g:g.get("date") or "",reverse=True)
    return {
        "league":"UAAP",
        "season":"Season 89 Men's Basketball",
        "sourceName":"UAAP Basketball Live Stats",
        "sourceUrl":UAAP_BASE,
        "gameCount":len(games),
        "leaders":aggregate(games),
        "latestGame":games[0],
        "games":games[:12]
    }

def load_previous_leagues():
    try:
        data=json.loads(OUT.read_text(encoding="utf-8"))
        return data.get("leagues",{}) if isinstance(data,dict) else {}
    except:return {}

def main():
    previous=load_previous_leagues()
    leagues=dict(previous)
    jobs=[
        ("uaap",build_uaap_stats),
        ("pba",parse_pba_stats),
        ("nblaus",parse_nbl_australia_stats),
        ("basketball",lambda:espn_basketball_stats("basketball","nba",2026,"2025–26 Regular Season")),
        ("wnba",lambda:espn_basketball_stats("wnba","wnba",2026,"2026 Regular Season")),
        ("baseball",espn_baseball_stats),
        ("hockey",espn_hockey_stats),
        ("football",lambda:espn_football_stats("football","nfl","NFL")),
        ("ncaaf",lambda:espn_football_stats("ncaaf","college-football","NCAA Football")),
    ]
    updated=[]
    for key,builder in jobs:
        try:
            value=builder()
            if value and (value.get("groups") or value.get("leaders")):
                leagues[key]=value
                updated.append(key)
                print("Updated",key)
            else:
                print("No usable statistics",key)
        except Exception as ex:
            print("Statistics",key,type(ex).__name__,str(ex)[:180])
            if key not in previous:
                leagues.pop(key,None)
    payload={"updatedAt":datetime.now(timezone.utc).isoformat(),"leagues":leagues}
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Statistics leagues",",".join(sorted(leagues.keys())),"updated",",".join(updated))

if __name__=="__main__":
    main()
