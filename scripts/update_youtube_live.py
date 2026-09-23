#!/usr/bin/env python3
import json, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import html as html_lib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from asian_live_expiry import expire_entries

KEY=os.environ["YOUTUBE_API_KEY"]
OUT=Path(__file__).resolve().parents[1]/"youtube-live.json"
REGIONAL=Path(__file__).resolve().parents[1]/"regional-web.json"
SOURCE_REGISTRY=Path(__file__).resolve().parents[1]/"live-stream-sources.json"
UA="IMG-Sports-Live/1.0"
ONE_SPORTS_CHANNEL_ID="UCXDG9ue-emCN8Ad3h7lERqQ"
NBL_PILIPINAS_CHANNEL_ID="UCJDBLldRGVJPEvyjJdSHefw"
WTA_YOUTUBE_USERNAME="WTA"
MPBL_YOUTUBE_HANDLE="mpblofficial"
PINNED_ASIAN_GAMES_VIDEO_IDS=["5mZlZtTk83E"]
SCOREBOARDS={
 "Basketball":"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
 "Football":"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard",
 "Baseball":"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
 "Hockey":"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
 "American Football":"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
}
def get_json(url, attempts=3):
 last=None
 for attempt in range(attempts):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":UA})
   with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
  except Exception as ex:
   last=ex
   if attempt+1<attempts: time.sleep(1.5*(attempt+1))
 raise last
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
def youtube_search(q="", max_results=25, channel_id=None, event_type="live"):
 params={"part":"snippet","type":"video","eventType":event_type,"maxResults":max_results,"key":KEY}
 if q: params["q"]=q
 if channel_id: params["channelId"]=channel_id
 return get_json("https://www.googleapis.com/youtube/v3/search?"+urllib.parse.urlencode(params)).get("items",[])

def resolve_legacy_channel_id(username):
 params={"part":"snippet","forUsername":username,"key":KEY}
 items=get_json("https://www.googleapis.com/youtube/v3/channels?"+urllib.parse.urlencode(params)).get("items",[])
 return str(items[0].get("id","")) if items else ""

def resolve_handle_channel_id(handle):
 value=str(handle or "").strip().lstrip("@")
 if not value:return ""
 params={"part":"snippet","forHandle":value,"key":KEY}
 items=get_json("https://www.googleapis.com/youtube/v3/channels?"+urllib.parse.urlencode(params)).get("items",[])
 return str(items[0].get("id","")) if items else ""


def load_source_registry():
 try:
  data=json.loads(SOURCE_REGISTRY.read_text("utf-8"))
  sources=data.get("sources",[])
  return [x for x in sources if isinstance(x,dict) and x.get("id") and x.get("leagueKey")]
 except Exception as ex:
  print("livestream source registry",ex)
  return []

def source_title_allowed(source,title):
 upper=str(title or "").upper()
 excludes=[str(x).upper() for x in source.get("excludeAny",[]) if str(x).strip()]
 if any(token in upper for token in excludes):return False
 includes=[str(x).upper() for x in source.get("includeAny",[]) if str(x).strip()]
 return not includes or any(token in upper for token in includes)

def resolve_source_channel(source,previous):
 source_id=str(source.get("id") or "")
 cached=str(previous.get("scanner",{}).get("resolvedChannels",{}).get(source_id) or "")
 if cached:return cached
 direct=str(source.get("channelId") or "")
 if direct:return direct
 handle=str(source.get("handle") or "")
 if handle:return resolve_handle_channel_id(handle)
 username=str(source.get("username") or "")
 if username:return resolve_legacy_channel_id(username)
 return ""

