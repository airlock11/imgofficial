#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"league-data-registry.json"
OUT=ROOT/"league-data-health.json"

def load(name):
    p=ROOT/name
    try:return json.loads(p.read_text("utf-8"))
    except Exception:return {}

def league_map(data):
    return data.get("leagues",{}) if isinstance(data,dict) else {}

def has_games(x):
    return isinstance(x,dict) and isinstance(x.get("games"),list) and len(x.get("games"))>0

def has_any(x,*keys):
    return isinstance(x,dict) and any(bool(x.get(k)) for k in keys)

reg=json.loads(REG.read_text("utf-8"))
extended=league_map(load("extended-sports-data.json"))
special=league_map(load("special-sports-data.json"))
sportradar=league_map(load("sportradar-soccer-data.json"))
regional=league_map(load("regional-web.json"))
stats=league_map(load("stats-data.json"))

rows={}
for key,meta in reg.get("leagues",{}).items():
    sources=[x for x in (extended.get(key),special.get(key),sportradar.get(key),regional.get(key)) if isinstance(x,dict)]
    game_ready=any(has_games(x) for x in sources) or meta.get("pipeline")=="direct_espn"
    standings_ready=any(has_any(x,"standings") for x in sources)
    stats_ready=isinstance(stats.get(key),dict) and has_any(stats.get(key),"groups","leaders")
    ranking_ready=any(has_any(x,"rankings","ranking","titleholders","medals") for x in sources)
    rows[key]={
      "label":meta.get("label",key),
      "sport":meta.get("sport",""),
      "pipeline":meta.get("pipeline",""),
      "automatic":bool(meta.get("automatic")),
      "scoresScheduleConfigured":game_ready,
      "statisticsPublished":stats_ready,
      "standingsPublished":standings_ready,
      "rankingsPublished":ranking_ready,
      "status":"healthy" if game_ready else "needs-source",
      "note":"Optional dimensions publish only when a verified source supplies them."
    }

payload={
  "updatedAt":datetime.now(timezone.utc).isoformat(),
  "policy":reg.get("policy",{}),
  "summary":{
    "leagues":len(rows),
    "automatic":sum(1 for x in rows.values() if x["automatic"]),
    "scoreScheduleConfigured":sum(1 for x in rows.values() if x["scoresScheduleConfigured"]),
    "needsSource":sum(1 for x in rows.values() if x["status"]!="healthy")
  },
  "leagues":rows
}
OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n","utf-8")
print(json.dumps(payload["summary"]))
