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

def espn_leader_group(sport,league,title,suffix,sort_field,stat_aliases,season=None,seasontype=2,category=None):
    base=f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/statistics/byathlete"
    params={
        "region":"us","lang":"en","contentorigin":"espn","isqualified":"false",
        "page":"1","limit":"50","sort":sort_field+":desc"
    }
    if season is not None:params["season"]=str(season)
    if seasontype is not None:params["seasontype"]=str(seasontype)
    if category:params["category"]=category
    url=base+"?"+urllib.parse.urlencode(params)
    data=fetch_json(url)
    aliases={str(x).lower() for x in stat_aliases}
    aliases.add(str(sort_field).split(".")[-1].lower())
    rows=[]

    category_defs=data.get("categories",[]) or []
    for item in data.get("athletes",[]) or []:
        athlete=item.get("athlete") or {}
        player=clean(athlete.get("displayName") or athlete.get("fullName") or athlete.get("shortName"))
        if not player:continue
        team_obj=athlete.get("team") or {}
        if isinstance(team_obj,dict):
            team=clean(team_obj.get("abbreviation") or team_obj.get("shortDisplayName") or team_obj.get("displayName"))
        else:
            team=""
        team=team or clean(athlete.get("teamShortName") or athlete.get("teamAbbreviation"))

        chosen_value=None
        chosen_display=""

        # Newer common/v3 response shape.
        stats=item.get("statistics",[]) or []
        for stat in stats:
            if clean(stat.get("name")).lower() in aliases:
                chosen_value=stat.get("value")
                if chosen_value is None:chosen_value=stat.get("displayValue")
                chosen_display=clean(stat.get("displayValue"))
                break
        if chosen_value is None and len(stats)==1:
            stat=stats[0]
            chosen_value=stat.get("value")
            if chosen_value is None:chosen_value=stat.get("displayValue")
            chosen_display=clean(stat.get("displayValue"))

        # Older/common alternate response shape: top-level category definitions
        # plus athlete.categories[].totals.
        if chosen_value is None:
            item_categories=item.get("categories",[]) or []
            for idx,cat in enumerate(item_categories):
                meta=category_defs[idx] if idx<len(category_defs) else {}
                names=meta.get("names") or cat.get("names") or []
                labels=meta.get("labels") or cat.get("labels") or []
                displays=meta.get("displayNames") or cat.get("displayNames") or []
                totals=cat.get("totals") or []
                normalized=[clean(x).lower() for x in names]
                match_idx=None
                for alias in aliases:
                    if alias in normalized:
                        match_idx=normalized.index(alias);break
                if match_idx is None:
                    # Some feeds omit canonical names but expose short labels/display names.
                    combined=[clean(x).lower() for x in displays]
                    for alias in aliases:
                        if alias in combined:
                            match_idx=combined.index(alias);break
                if match_idx is None:
                    alias_tokens={re.sub(r"[^a-z0-9]","",x) for x in aliases}
                    compact=[re.sub(r"[^a-z0-9]","",clean(x).lower()) for x in labels]
                    for token in alias_tokens:
                        if token in compact:
                            match_idx=compact.index(token);break
                if match_idx is not None and match_idx<len(totals):
                    chosen_value=totals[match_idx]
                    chosen_display=clean(totals[match_idx])
                    break

        parsed=num(chosen_value)
        if parsed is None:continue
        rows.append({
            "player":player,"team":team,"gp":None,
            "value":parsed,"displayValue":chosen_display or display_number(parsed)
        })

    if not rows:
        raise ValueError(f"No ESPN {league} {title} leaders returned")
    return {"title":title,"suffix":suffix,"rows":rows[:8],"sourceUrl":url}

def espn_multi_group_stats(sport,league,label,season_label,season,definitions):
    groups=[]
    source_urls=[]
    errors=[]
    for definition in definitions:
        title,suffix,sort_field,aliases,*rest=definition
        category=rest[0] if rest else None
        try:
            group=espn_leader_group(sport,league,title,suffix,sort_field,aliases,season,2,category)
            source_urls.append(group.pop("sourceUrl",""))
            groups.append(group)
        except Exception as ex:
            errors.append(title+": "+type(ex).__name__+" "+str(ex))
    if not groups:
        raise ValueError("; ".join(errors) or f"No {label} leader groups")
    return {
        "league":label,"season":season_label,
        "sourceName":"ESPN public statistics feed",
        "sourceUrl":next((x for x in source_urls if x),""),
        "groups":groups
    }

