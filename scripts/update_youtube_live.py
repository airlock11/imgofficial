#!/usr/bin/env python3
import json, os, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import html as html_lib
from datetime import datetime, timezone
from pathlib import Path

KEY=os.environ["YOUTUBE_API_KEY"]
OUT=Path(__file__).resolve().parents[1]/"youtube-live.json"
UA="IMG-Sports-Live/1.0"
ONE_SPORTS_CHANNEL_ID="UCXDG9ue-emCN8Ad3h7lERqQ"
PINNED_ASIAN_GAMES_VIDEO_IDS=["5mZlZtTk83E"]
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
def youtube_search(q="", max_results=25, channel_id=None):
 params={"part":"snippet","type":"video","eventType":"live","maxResults":max_results,"key":KEY}
 if q: params["q"]=q
 if channel_id: params["channelId"]=channel_id
 return get_json("https://www.googleapis.com/youtube/v3/search?"+urllib.parse.urlencode(params)).get("items",[])

def video_details(ids):
 if not ids:return {}
 params=urllib.parse.urlencode({"part":"snippet,status,liveStreamingDetails","id":",".join(ids),"key":KEY})
 data=get_json("https://www.googleapis.com/youtube/v3/videos?"+params)
 return {x["id"]:x for x in data.get("items",[])}

def channel_feed_ids(channel_id):
 url="https://www.youtube.com/feeds/videos.xml?channel_id="+urllib.parse.quote(channel_id)
 req=urllib.request.Request(url,headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=20) as r:
  root=ET.fromstring(r.read())
 ns={"yt":"http://www.youtube.com/xml/schemas/2015","atom":"http://www.w3.org/2005/Atom"}
 return [e.text for e in root.findall(".//yt:videoId",ns) if e.text]

def channel_stream_page_ids(channel_id):
 url="https://www.youtube.com/channel/"+urllib.parse.quote(channel_id)+"/streams"
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
 with urllib.request.urlopen(req,timeout=20) as r:
  html=r.read().decode("utf-8","ignore")
 return list(dict.fromkeys(re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"',html)))

def public_watch_info(video_id):
 url="https://www.youtube.com/watch?v="+urllib.parse.quote(video_id)
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept-Language":"en-US,en;q=0.9"})
 with urllib.request.urlopen(req,timeout=20) as r:
  page=r.read().decode("utf-8","ignore")
 live=('"isLiveNow":true' in page) and ('"isLive":true' in page or '"liveBroadcastDetails"' in page or '"isLiveNow":true' in page)
 mt=re.search(r'<meta\s+name="title"\s+content="([^"]*)"',page,re.I) or re.search(r'<title>(.*?)</title>',page,re.I|re.S)
 title=html_lib.unescape((mt.group(1) if mt else "").replace(" - YouTube","").strip())
 mc=re.search(r'"ownerChannelName":"([^"]+)"',page)
 channel=html_lib.unescape(mc.group(1)) if mc else ""
 return {"title":title,"channel":channel,"live":live}

def search(event):
 wanted=tokens(" ".join(event["teams"]))
 best=None
 for item in youtube_search(" ".join(event["teams"])+" live",5):
  vid=item.get("id",{}).get("videoId"); sn=item.get("snippet",{}); title=sn.get("title","")
  overlap=len(wanted & tokens(title))
  if not vid or overlap<2:continue
  cand={"videoId":vid,"watchUrl":"https://www.youtube.com/watch?v="+vid,"embedUrl":"https://www.youtube.com/embed/"+vid,"provider":"YouTube","channel":sn.get("channelTitle",""),"title":title,"matchScore":overlap}
  if not best or cand["matchScore"]>best["matchScore"]:best=cand
 return best

def one_sports_live():
 # Discover current One Sports broadcasts directly from its public channel surfaces.
 # Classify only the leagues IMG is explicitly tracking here.
 ids=[]
 try:
  ids += channel_feed_ids(ONE_SPORTS_CHANNEL_ID)
 except Exception as ex:
  print("One Sports feed",ex)
 try:
  ids += channel_stream_page_ids(ONE_SPORTS_CHANNEL_ID)
 except Exception as ex:
  print("One Sports streams page",ex)
 ids=PINNED_ASIAN_GAMES_VIDEO_IDS + ids
 ids=list(dict.fromkeys(x for x in ids if x))
 details=video_details(ids[:50])
 out=[]
 for vid in ids[:50]:
  d=details.get(vid)
  if d:
   dsn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
   title=dsn.get("title",""); channel=(dsn.get("channelTitle") or "").strip()
   is_live=dsn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
   ended=bool(live.get("actualEndTime"))
   embeddable=status.get("embeddable",True)
  else:
   try:
    info=public_watch_info(vid)
   except Exception as ex:
    if vid in PINNED_ASIAN_GAMES_VIDEO_IDS: print("Pinned public page",vid,ex)
    continue
   title=info["title"]; channel=info["channel"]; is_live=info["live"]; ended=False; embeddable=True
  if vid in PINNED_ASIAN_GAMES_VIDEO_IDS:
   print("Pinned stream diagnostic",vid,repr(title),repr(channel),"live=",bool(is_live),"ended=",bool(ended),"api=",bool(d))
  if "one sports" not in channel.lower():continue
  if not is_live or ended:continue
  upper=title.upper()
  if "2026 ASIAN GAMES" in upper:
   league_key="asian_games"; sport="Asian Games"; league="2026 ASIAN GAMES"; prefix="ag26"
  elif re.search(r"\bPBA\b",upper):
   league_key="pba"; sport="Basketball"; league="PBA"; prefix="pba"
  elif "NBL PILIPINAS" in upper or "NBL-PILIPINAS" in upper:
   league_key="nbl"; sport="Basketball"; league="NBL Pilipinas"; prefix="nblph"
  else:
   continue
  watch="https://www.youtube.com/watch?v="+vid
  stream={"videoId":vid,"watchUrl":watch,"provider":"YouTube","channel":channel,"title":title}
  if embeddable:stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":prefix+"-youtube-"+vid,"sport":sport,"leagueKey":league_key,"league":league,"teams":[],"title":title,"stream":stream})
 return out

events=live_events(); streams=[]
for e in events:
 try:
  s=search(e)
  if s: streams.append({**e,"stream":s})
 except Exception as ex: print("youtube",e["title"],ex)
try:
 streams.extend(one_sports_live())
except Exception as ex:
 print("youtube One Sports",ex)
seen=set(); dedup=[]
for x in streams:
 vid=x.get("stream",{}).get("videoId")
 if vid and vid in seen: continue
 if vid: seen.add(vid)
 dedup.append(x)
streams=dedup
OUT.write_text(json.dumps({"updatedAt":datetime.now(timezone.utc).isoformat(),"streams":streams},indent=2)+"\n",encoding="utf-8")
print("live events",len(events),"matched streams",len(streams))