def scan_official_source(source,previous):
 source_id=str(source.get("id") or "official")
 try:
  channel_id=resolve_source_channel(source,previous)
 except Exception as ex:
  print("official source resolve",source_id,ex)
  return [],""
 if not channel_id:
  print("official source unresolved",source_id)
  return [],""

 ids=[]
 try:
  ids += channel_feed_ids(channel_id)
 except Exception as ex:
  print("official source feed",source_id,ex)
 try:
  ids += channel_stream_page_ids(channel_id)
 except Exception as ex:
  print("official source streams",source_id,ex)
 try:
  ids += channel_recent_video_ids(channel_id,25)
 except Exception as ex:
  print("official source uploads",source_id,ex)
 ids=list(dict.fromkeys(x for x in ids if x))[:50]
 if not ids:return [],channel_id

 try:
  details=video_details(ids)
 except Exception as ex:
  print("official source details",source_id,ex)
  details={}

 out=[]
 for vid in ids:
  d=details.get(vid)
  if d:
   sn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
   if sn.get("channelId")!=channel_id:continue
   title=sn.get("title",""); channel=(sn.get("channelTitle") or source.get("league") or source_id).strip()
   is_live=sn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
   ended=bool(live.get("actualEndTime"))
   embeddable=status.get("embeddable",True)
  else:
   # Accuracy-first: do not publish a stream that the exact-video API did not return.
   # Public watch-page markup is useful for diagnostics, but not strong enough to
   # prove the source channel identity for a LIVE badge.
   continue

  if not is_live or ended or not source_title_allowed(source,title):continue
  watch="https://www.youtube.com/watch?v="+vid
  verified_at=datetime.now(timezone.utc).isoformat()
  stream={
   "videoId":vid,
   "watchUrl":watch,
   "provider":"YouTube",
   "channel":channel,
   "title":title,
   "officialSourceId":source_id,
   "sourceChannelId":channel_id,
   "verificationStatus":"verified",
   "lastVerifiedLiveAt":verified_at
  }
  if embeddable:stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  prefix=str(source.get("prefix") or source.get("leagueKey") or "live")
  out.append({
   "eventId":prefix+"-youtube-"+vid,
   "sport":source.get("sport") or "Sport",
   "leagueKey":source.get("leagueKey"),
   "league":source.get("league") or source.get("leagueKey"),
   "teams":[],
   "title":title,
   "officialSourceId":source_id,
   "verificationStatus":"verified",
   "lastVerifiedLiveAt":verified_at,
   "stream":stream
  })
 return out,channel_id

def scan_official_registry(previous):
 streams=[]
 resolved={}
 checked=[]
 for source in load_source_registry():
  source_id=str(source.get("id") or "")
  checked.append(source_id)
  try:
   found,channel_id=scan_official_source(source,previous)
   if channel_id:resolved[source_id]=channel_id
   streams.extend(found)
  except Exception as ex:
   print("official source scan",source_id,ex)
 return streams,{
  "version":3,
  "mode":"official-auto-discovery",
  "checkedAt":datetime.now(timezone.utc).isoformat(),
  "sourcesChecked":checked,
  "resolvedChannels":resolved
 }

def video_details(ids):
 if not ids:return {}
 params=urllib.parse.urlencode({"part":"snippet,status,liveStreamingDetails","id":",".join(ids),"key":KEY})
 data=get_json("https://www.googleapis.com/youtube/v3/videos?"+params)
 return {x["id"]:x for x in data.get("items",[])}