def espn_basketball_html(key,season_label):
    url="https://www.espn.com/nba/stats/player" if key=="basketball" else "https://www.espn.com/wnba/stats/player"
    soup=BeautifulSoup(fetch(url),"html.parser")
    name_table=None
    stat_table=None
    for table in soup.find_all("table"):
        headers=[]
        for tr in table.find_all("tr")[:4]:
            vals=[clean(x.get_text(" ",strip=True)).upper() for x in tr.find_all(["th","td"])]
            if len(vals)>len(headers):headers=vals
        joined=" ".join(headers)
        if "RK" in headers and "NAME" in headers:name_table=table
        if "PTS" in headers and "REB" in headers and "AST" in headers and "STL" in headers and "BLK" in headers:
            stat_table=table
    if not name_table or not stat_table:
        raise ValueError("ESPN player statistics tables not found")

    names=[]
    for tr in name_table.find_all("tr"):
        cells=tr.find_all(["th","td"])
        vals=[clean(x.get_text(" ",strip=True)) for x in cells]
        if not vals or any(v.upper()=="NAME" for v in vals):continue
        if len(cells)<2:continue
        name_cell=cells[-1]
        links=[clean(a.get_text(" ",strip=True)) for a in name_cell.find_all("a") if clean(a.get_text(" ",strip=True))]
        player=links[0] if links else ""
        raw=clean(name_cell.get_text(" ",strip=True))
        if not player:
            m=re.match(r"(.+?)\s+([A-Z]{2,5}(?:/[A-Z]{2,5})?)$",raw)
            if m:player,team=clean(m.group(1)),m.group(2)
            else:continue
        else:
            team=clean(raw.replace(player,"",1))
        names.append({"player":player,"team":team})

    header=[]
    data_rows=[]
    started=False
    for tr in stat_table.find_all("tr"):
        cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
        upper=[x.upper() for x in cells]
        if "PTS" in upper and "REB" in upper and "AST" in upper:
            header=cells;started=True;continue
        if started and cells:data_rows.append(cells)
    if not header or not data_rows:raise ValueError("ESPN statistic rows not found")
    index={h.upper():i for i,h in enumerate(header)}
    def at(row,name):
        i=index.get(name.upper())
        return row[i] if i is not None and i<len(row) else ""
    rows=[]
    for identity,values in zip(names,data_rows):
        pts=num(at(values,"PTS"))
        if pts is None:continue
        rows.append({
            "player":identity["player"],"team":identity["team"],
            "gp":intnum(at(values,"GP")),
            "ppg":pts,"rpg":num(at(values,"REB")),"apg":num(at(values,"AST")),
            "spg":num(at(values,"STL")),"bpg":num(at(values,"BLK"))
        })
    groups=generic_groups(rows,[
        ("Points","ppg","PPG"),("Rebounds","rpg","RPG"),("Assists","apg","APG"),
        ("Steals","spg","SPG"),("Blocks","bpg","BPG")
    ])
    if not groups:raise ValueError("ESPN basketball groups empty")
    return {
        "league":"NBA" if key=="basketball" else "WNBA",
        "season":season_label,
        "sourceName":"ESPN",
        "sourceUrl":url,
        "groups":groups
    }

def espn_basketball_stats(key,league,season,season_label):
    label="NBA" if key=="basketball" else "WNBA"
    try:
        return espn_multi_group_stats("basketball",league,label,season_label,season,[
            ("Points","PPG","offensive.avgPoints",["avgPoints"]),
            ("Rebounds","RPG","general.avgRebounds",["avgRebounds"]),
            ("Assists","APG","offensive.avgAssists",["avgAssists"]),
            ("Steals","SPG","defensive.avgSteals",["avgSteals"]),
            ("Blocks","BPG","defensive.avgBlocks",["avgBlocks"])
        ])
    except Exception as ex:
        primary=type(ex).__name__+": "+str(ex)[:900]
        print("ESPN sorted",key,primary)
        try:
            return espn_basketball_html(key,season_label)
        except Exception as fallback:
            raise ValueError(primary+" | HTML "+type(fallback).__name__+": "+str(fallback)[:300])

