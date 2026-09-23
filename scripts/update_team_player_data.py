#!/usr/bin/env python3
import json, re, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"team-player-data.json"
SOURCES=ROOT/"team-player-sources.json"
UA="Mozilla/5.0 (compatible; IMG-TeamPlayerBot/1.0; +https://imgofficial.com)"

def fetch_json(url,timeout=20):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/plain,*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8","replace"))

def load_json(path,default):
    try:return json.loads(path.read_text("utf-8"))
    except Exception:return default

def team_key(name):
    return re.sub(r"[^a-z0-9]+","-",str(name or "").lower()).strip("-")

def clean_player(a):
    p={
      "id":str(a.get("id") or ""),
      "name":a.get("displayName") or a.get("fullName") or a.get("name") or "",
      "shortName":a.get("shortName") or "",
      "position":(a.get("position") or {}).get("abbreviation") if isinstance(a.get("position"),dict) else a.get("position") or "",
      "number":a.get("jersey") or a.get("number") or "",
      "age":a.get("age") or "",
      "height":a.get("displayHeight") or a.get("height") or "",
      "weight":a.get("displayWeight") or a.get("weight") or "",
      "headshot":(a.get("headshot") or {}).get("href") if isinstance(a.get("headshot"),dict) else a.get("headshot") or "",
      "profile":next((x.get("href") for x in (a.get("links") or []) if isinstance(x,dict) and x.get("href")), "")
    }
    stats=a.get("statistics") or a.get("stats") or []
    if isinstance(stats,dict): p["stats"]=stats
    elif isinstance(stats,list) and stats: p["stats"]=stats
    return {k:v for k,v in p.items() if v not in ("",None,[])}

def roster_from_payload(j):
    candidates=[]
    for key in ("athletes","items","roster","players"):
        v=j.get(key) if isinstance(j,dict) else None
        if isinstance(v,list): candidates.extend(v)
    out=[]
    for item in candidates:
        if isinstance(item,dict) and isinstance(item.get("items"),list):
            for a in item["items"]:
                if isinstance(a,dict): out.append(clean_player(a))
        elif isinstance(item,dict):
            out.append(clean_player(item.get("athlete") if isinstance(item.get("athlete"),dict) else item))
    seen=set(); result=[]
    for p in out:
        k=p.get("id") or p.get("name")
        if k and k not in seen:
            seen.add(k); result.append(p)
    return result

def espn_teams(sport,league):
    base=f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}"
    j=fetch_json(base+"/teams?limit=100")
    rows=((j.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams") or []
    teams=[]
    for row in rows:
        t=row.get("team",row) if isinstance(row,dict) else {}
        tid=str(t.get("id") or "")
        if not tid: continue
        roster=[]
        for u in (
          f"{base}/teams/{urllib.parse.quote(tid)}/roster",
          f"{base}/teams/{urllib.parse.quote(t.get('slug') or tid)}/roster"
        ):
            try:
                roster=roster_from_payload(fetch_json(u))
                if roster: break
            except Exception: pass
        teams.append({
          "id":tid,"slug":t.get("slug") or team_key(t.get("displayName")),
          "name":t.get("displayName") or t.get("name") or "",
          "abbreviation":t.get("abbreviation") or "",
          "logo":((t.get("logos") or [{}])[0].get("href") if t.get("logos") else t.get("logo") or ""),
          "color":t.get("color") or "",
          "profile":next((x.get("href") for x in (t.get("links") or []) if isinstance(x,dict) and x.get("href")), ""),
          "roster":roster
        })
    return teams

def regional_teams(key):
    rows=[]
    for file in ("regional-web.json","special-sports-data.json","extended-sports-data.json"):
        data=load_json(ROOT/file,{})
        league=(data.get("leagues") or {}).get(key) or {}
        for g in league.get("games") or []:
            for n in (g.get("away"),g.get("home")):
                if n: rows.append(n)
    out=[];seen=set()
    for name in rows:
        k=team_key(name)
        if k and k not in seen:
            seen.add(k);out.append({"id":k,"slug":k,"name":name,"roster":[]})
    return out

def merge_keep_old(new,old):
    oldmap={team_key(t.get("name")):t for t in old or []}
    out=[]
    for t in new:
        o=oldmap.get(team_key(t.get("name")),{})
        if not t.get("roster") and o.get("roster"): t["roster"]=o["roster"]
        out.append(t)
    known={team_key(t.get("name")) for t in out}
    out.extend([t for t in old or [] if team_key(t.get("name")) not in known])
    return out

def main():
    src=load_json(SOURCES,{})
    previous=load_json(OUT,{"leagues":{}})
    result={"updated_at":datetime.now(timezone.utc).isoformat(),"leagues":{}}
    for slug,cfg in (src.get("leagues") or {}).items():
        old=(previous.get("leagues") or {}).get(slug,{})
        entry={
          "name":old.get("name") or slug,
          "mode":cfg.get("mode","teams"),
          "sources":{k:v for k,v in cfg.items() if k in ("teams","players","stats","rankings","youtube","facebook") and v}
        }
        teams=[]
        err=""
        structured=cfg.get("structured")
        if structured and cfg.get("mode")=="teams":
            try: teams=espn_teams(structured["sport"],structured["league"])
            except Exception as ex: err=f"{type(ex).__name__}: {str(ex)[:160]}"
        if not teams and cfg.get("regionalKey"):
            teams=regional_teams(cfg["regionalKey"])
        if cfg.get("mode")=="teams":
            teams=merge_keep_old(teams,old.get("teams") or [])
            entry["teams"]=teams
            entry["team_count"]=len(teams)
            entry["player_count"]=sum(len(t.get("roster") or []) for t in teams)
        else:
            entry["participants"]=old.get("participants") or []
            entry["participant_count"]=len(entry["participants"])
        if err: entry["last_error"]=err
        result["leagues"][slug]=entry
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf-8")

if __name__=="__main__": main()
