#!/usr/bin/env python3
import json,os,re,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
UA="IMG-Football-Highlights/1.0"; YT="https://www.googleapis.com/youtube/v3"
ROOT=Path(__file__).resolve().parents[1]
def now(): return datetime.now(timezone.utc)
def iso(): return now().replace(microsecond=0).isoformat().replace("+00:00","Z")
def text(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Language":"en-US,en;q=0.8"})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode("utf-8","replace")
def jget(url): return json.loads(text(url))
def yt(path,params):
 key=os.environ.get("YOUTUBE_API_KEY","").strip()
 if not key: raise RuntimeError("YOUTUBE_API_KEY missing")
 p=dict(params);p["key"]=key
 return jget(YT+"/"+path+"?"+urllib.parse.urlencode(p))
def channel(cfg):
 if cfg.get("channelId"):return cfg["channelId"]
 if cfg.get("handle"):
  x=yt("channels",{"part":"snippet,contentDetails","forHandle":str(cfg["handle"]).lstrip("@")}).get("items",[])
  if x:return x[0]["id"]
 if cfg.get("seedVideo"):
  x=yt("videos",{"part":"snippet","id":cfg["seedVideo"]}).get("items",[])
  if x:return x[0].get("snippet",{}).get("channelId","")
 if cfg.get("officialPage"):
  html=text(cfg["officialPage"])
  vids=re.findall(r"(?:youtube\.com/embed/|youtu\.be/)([A-Za-z0-9_-]{11})",html,re.I)
  for vid in vids[:5]:
   x=yt("videos",{"part":"snippet","id":vid}).get("items",[])
   if x:return x[0].get("snippet",{}).get("channelId","")
 return ""
def youtube(cfg):
 cid=channel(cfg)
 if not cid:return []
 c=yt("channels",{"part":"snippet,contentDetails","id":cid}).get("items",[])
 if not c:return []
 cname=c[0].get("snippet",{}).get("title","")
 upl=c[0].get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads","")
 if not upl:return []
 pis=yt("playlistItems",{"part":"contentDetails","playlistId":upl,"maxResults":50}).get("items",[])
 ids=[x.get("contentDetails",{}).get("videoId","") for x in pis]
 rows=yt("videos",{"part":"snippet,status","id":",".join([x for x in ids if x][:50])}).get("items",[])
 cutoff=now()-timedelta(days=int(cfg.get("maxAgeDays",180)));out=[]
 inc=[str(x).upper() for x in cfg.get("includeAny",[])]
 req=[str(x).upper() for x in cfg.get("requireAny",[])]
 exc=[str(x).upper() for x in cfg.get("excludeAny",[])]
 for v in rows:
  sn=v.get("snippet",{}); title=sn.get("title",""); up=title.upper()
  if sn.get("channelId")!=cid or any(x in up for x in exc):continue
  if inc and not any(x in up for x in inc):continue
  if req and not any(x in up for x in req):continue
  pub=sn.get("publishedAt","")
  try:
   if datetime.fromisoformat(pub.replace("Z","+00:00"))<cutoff:continue
  except:pass
  vid=v.get("id","");th=sn.get("thumbnails",{});thumb=(th.get("maxres") or th.get("standard") or th.get("high") or {}).get("url","")
  emb=bool(v.get("status",{}).get("embeddable"))
  out.append({"id":vid,"title":title,"url":"https://www.youtube.com/watch?v="+vid,"embedUrl":"https://www.youtube.com/embed/"+vid if emb else "","thumbnail":thumb,"publishedAt":pub,"provider":"YouTube","sourceName":cname,"verified":True,"verification":"exact-channel"})
 out.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
 return out[:int(cfg.get("limit",12))]
def urls(x):
 if isinstance(x,str):return [x] if x.startswith("http") else []
 if isinstance(x,list):
  z=[]
  for y in x:z+=urls(y)
  return z
 if isinstance(x,dict):
  z=[]
  for y in x.values():z+=urls(y)
  return z
 return []
def espn(cfg):
 start=(now()-timedelta(days=int(cfg.get("daysBack",12)))).strftime("%Y%m%d");end=now().strftime("%Y%m%d")
 ev=jget("https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg["espn"]+"/scoreboard?dates="+start+"-"+end).get("events",[])
 out=[]
 for e in [x for x in ev if x.get("status",{}).get("type",{}).get("state")=="post"][:12]:
  eid=str(e.get("id","")); 
  if not eid:continue
  try:s=jget("https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg["espn"]+"/summary?event="+eid)
  except:continue
  comp=(e.get("competitions") or [{}])[0];teams=[x.get("team",{}).get("displayName","") for x in comp.get("competitors",[])]
  for n,v in enumerate((s.get("videos") or [])+(s.get("highlights") or [])):
   title=v.get("headline") or v.get("title") or v.get("description") or " vs ".join(teams)
   us=urls(v.get("links",{}))+urls(v.get("source",{}))+urls(v.get("playback",{}))
   link=next((u for u in us if "espn" in u and not re.search(r"\.(m3u8|mp4)(\?|$)",u,re.I)), "") or next(iter(us),"")
   image=v.get("thumbnail") or v.get("image") or ""; image=image.get("url","") if isinstance(image,dict) else image
   if link:out.append({"id":eid+"-"+str(n),"title":title,"url":link,"embedUrl":"","thumbnail":image,"publishedAt":e.get("date",""),"provider":"ESPN","sourceName":"ESPN match video","verified":True,"verification":"match-summary-event-id","eventId":eid,"teams":teams})
 seen=set();clean=[]
 for x in out:
  if x["url"] in seen:continue
  seen.add(x["url"]);clean.append(x)
 clean.sort(key=lambda x:x.get("publishedAt",""),reverse=True)
 return clean[:int(cfg.get("limit",12))]
def clean(s):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s)).strip()
def uefa(cfg):
 html=text(cfg["uefaPage"]);out=[];seen=set()
 for m in re.finditer(r'href=["\\']([^"\\']*/video/highlights/[^"\\']+)["\\']',html,re.I):
  href=m.group(1);href="https://www.uefa.com"+href if href.startswith("/") else urllib.parse.urljoin(cfg["uefaPage"],href)
  if href in seen:continue
  seen.add(href);win=html[max(0,m.start()-500):min(len(html),m.end()+700)]
  tm=re.search(r'(?:aria-label|title)=["\\']([^"\\']+)["\\']',win,re.I);title=tm.group(1) if tm else clean(win)[:180]
  try:
   d=text(href);im=re.search(r'<meta[^>]+property=["\\']og:image["\\'][^>]+content=["\\']([^"\\']+)',d,re.I);thumb=im.group(1) if im else ""
  except:thumb=""
  out.append({"id":href.rstrip("/").split("/")[-1],"title":clean(title),"url":href,"embedUrl":"","thumbnail":thumb,"publishedAt":"","provider":"UEFA.com","sourceName":cfg["sourceName"],"verified":True,"verification":"official-competition-highlight-page"})
  if len(out)>=int(cfg.get("limit",12)):break
 return out
def run(cfg):
 p=ROOT/cfg["output"]
 try:previous=json.loads(p.read_text("utf-8"))
 except:previous={}
 items=[];err=""
 try:
  if cfg["mode"]=="youtube":items=youtube(cfg)
  elif cfg["mode"]=="espn":items=espn(cfg)
  elif cfg["mode"]=="uefa":items=uefa(cfg)
  elif cfg["mode"]=="la_primera_reserve":
   c=dict(cfg);c["officialPage"]="https://laprimera.com.sv/home/";c["includeAny"]=["RESERVA","RESERVAS"];c["requireAny"]=["HIGHLIGHT","HIGHLIGHTS","RESUMEN","GOLES","GOLAZOS"];items=youtube(c)
 except Exception as ex:err=str(ex)
 if not items and err:items=[x for x in previous.get("highlights",[]) if x.get("verified") is True]
 payload={"version":1,"leagueKey":cfg["leagueKey"],"league":cfg["league"],"updatedAt":iso(),"source":{"mode":cfg["mode"],"name":cfg.get("sourceName",""),"url":cfg.get("sourceUrl","")},"highlights":items,"count":len(items),"error":err}
 p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
 print(cfg["league"],len(items),err or "ok")