def espn_soccer_html_stats():
    url="https://www.espn.com/soccer/stats?league=USA.1"
    soup=BeautifulSoup(fetch(url),"html.parser")
    tables=soup.find_all("table")
    groups=[]
    pending_names=[]

    def headers_and_row(table):
        for tr in table.find_all("tr"):
            vals=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            upper=[v.upper() for v in vals]
            if "NAME" in upper or ("P" in upper and ("G" in upper or "A" in upper)):
                return vals,tr
        return [],None

    def identities(table,header,row):
        index={clean(h).upper():i for i,h in enumerate(header)}
        ni=index.get("NAME");ti=index.get("TEAM")
        if ni is None:return []
        out=[];active=False
        for tr in table.find_all("tr"):
            if tr is row:active=True;continue
            if not active:continue
            cells=tr.find_all(["th","td"])
            vals=[clean(x.get_text(" ",strip=True)) for x in cells]
            if ni>=len(vals):continue
            name_cell=cells[ni]
            links=[clean(a.get_text(" ",strip=True)) for a in name_cell.find_all("a") if clean(a.get_text(" ",strip=True))]
            player=links[0] if links else vals[ni]
            team=vals[ti] if ti is not None and ti<len(vals) else ""
            if player and player.upper()!="NAME":out.append({"player":player,"team":team})
        return out

    def metrics(table,header,row,metric):
        index={clean(h).upper():i for i,h in enumerate(header)}
        pi=index.get("P");mi=index.get(metric)
        if mi is None:return []
        out=[];active=False
        for tr in table.find_all("tr"):
            if tr is row:active=True;continue
            if not active:continue
            vals=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            if mi>=len(vals):continue
            value=num(vals[mi])
            if value is None:continue
            gp=intnum(vals[pi]) if pi is not None and pi<len(vals) else None
            out.append({"gp":gp,"value":value,"displayValue":display_number(value)})
        return out

    for table in tables:
        header,row=headers_and_row(table)
        if not header or row is None:continue
        upper=[x.upper() for x in header]
        has_names="NAME" in upper
        metric="G" if "G" in upper else ("A" if "A" in upper else "")

        if has_names:
            ids=identities(table,header,row)
            if ids:pending_names=ids
            if metric and ids:
                vals=metrics(table,header,row,metric)
                rows=[]
                for identity,value in zip(ids,vals):
                    rows.append({**identity,**value})
                if rows:
                    title="Goals" if metric=="G" else "Assists"
                    groups.append({"title":title,"suffix":metric,"rows":rows[:8]})
                    pending_names=[]
            continue

        if metric and pending_names:
            vals=metrics(table,header,row,metric)
            rows=[]
            for identity,value in zip(pending_names,vals):
                rows.append({**identity,**value})
            if rows:
                title="Goals" if metric=="G" else "Assists"
                groups.append({"title":title,"suffix":metric,"rows":rows[:8]})
                pending_names=[]

    dedup=[]
    seen=set()
    for group in groups:
        if group["title"] in seen:continue
        seen.add(group["title"]);dedup.append(group)
    if not dedup:
        raise ValueError("ESPN MLS statistics tables not parsed")
    return {
        "league":"MLS","season":"2026 Regular Season",
        "sourceName":"ESPN","sourceUrl":url,"groups":dedup
    }

def _deep_find_exact(obj,names):
    wanted={re.sub(r"[^a-z0-9]","",str(x).lower()) for x in names}
    if isinstance(obj,dict):
        for key,value in obj.items():
            nk=re.sub(r"[^a-z0-9]","",str(key).lower())
            if nk in wanted and not isinstance(value,(dict,list)):
                return value
        for value in obj.values():
            found=_deep_find_exact(value,names)
            if found is not None:return found
    elif isinstance(obj,list):
        for value in obj:
            found=_deep_find_exact(value,names)
            if found is not None:return found
    return None