def channel_recent_video_ids(channel_id,max_results=25):
 # Cheap YouTube API fallback: inspect the channel's uploads playlist instead of
 # running expensive global Search API queries. New livestreams appear here even
 # when RSS or the public /streams page temporarily misses them.
 params=urllib.parse.urlencode({"part":"contentDetails","id":channel_id,"key":KEY})
 items=get_json("https://www.googleapis.com/youtube/v3/channels?"+params).get("items",[])
 if not items:return []
 uploads=items[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads")
 if not uploads:return []
 q=urllib.parse.urlencode({"part":"contentDetails","playlistId":uploads,"maxResults":max_results,"key":KEY})
 rows=get_json("https://www.googleapis.com/youtube/v3/playlistItems?"+q).get("items",[])
 return [x.get("contentDetails",{}).get("videoId") for x in rows if x.get("contentDetails",{}).get("videoId")]

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
 try:
  ids += channel_recent_video_ids(ONE_SPORTS_CHANNEL_ID,25)
 except Exception as ex:
  print("One Sports uploads",ex)
 ids=PINNED_ASIAN_GAMES_VIDEO_IDS + ids
 ids=list(dict.fromkeys(x for x in ids if x))
 details=video_details(ids[:50])
 out=[]
 for vid in ids[:50]:
  d=details.get(vid)
  if not d:
   # Fail closed: a public page alone cannot prove exact official-channel ownership.
   continue
  dsn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
  if dsn.get("channelId")!=ONE_SPORTS_CHANNEL_ID:
   continue
  title=dsn.get("title",""); channel=(dsn.get("channelTitle") or "One Sports").strip()
  is_live=dsn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
  ended=bool(live.get("actualEndTime"))
  embeddable=status.get("embeddable",True)
  if vid in PINNED_ASIAN_GAMES_VIDEO_IDS:
   print("Pinned stream diagnostic",vid,repr(title),repr(channel),"live=",bool(is_live),"ended=",bool(ended),"api=",True)
  if not is_live or ended:continue
  upper=title.upper()
  if "2026 ASIAN GAMES" in upper:
   league_key="asian_games"; sport="Asian Games"; league="2026 ASIAN GAMES"; prefix="ag26"
  elif re.search(r"\bPBA\b",upper):
   league_key="pba"; sport="Basketball"; league="PBA"; prefix="pba"
  elif re.search(r"\bNCAA\b",upper):
   league_key="ncaa_ph"; sport="Basketball"; league="NCAA Philippines"; prefix="ncaaph"
  elif re.search(r"\bUAAP\b",upper):
   league_key="uaap"; sport="Basketball"; league="UAAP"; prefix="uaap"
  else:
   continue
  watch="https://www.youtube.com/watch?v="+vid
  verified_at=datetime.now(timezone.utc).isoformat()
  stream={"videoId":vid,"watchUrl":watch,"provider":"YouTube","channel":channel,"title":title,"sourceChannelId":ONE_SPORTS_CHANNEL_ID,"verificationStatus":"verified","lastVerifiedLiveAt":verified_at}
  if embeddable:stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":prefix+"-youtube-"+vid,"sport":sport,"leagueKey":league_key,"league":league,"teams":[],"title":title,"verificationStatus":"verified","lastVerifiedLiveAt":verified_at,"stream":stream})
 return out

def wta_official_live():
 # WTA's own site identifies youtube.com/WTA as an official social channel.
 # Accept only videos from that exact resolved channel and only while YouTube
 # reports the broadcast as currently live and not ended.
 try:
  channel_id=resolve_legacy_channel_id(WTA_YOUTUBE_USERNAME)
 except Exception as ex:
  print("WTA channel resolve",ex)
  return []
 if not channel_id:
  print("WTA official YouTube channel could not be resolved")
  return []

 ids=[]
 try:
  ids += channel_feed_ids(channel_id)
 except Exception as ex:
  print("WTA feed",ex)
 try:
  ids += channel_stream_page_ids(channel_id)
 except Exception as ex:
  print("WTA streams page",ex)
 try:
  ids += [x.get("id",{}).get("videoId") for x in youtube_search(max_results=25,channel_id=channel_id,event_type="live")]
 except Exception as ex:
  print("WTA live search",ex)

 ids=list(dict.fromkeys(x for x in ids if x))
 details=video_details(ids[:50])
 out=[]
 for vid in ids[:50]:
  d=details.get(vid)
  if not d:continue
  sn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
  if sn.get("channelId")!=channel_id:continue
  title=sn.get("title",""); channel=(sn.get("channelTitle") or "WTA").strip()
  is_live=sn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
  ended=bool(live.get("actualEndTime"))
  if not is_live or ended:continue
  # Keep this scoped to actual WTA tennis content, not unrelated channel activity.
  upper=title.upper()
  if not any(token in upper for token in ["WTA","TENNIS","OPEN","FINAL","SEMIFINAL","QUARTERFINAL","ROUND"]):continue
  watch="https://www.youtube.com/watch?v="+vid
  stream={"videoId":vid,"watchUrl":watch,"provider":"YouTube","channel":channel,"title":title}
  if status.get("embeddable",True):stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":"wta-youtube-"+vid,"sport":"Tennis","leagueKey":"wta","league":"WTA Tour","teams":[],"title":title,"stream":stream})
 return out

def mpbl_official_live():
 # Official MPBL channel supplied by IMG: https://youtube.com/@mpblofficial
 # Only publish a stream while YouTube confirms that exact channel is live.
 try:
  channel_id=resolve_handle_channel_id(MPBL_YOUTUBE_HANDLE)
 except Exception as ex:
  print("MPBL channel resolve",ex)
  return []
 if not channel_id:
  print("MPBL official YouTube handle could not be resolved")
  return []

 ids=[]
 try:
  ids += channel_feed_ids(channel_id)
 except Exception as ex:
  print("MPBL feed",ex)
 try:
  ids += channel_stream_page_ids(channel_id)
 except Exception as ex:
  print("MPBL streams page",ex)
 try:
  ids += [x.get("id",{}).get("videoId") for x in youtube_search(max_results=25,channel_id=channel_id,event_type="live")]
 except Exception as ex:
  print("MPBL live search",ex)

 ids=list(dict.fromkeys(x for x in ids if x))
 details=video_details(ids[:50])
 out=[]
 for vid in ids[:50]:
  d=details.get(vid)
  if not d:continue
  sn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
  if sn.get("channelId")!=channel_id:continue
  title=sn.get("title",""); channel=(sn.get("channelTitle") or "MPBL Official").strip()
  is_live=sn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
  ended=bool(live.get("actualEndTime"))
  if not is_live or ended:continue
  upper=title.upper()
  if not any(token in upper for token in ["MPBL","MAHARLIKA","BASKETBALL","LIVE"]):continue
  watch="https://www.youtube.com/watch?v="+vid
  stream={"videoId":vid,"watchUrl":watch,"provider":"YouTube","channel":channel,"title":title}
  if status.get("embeddable",True):stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":"mpbl-youtube-"+vid,"sport":"Basketball","leagueKey":"mpbl","league":"MPBL","teams":[],"title":title,"stream":stream})
 return out

def load_previous():
 try:
  return json.loads(OUT.read_text("utf-8"))
 except Exception:
  return {}

def verified_age_seconds(item, now=None):
 now=now or datetime.now(timezone.utc)
 value=item.get("lastVerifiedLiveAt") or (item.get("stream") or {}).get("lastVerifiedLiveAt")
 try:
  dt=datetime.fromisoformat(str(value or "").replace("Z","+00:00")).astimezone(timezone.utc)
  return max(0,(now-dt).total_seconds())
 except Exception:
  return 999999

def previous_still_live(previous):
 # Recheck every published exact video ID before removing it. Channel discovery
 # surfaces can omit simultaneous broadcasts even while their players are live.
 # Streams are retained only while YouTube or the public watch page confirms they are live.
 candidates=[x for x in previous.get("streams",[]) if x.get("stream",{}).get("videoId")]
 ids=list(dict.fromkeys(x.get("stream",{}).get("videoId") for x in candidates))
 if not ids:return []
 api_failed=False
 try:
  details=video_details(ids[:50])
 except Exception as ex:
  print("previous live details",ex)
  details={}
  api_failed=True
 out=[]
 now=datetime.now(timezone.utc)
 for item in candidates:
  stream=item.get("stream",{})
  vid=stream.get("videoId")
  d=details.get(vid)
  if d:
   sn=d.get("snippet",{}); live=d.get("liveStreamingDetails",{}); status=d.get("status",{})
   expected_channel=str(stream.get("sourceChannelId") or "")
   if item.get("leagueKey")=="asian_games":
    expected_channel=ONE_SPORTS_CHANNEL_ID
   if expected_channel and sn.get("channelId")!=expected_channel:
    continue
   is_live=sn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
   ended=bool(live.get("actualEndTime"))
   if not is_live or ended:
    continue
   if sn.get("channelTitle"):stream["channel"]=sn.get("channelTitle")
   if sn.get("channelId"):stream["sourceChannelId"]=sn.get("channelId")
   if sn.get("title"):stream["title"]=sn.get("title"); item["title"]=sn.get("title")
   if status.get("embeddable",True):stream["embedUrl"]="https://www.youtube.com/embed/"+vid
   else:stream.pop("embedUrl",None)
   verified_at=now.isoformat()
   item["verificationStatus"]="verified"
   item["lastVerifiedLiveAt"]=verified_at
   stream["verificationStatus"]="verified"
   stream["lastVerifiedLiveAt"]=verified_at
   item["stream"]=stream
   out.append(item)
   continue

  # Grace is allowed only when the whole exact-video API request failed.
  # If the API request succeeded but omitted this ID, fail closed and remove it.
  if api_failed and verified_age_seconds(item,now)<=300:
   item["verificationStatus"]="grace"
   stream["verificationStatus"]="grace"
   item["stream"]=stream
   out.append(item)
 return out

def nbl_regional_schedule():
 try:
  data=json.loads(REGIONAL.read_text("utf-8"))
 except Exception:
  return []
 now=datetime.now(timezone.utc)
 out=[]
 for g in data.get("leagues",{}).get("nbl",{}).get("games",[]):
  if g.get("state")!="scheduled":continue
  try:
   dt=datetime.fromisoformat(str(g.get("date","")).replace("Z","+00:00")).astimezone(timezone.utc)
  except Exception:
   continue
  if now-timedelta(hours=6) <= dt <= now+timedelta(days=14):
   out.append(g)
 return sorted(out,key=lambda x:x.get("date",""))

def matchup_from_title(title):
 text=str(title or "")
 part=text.split("|")[-1].strip()
 m=re.search(r"(.+?)\s+vs\.?\s+(.+)$",part,re.I)
 if not m:return ("NBL Pilipinas",text or "Scheduled game")
 return (m.group(1).strip(),m.group(2).strip())

def nbl_pilipinas_upcoming(previous):
 now=datetime.now(timezone.utc)
 prev_checked=previous.get("upcomingCheckedAt")
 should_check=True
 if prev_checked:
  try:
   checked=datetime.fromisoformat(str(prev_checked).replace("Z","+00:00")).astimezone(timezone.utc)
   should_check=(now-checked)>=timedelta(hours=4)
  except Exception:
   pass
 if not should_check:
  kept=[]
  for x in previous.get("upcoming",[]):
   try:
    start=datetime.fromisoformat(str(x.get("scheduledStartTime","")).replace("Z","+00:00")).astimezone(timezone.utc)
    if start>=now-timedelta(hours=3):kept.append(x)
   except Exception:
    pass
  return kept,prev_checked
 items=youtube_search(max_results=25,channel_id=NBL_PILIPINAS_CHANNEL_ID,event_type="upcoming")
 ids=[x.get("id",{}).get("videoId") for x in items if x.get("id",{}).get("videoId")]
 details=video_details(ids)
 out=[]
 for vid,d in details.items():
  sn=d.get("snippet",{}); live=d.get("liveStreamingDetails",{}); status=d.get("status",{})
  if sn.get("channelId")!=NBL_PILIPINAS_CHANNEL_ID:continue
  start=live.get("scheduledStartTime")
  if not start:continue
  title=sn.get("title",""); a,b=matchup_from_title(title)
  stream={"videoId":vid,"watchUrl":"https://www.youtube.com/watch?v="+vid,"provider":"YouTube","channel":sn.get("channelTitle") or "NBL Pilipinas","title":title,"status":"upcoming","scheduledStartTime":start}
  if status.get("embeddable",True):stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":"nblph-upcoming-"+vid,"sport":"Basketball","leagueKey":"nbl","league":"NBL Pilipinas","away":a,"home":b,"title":title,"scheduledStartTime":start,"stream":stream})
 return out,now.isoformat()

def nbl_pilipinas_live():
 # NBL Pilipinas uses its own official YouTube page, not the One Sports rule.
 ids=[]
 try:
  ids += channel_feed_ids(NBL_PILIPINAS_CHANNEL_ID)
 except Exception as ex:
  print("NBL Pilipinas feed",ex)
 try:
  ids += channel_stream_page_ids(NBL_PILIPINAS_CHANNEL_ID)
 except Exception as ex:
  print("NBL Pilipinas streams page",ex)
 ids=list(dict.fromkeys(x for x in ids if x))
 details=video_details(ids[:50])
 out=[]
 for vid in ids[:50]:
  d=details.get(vid)
  if d:
   dsn=d.get("snippet",{}); status=d.get("status",{}); live=d.get("liveStreamingDetails",{})
   if dsn.get("channelId")!=NBL_PILIPINAS_CHANNEL_ID:continue
   title=dsn.get("title",""); channel=(dsn.get("channelTitle") or "NBL Pilipinas").strip()
   is_live=dsn.get("liveBroadcastContent")=="live" or (live.get("actualStartTime") and not live.get("actualEndTime"))
   ended=bool(live.get("actualEndTime")); embeddable=status.get("embeddable",True)
  else:
   try:
    info=public_watch_info(vid)
   except Exception:
    continue
   title=info["title"]; channel=info["channel"] or "NBL Pilipinas"
   is_live=info["live"]; ended=False; embeddable=True
  if not is_live or ended:continue
  watch="https://www.youtube.com/watch?v="+vid
  stream={"videoId":vid,"watchUrl":watch,"provider":"YouTube","channel":channel,"title":title}
  if embeddable:stream["embedUrl"]="https://www.youtube.com/embed/"+vid
  out.append({"eventId":"nblph-youtube-"+vid,"sport":"Basketball","leagueKey":"nbl","league":"NBL Pilipinas","teams":[],"title":title,"stream":stream})
 return out

previous=load_previous()
now=datetime.now(timezone.utc)
streams=[]
scanner_state={
 "version":3,
 "mode":"official-auto-discovery",
 "checkedAt":now.isoformat(),
 "sourcesChecked":[],
 "resolvedChannels":previous.get("scanner",{}).get("resolvedChannels",{})
}

# One Sports is a verified multi-league channel and needs title-based league classification.
try:
 streams.extend(one_sports_live())
except Exception as ex:
 print("youtube One Sports",ex)

# All single-league official channels are scanned through the IMG source registry.
try:
 official_streams,scanner_state=scan_official_registry(previous)
 streams.extend(official_streams)
except Exception as ex:
 print("youtube official registry",ex)

# Exact previously-published video IDs are rechecked so simultaneous live broadcasts
# are not lost if a channel's feed/Streams surface temporarily omits one.
try:
 streams.extend(previous_still_live(previous))
except Exception as ex:
 print("youtube previous streams",ex)

seen=set(); dedup=[]
for x in streams:
 vid=x.get("stream",{}).get("videoId")
 if vid and vid in seen:continue
 if vid:seen.add(vid)
 stream=x.get("stream",{})
 if x.get("leagueKey")=="asian_games":
  # Preserve the verifier's state exactly. Never upgrade grace/fallback to verified.
  x.pop("expiresAt",None); x.pop("fallbackExpiresAt",None)
  stream.pop("expiresAt",None); stream.pop("fallbackExpiresAt",None)
 league_key=str(x.get("leagueKey") or "").strip()
 if league_key:
  x["delivery"]={
   "leagueKey":league_key,
   "url":"/scores/?league="+urllib.parse.quote(league_key),
   "placement":"above_statistics"
  }
  if isinstance(x.get("stream"),dict):
   x["stream"]["deliveryLeagueKey"]=league_key
   x["stream"]["deliveryPlacement"]="above_statistics"
 dedup.append(x)

streams,expiry_ledger=expire_entries(dedup,previous,now,streams=True)
try:
 upcoming,upcoming_checked=nbl_pilipinas_upcoming(previous)
except Exception as ex:
 print("youtube NBL Pilipinas upcoming",ex)
 upcoming=previous.get("upcoming",[])
 upcoming_checked=previous.get("upcomingCheckedAt")

payload={
 "updatedAt":datetime.now(timezone.utc).isoformat(),
 "freshForMinutes":20,
 "streams":streams,
 "liveExpiryLedger":expiry_ledger,
 "upcoming":upcoming,
 "upcomingCheckedAt":upcoming_checked,
 "nblSchedule":nbl_regional_schedule(),
 "scanner":scanner_state
}
def semantic_payload(value):
 data=json.loads(json.dumps(value))
 data.pop("updatedAt",None)
 scanner=data.get("scanner")
 if isinstance(scanner,dict):scanner.pop("checkedAt",None)
 # Positive verification timestamps change every scan but do not represent a
 # meaningful stream-state change. Fallback/verified status and deadlines remain.
 for item in data.get("streams",[]):
  if item.get("leagueKey")!="asian_games":
   item.pop("lastVerifiedLiveAt",None)
   stream=item.get("stream")
   if isinstance(stream,dict):stream.pop("lastVerifiedLiveAt",None)
 for item in data.get("liveExpiryLedger",{}).values():
  if isinstance(item,dict):item.pop("lastVerifiedLiveAt",None)
 return data

# Avoid a GitHub Pages deployment every five minutes when nothing meaningful
# changed. Ended/new streams still change the semantic payload and publish immediately.
if semantic_payload(payload)==semantic_payload(previous):
 print(
  "IMG livestream scanner",
  "official sources",len(scanner_state.get("sourcesChecked",[])),
  "verified live streams",len(streams),
  "no semantic stream changes"
 )
else:
 OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
 print(
  "IMG livestream scanner",
  "official sources",len(scanner_state.get("sourcesChecked",[])),
  "verified live streams",len(streams),
  "NBL upcoming",len(upcoming),
  "NBL scheduled",len(payload["nblSchedule"])
 )
