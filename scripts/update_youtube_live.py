#!/usr/bin/env python3
import json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

KEY=os.environ["YOUTUBE_API_KEY"]
OUT=Path(__file__).resolve().parents[1]/"youtube-live.json"
UA="IMG-Sports-Live/1.0"
SCOREBOARDS={
 "Basketball":"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
 "Football":"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard",
 "Baseball":"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
 "Hockey":"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
 "American Football":"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
}
def get_json(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
def tokens(s):
 return {x for x in re.findall(r"[a-z0-9]+",str(s).lower()) if len(x)>2 and x not in {"live","vs","the","game","official"}}
def live_events():
 out=[]
 for sport,url in SCOREBOARDS.items():
  try:
   for e in get_json(url).get("events",[]):
    if e.get("status",{}).get("type",{}).get("state")!="in":continue
    c=(e.get("competitions") or [{}])[0]
    teams=[x.get("team",{}).get("displayName","") for x in c.get("competitors",[])]
    if len(teams)>=2:out.append({"eventId":str(e.get("id","")),"sport":sport,"teams":teams[:2],"title":e.get("name","")})
  except Exception as ex: print("scoreboard",sport,ex)
 return out[:10]
def search(event):
 q=" ".join(event["teams"])+" live"
 params=urllib.parse.urlencode({"part":"snippet","type":"video","eventType":"live","maxResults":5,"q":q,"key":KEY})
 data=get_json("https://www.googleapis.com/youtube/v3/search?"+params)
 wanted=tokens(" ".join(event["teams"]))
 best=None
 for item in data.get("items",[]):
  vid=item.get("id",{}).get("videoId"); sn=item.get("snippet",{}); title=sn.get("title","")
  overlap=len(wanted & tokens(title))
  if not vid or overlap<2:continue
  cand={"videoId":vid,"watchUrl":"https://www.youtube.com/watch?v="+vid,"embedUrl":"https://www.youtube.com/embed/"+vid,"provider":"YouTube","channel":sn.get("channelTitle",""),"title":title,"matchScore":overlap}
  if not best or cand["matchScore"]>best["matchScore"]:best=cand
 return best

def asian_games_streams():
 params=urllib.parse.urlencode({"part":"snippet","type":"video","eventType":"live","maxResults":25,"q":"2026 ASIAN GAMES One Sports","key":KEY})
 data=get_json("https://www.googleapis.com/youtube/v3/search?"+params)
 found=[]
 for item in data.get("items",[]):
  vid=item.get("id",{}).get("videoId"); sn=item.get("snippet",{}); title=sn.get("title",""); channel=sn.get("channelTitle","")
  if not vid or "2026 ASIAN GAMES" not in title.upper() or channel.strip().lower()!="one sports": continue
  found.append({"eventId":"ag26-youtube-"+vid,"sport":"Asian Games","teams":[],"title":title,"stream":{"videoId":vid,"watchUrl":"https://www.youtube.com/watch?v="+vid,"embedUrl":"https://www.youtube.com/embed/"+vid,"provider":"YouTube","channel":channel,"title":title,"matchScore":99}})
 return found

events=live_events(); streams=[]
for e in events:
 try:
  s=search(e)
  if s: streams.append({**e,"stream":s})
 except Exception as ex: print("youtube",e["title"],ex)
OUT.write_text(json.dumps({"updatedAt":datetime.now(timezone.utc).isoformat(),"streams":streams},indent=2)+"\n",encoding="utf-8")
print("live events",len(events),"matched streams",len(streams))