def _deep_find_dict(obj,names):
    wanted={re.sub(r"[^a-z0-9]","",str(x).lower()) for x in names}
    if isinstance(obj,dict):
        for key,value in obj.items():
            nk=re.sub(r"[^a-z0-9]","",str(key).lower())
            if nk in wanted and isinstance(value,dict):
                return value
        for value in obj.values():
            found=_deep_find_dict(value,names)
            if found is not None:return found
    elif isinstance(obj,list):
        for value in obj:
            found=_deep_find_dict(value,names)
            if found is not None:return found
    return None

def _candidate_dict_lists(obj):
    found=[]
    if isinstance(obj,list):
        if obj and all(isinstance(x,dict) for x in obj):
            found.append(obj)
        for value in obj:
            found.extend(_candidate_dict_lists(value))
    elif isinstance(obj,dict):
        for value in obj.values():
            found.extend(_candidate_dict_lists(value))
    return found

def _mls_player_name(row):
    player=_deep_find_dict(row,["player","athlete"])
    target=player or row
    name=_deep_find_exact(target,[
        "displayName","fullName","playerName","playerFullName","commonName","name"
    ])
    if name and not str(name).isdigit():return clean(name)
    first=_deep_find_exact(target,["firstName","playerFirstName","first_name"])
    last=_deep_find_exact(target,["lastName","playerLastName","last_name"])
    return clean(" ".join(str(x) for x in [first,last] if x))

def _mls_club_name(row):
    club=_deep_find_dict(row,["club","team"])
    target=club or row
    value=_deep_find_exact(target,[
        "clubName","teamName","displayName","shortDisplayName","shortName","name","abbreviation"
    ])
    return clean(value)

def mls_official_stats():
    urls=[
        "https://stats-api.mlssoccer.com/players/competitions/MLS-COM-000001/seasons/MLS-SEA-0001KA?per_page=1000",
        "https://stats-api.mlssoccer.com/v1/players/seasons?season_opta_id=2026&competition_opta_id=98&page=0&page_size=1000&include=player&include=club"
    ]
    errors=[]
    for url in urls:
        try:
            data=fetch_json(url)
            lists=_candidate_dict_lists(data)
            lists.sort(key=len,reverse=True)
            parsed=[]
            for items in lists[:8]:
                rows=[]
                for item in items:
                    player=_mls_player_name(item)
                    if not player:continue
                    goals=num(_deep_find_exact(item,[
                        "goals","totalGoals","goalsScored","playerSeasonStatGoals","player_season_stat_goals"
                    ]))
                    assists=num(_deep_find_exact(item,[
                        "assists","totalAssists","playerSeasonStatAssists","player_season_stat_assists"
                    ]))
                    gp=intnum(_deep_find_exact(item,[
                        "appearances","gamesPlayed","matchesPlayed","playerSeasonStatAppearances",
                        "player_season_stat_appearances","gp"
                    ]))
                    if goals is None and assists is None:continue
                    rows.append({
                        "player":player,"team":_mls_club_name(item),"gp":gp,
                        "goals":goals if goals is not None else 0,
                        "assists":assists if assists is not None else 0
                    })
                if len(rows)>len(parsed):parsed=rows
            if not parsed:
                raise ValueError("No player season rows found")
            unique={}
            for row in parsed:
                key=(row["player"].lower(),row["team"].lower())
                old=unique.get(key)
                if old is None or (row["goals"]+row["assists"])>(old["goals"]+old["assists"]):
                    unique[key]=row
            rows=list(unique.values())
            groups=generic_groups(rows,[
                ("Goals","goals","G"),
                ("Assists","assists","A")
            ])
            if not groups:raise ValueError("MLS Official groups empty")
            return {
                "league":"MLS","season":"2026 Regular Season",
                "sourceName":"MLS Official","sourceUrl":"https://www.mlssoccer.com/competitions/mls-regular-season/2026/stats/",
                "groups":groups
            }
        except Exception as ex:
            errors.append(type(ex).__name__+": "+str(ex)[:400])
    raise ValueError(" | ".join(errors))

