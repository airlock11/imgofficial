#!/usr/bin/env python3
import json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

KEY=os.environ["YOUTUBE_API_KEY"]
OUT=Path(__file__).resolve().parents[1]/"boxing-highlights.json"
UA="IMG-Boxing-Highlights/1.0"

SOURCES={
 "wbc":{
  "name":"World Boxing Council",
  "channel":"World Boxing Council",
  "channelId":"UCOogiDvTQ8G7Zb5AOim9Olw",
  "url":"https://www.youtube.com/@WBCBoxingvid",
 },
 "wba":{
  "name":"World Boxing Association",
  "channel":"World Boxing Association",
  "channelId":"UCFLh18_umMvBkz9YCLo4vkA",
  "url":"https://www.youtube.com/@WorldBoxingAssociationOfficial",
 },
 "wbo":{
  "name":"World Boxing Organization",
  "channel":"World Boxing Organization",
  "channelId":"UCj9SVchp1P7nXAOcaWGMCiA",
  "url":"https://www.youtube.com/@WorldBoxingOrg",
 },
}

INCLUDE=(
 "highlight","highlights","knockout"," ko ","ko!","tko","best moments",
 "top moments","fight recap","recap","best of","fight highlights"
)
EXCLUDE=(
 "live:"," live ","full fight","full event","press conference","weigh-in","weigh in",
 "interview","podcast","convention","ceremony","promo","trailer","face off","face-off",
 "conference","meeting","documentary","seminar","presentation","donation","donations"
)

def get_json(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=20) as r:
  return json.load(r)

def api(endpoint,params):
 q=urllib.parse.urlencode({**params,"key":KEY})
 return get_json("https://www.googleapis.com/youtube/v3/"+endpoint+"?"+q)

def chunks(items,size=50):
 for i in range(0,len(items),size):
  yield items[i:i+size]

def recent_video_ids(channel_id,max_results=50):
 channels=api("channels",{"part":"contentDetails","id":channel_id})
 items=channels.get("items",[])
 if not items:return []
 uploads=items[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads")
 if not uploads:return []
 rows=api("playlistItems",{
  "part":"contentDetails","playlistId":uploads,"maxResults":max_results
 }).get("items",[])
 return [x.get("contentDetails",{}).get("videoId") for x in rows if x.get("contentDetails",{}).get("videoId")]

def video_details(ids):
 out={}
 for batch in chunks(ids):
  if not batch:continue
  rows=api("videos",{
   "part":"snippet,status,contentDetails",
   "id":",".join(batch),
   "maxResults":50
  }).get("items",[])
  for row in rows:
   if row.get("id"):out[row["id"]]=row
 return out

def looks_like_highlight(title):
 text=" "+re.sub(r"\s+"," ",str(title or "").lower()).strip()+" "
 if any(token in text for token in EXCLUDE):return False
 return any(token in text for token in INCLUDE)

def best_thumb(snippet):
 thumbs=snippet.get("thumbnails",{}) or {}
 for key in ("maxres","standard","high","medium","default"):
  url=(thumbs.get(key) or {}).get("url")
  if url:return url
 return ""

def load_previous():
 try:return json.loads(OUT.read_text("utf-8"))
 except Exception:return {}

def scan_source(key,source):
 ids=recent_video_ids(source["channelId"],50)
 details=video_details(ids)
 rows=[]
 for vid in ids:
  d=details.get(vid)
  if not d:continue
  sn=d.get("snippet",{}); status=d.get("status",{})
  if sn.get("channelId")!=source["channelId"]:continue
  if status.get("privacyStatus")!="public":continue
  if status.get("embeddable",True) is False:continue
  if sn.get("liveBroadcastContent")=="live":continue
  title=sn.get("title","").strip()
  if not looks_like_highlight(title):continue
  rows.append({
   "videoId":vid,
   "title":title,
   "channel":sn.get("channelTitle") or source["channel"],
   "publishedAt":sn.get("publishedAt",""),
   "watchUrl":"https://www.youtube.com/watch?v="+vid,
   "embedUrl":"https://www.youtube-nocookie.com/embed/"+vid+"?playsinline=1&rel=0",
   "thumb":best_thumb(sn),
   "officialSource":source["name"],
   "officialSourceUrl":source["url"],
   "leagueKey":key,
  })
  if len(rows)>=8:break
 return rows

def semantic(value):
 data=json.loads(json.dumps(value))
 data.pop("updatedAt",None)
 return data

previous=load_previous()
highlights={}
for key,source in SOURCES.items():
 try:
  highlights[key]=scan_source(key,source)
 except Exception as ex:
  print("boxing highlights",key,ex)
  highlights[key]=(previous.get("highlights",{}) or {}).get(key,[])

payload={
 "updatedAt":datetime.now(timezone.utc).isoformat(),
 "sources":SOURCES,
 "highlights":highlights,
}

if semantic(payload)==semantic(previous):
 print("IMG boxing highlights: no semantic changes")
else:
 OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
 print("IMG boxing highlights updated",sum(len(v) for v in highlights.values()))