def mls_pulse_stats():
    url="https://www.themlspulse.com/stats/goal-contributions"
    soup=BeautifulSoup(fetch(url),"html.parser")
    rows=[]

    for table in soup.find_all("table"):
        header=[]
        header_row=None
        for tr in table.find_all("tr"):
            vals=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            upper=[v.upper() for v in vals]
            if "PLAYER" in upper and "TEAM" in upper and "GOALS" in upper and "ASSISTS" in upper:
                header=vals;header_row=tr;break
        if not header or header_row is None:continue

        index={clean(h).upper():i for i,h in enumerate(header)}
        pi=index.get("PLAYER");ti=index.get("TEAM");gi=index.get("GOALS");ai=index.get("ASSISTS");appi=index.get("APPS")
        active=False
        for tr in table.find_all("tr"):
            if tr is header_row:
                active=True
                continue
            if not active:continue
            cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            need=[x for x in [pi,ti,gi,ai] if x is not None]
            if not cells or not need or max(need)>=len(cells):continue
            player=cells[pi] if pi is not None else ""
            team=cells[ti] if ti is not None else ""
            goals=num(cells[gi]) if gi is not None else None
            assists=num(cells[ai]) if ai is not None else None
            gp=intnum(cells[appi]) if appi is not None and appi<len(cells) else None
            if not player or goals is None or assists is None:continue
            rows.append({"player":player,"team":team,"gp":gp,"goals":goals,"assists":assists})
        if rows:break

    if not rows:
        # Some deployments render the leaderboard as repeated text blocks rather than a table.
        text=clean(soup.get_text("\n",strip=True))
        pattern=re.compile(
            r"(?:^|\n)\s*\d+\s*\n\s*([^\n]+)\s*\n\s*([^\n]+)\s*\n\s*(?:GK|DF|MF|FW)\s*\n\s*\d+\s*\n\s*(\d+)\s*\n\s*(\d+)\s*\n\s*(\d+)",
            re.M
        )
        for player,team,goals,assists,apps in pattern.findall(text):
            rows.append({
                "player":clean(player),"team":clean(team),"gp":intnum(apps),
                "goals":num(goals),"assists":num(assists)
            })

    if not rows:raise ValueError("MLS Pulse leaderboard not parsed")

    groups=generic_groups(rows,[
        ("Goals","goals","G"),
        ("Assists","assists","A")
    ])
    if not groups:raise ValueError("MLS Pulse groups empty")
    return {
        "league":"MLS","season":"2026 Regular Season",
        "sourceName":"The MLS Pulse · ESPN-sourced player data",
        "sourceUrl":url,"groups":groups
    }

def espn_mls_core_stats():
    url="https://sports.core.api.espn.com/v2/sports/soccer/leagues/usa.1/seasons/2026/leaders"
    data=fetch_json(url)
    categories=data.get("categories",[]) or []
    groups=[]
    wanted=[
        ("Goals","G",{"goals","totalgoals","goalsleader"}),
        ("Assists","A",{"assists","totalassists","assistsleader"})
    ]
    for title,suffix,names in wanted:
        category=None
        for item in categories:
            tokens={
                clean(item.get("name")).lower().replace(" ",""),
                clean(item.get("displayName")).lower().replace(" ",""),
                clean(item.get("shortDisplayName")).lower().replace(" ",""),
                clean(item.get("abbreviation")).lower().replace(" ","")
            }
            if tokens & names or any(name in token for token in tokens for name in names):
                category=item;break
        if not category:continue
        rows=[]
        for leader in (category.get("leaders",[]) or [])[:8]:
            athlete=leader.get("athlete") or {}
            if athlete.get("$ref"):
                try:athlete=fetch_json(str(athlete["$ref"]).replace("http://","https://"))
                except:athlete={}
            player=clean(athlete.get("displayName") or athlete.get("fullName") or athlete.get("shortName"))
            if not player:continue
            team_obj=leader.get("team") or athlete.get("team") or {}
            if isinstance(team_obj,dict) and team_obj.get("$ref"):
                try:team_obj=fetch_json(str(team_obj["$ref"]).replace("http://","https://"))
                except:team_obj={}
            team=clean(team_obj.get("displayName") or team_obj.get("shortDisplayName") or team_obj.get("abbreviation")) if isinstance(team_obj,dict) else ""
            value=leader.get("value")
            if value is None:value=num(leader.get("displayValue"))
            if value is None:continue
            rows.append({
                "player":player,"team":team,"gp":None,
                "value":value,"displayValue":display_number(value)
            })
        if rows:groups.append({"title":title,"suffix":suffix,"rows":rows})
    titles={g.get("title") for g in groups}
    if "Goals" not in titles or "Assists" not in titles:
        raise ValueError("MLS core leaders missing goals or assists")
    return {
        "league":"MLS","season":"2026 Regular Season",
        "sourceName":"ESPN public statistics feed","sourceUrl":url,
        "groups":groups
    }

def espn_mls_stats():
    errors=[]
    try:
        return espn_mls_core_stats()
    except Exception as ex:
        errors.append("ESPN Core "+type(ex).__name__+": "+str(ex)[:600])
    try:
        return mls_official_stats()
    except Exception as ex:
        errors.append("MLS Official "+type(ex).__name__+": "+str(ex)[:600])
    try:
        return mls_pulse_stats()
    except Exception as ex:
        errors.append("MLS Pulse "+type(ex).__name__+": "+str(ex)[:600])
    definitions=[
        ("Goals","G","offensive.totalGoals",["goals","totalGoals"],"scoring"),
        ("Assists","A","offensive.assists",["assists","totalAssists"],"scoring")
    ]
    try:
        data=espn_multi_group_stats("soccer","usa.1","MLS","2026 Regular Season",2026,definitions)
        titles={g.get("title") for g in data.get("groups",[])}
        if "Goals" in titles and "Assists" in titles:
            return data
        errors.append("ESPN feed missing one or more MLS groups")
    except Exception as ex:
        errors.append("ESPN "+type(ex).__name__+": "+str(ex)[:500])
    try:
        return espn_soccer_html_stats()
    except Exception as ex:
        errors.append("ESPN HTML "+type(ex).__name__+": "+str(ex)[:500])
    raise ValueError(" | ".join(errors))

def espn_epl_stats():
    league="eng.1"
    season=2026
    url=f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{league}/seasons/{season}/leaders"
    data=fetch_json(url)
    categories=data.get("categories",[]) or []
    wanted=[
        ("Goals","G",{"goals","totalgoals","goalsleader"}),
        ("Assists","A",{"assists","totalassists","assistsleader"})
    ]
    groups=[]
    for title,suffix,names in wanted:
        category=None
        for item in categories:
            tokens={
                clean(item.get("name")).lower().replace(" ",""),
                clean(item.get("displayName")).lower().replace(" ",""),
                clean(item.get("shortDisplayName")).lower().replace(" ",""),
                clean(item.get("abbreviation")).lower().replace(" ","")
            }
            if tokens & names or any(name in token for token in tokens for name in names):
                category=item
                break
        if not category:
            continue
        rows=[]
        for leader in (category.get("leaders",[]) or [])[:8]:
            athlete=leader.get("athlete") or {}
            if athlete.get("$ref"):
                try:
                    athlete=fetch_json(str(athlete["$ref"]).replace("http://","https://"))
                except Exception:
                    athlete={}
            player=clean(athlete.get("displayName") or athlete.get("fullName") or athlete.get("shortName"))
            if not player:
                continue
            team_obj=leader.get("team") or athlete.get("team") or {}
            if isinstance(team_obj,dict) and team_obj.get("$ref"):
                try:
                    team_obj=fetch_json(str(team_obj["$ref"]).replace("http://","https://"))
                except Exception:
                    team_obj={}
            team=clean(team_obj.get("displayName") or team_obj.get("shortDisplayName") or team_obj.get("abbreviation")) if isinstance(team_obj,dict) else ""
            value=leader.get("value")
            if value is None:
                value=num(leader.get("displayValue"))
            if value is None:
                continue
            rows.append({"player":player,"team":team,"gp":None,"value":value,"displayValue":display_number(value)})
        if rows:
            groups.append({"title":title,"suffix":suffix,"rows":rows})
    if not groups:
        raise ValueError("EPL statistics leaders not returned")
    return {
        "league":"Premier League",
        "season":"2026–27",
        "sourceName":"ESPN public statistics feed",
        "sourceUrl":url,
        "groups":groups
    }


def espn_hockey_stats():
    return espn_multi_group_stats("hockey","nhl","NHL","2025–26 Regular Season",2026,[
        ("Points","PTS","offensive.points",["points"],"skaters"),
        ("Goals","G","offensive.goals",["goals"],"skaters"),
        ("Assists","A","offensive.assists",["assists"],"skaters")
    ])

def espn_baseball_stats():
    return espn_multi_group_stats("baseball","mlb","MLB","2026 Regular Season",2026,[
        ("Home Runs","HR","batting.homeRuns",["homeRuns"],"batting"),
        ("Runs Batted In","RBI","batting.RBIs",["RBIs","rbi","runsBattedIn"],"batting"),
        ("Batting Average","AVG","batting.avg",["battingAverage","avg"],"batting"),
        ("Stolen Bases","SB","batting.stolenBases",["stolenBases"],"batting")
    ])

def espn_football_stats(key,league,label):
    return espn_multi_group_stats("football",league,label,"2026 Regular Season",2026,[
        ("Passing Yards","YDS","passing.passingYards",["passingYards"],"offense:passing"),
        ("Passing TDs","TD","passing.passingTouchdowns",["passingTouchdowns","passingTDs"],"offense:passing"),
        ("Rushing Yards","YDS","rushing.rushingYards",["rushingYards"],"offense:rushing"),
        ("Receiving Yards","YDS","receiving.receivingYards",["receivingYards"],"offense:receiving")
    ])

def parse_pba_stats():
    url="https://www.pba.ph/stats"
    soup=BeautifulSoup(fetch(url),"html.parser")
    rows=[]

    target=None
    headers=[]
    for table in soup.find_all("table"):
        for row in table.find_all("tr")[:5]:
            vals=[clean(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"])]
            upper=[v.upper() for v in vals]
            if "PLAYERS" in upper and "PTS" in upper and "APG" in upper and "REB" in upper:
                target=table;headers=vals;break
        if target:break
    if target:
        index={h.upper():i for i,h in enumerate(headers) if h}
        def cell(cells,name):
            i=index.get(name.upper())
            return cells[i] if i is not None and i<len(cells) else ""
        started=False
        for tr in target.find_all("tr"):
            cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["th","td"])]
            upper=[x.upper() for x in cells]
            if "PLAYERS" in upper and "PTS" in upper:
                started=True;continue
            if not started or not cells:continue
            player=cell(cells,"PLAYERS") or cells[0]
            gp=intnum(cell(cells,"GP"));pts=num(cell(cells,"PTS"))
            if not player or gp is None or pts is None:continue
            rows.append({"player":player,"team":"","gp":gp,"ppg":pts,
                "rpg":num(cell(cells,"REB")),"apg":num(cell(cells,"APG")),
                "spg":num(cell(cells,"STL")),"bpg":num(cell(cells,"BLK"))})

    if not rows:
        seen=set()
        for a in soup.find_all("a",href=True):
            href=str(a.get("href") or "")
            if "/players/" not in href:continue
            player=clean(a.get_text(" ",strip=True))
            if not player or player.lower() in {"players","player"} or player in seen:continue
            node=a
            candidate=None
            for _ in range(7):
                node=node.parent
                if node is None:break
                links=[x for x in node.find_all("a",href=True) if "/players/" in str(x.get("href") or "")]
                nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?",clean(node.get_text(" ",strip=True)))
                if len(links)==1 and 21<=len(nums)<=28:
                    candidate=nums;break
            if not candidate:continue
            vals=[num(x) for x in candidate]
            if len(vals)<21:continue
            gp=int(vals[0]) if vals[0] is not None else None
            if gp is None or vals[20] is None:continue
            rows.append({
                "player":player,"team":"","gp":gp,
                "ppg":vals[20],"apg":vals[11],"spg":vals[12],
                "bpg":vals[13],"rpg":vals[16]
            })
            seen.add(player)

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
        ("soccer",espn_epl_stats),
        ("mls",espn_mls_stats),
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
