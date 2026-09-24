#!/usr/bin/env python3
import json,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from io import BytesIO
from pathlib import Path
from PIL import Image,ImageEnhance,ImageFilter
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
UA="IMG-Sports-TeamLogos/1.0"

def get(url,binary=False):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Language":"en-US,en;q=0.8"})
    with urllib.request.urlopen(req,timeout=30) as r:
        data=r.read()
    return data if binary else data.decode("utf-8","replace")

def norm(v):
    return re.sub(r"[^a-z0-9]+"," ",str(v or "").lower()).strip()

def slug(v):
    return re.sub(r"[^a-z0-9]+","-",str(v or "").lower()).strip("-")

def img_url(tag,base):
    if not tag:return ""
    src=tag.get("data-src") or tag.get("data-lazy-src") or tag.get("data-original") or tag.get("src") or ""
    return urllib.parse.urljoin(base,src) if src and not src.startswith("data:") else ""

def page_logos(url,team_names):
    html=get(url);soup=BeautifulSoup(html,"html.parser");out={}
    for name in team_names:
        n=norm(name);best=""
        for img in soup.find_all("img"):
            alt=norm(img.get("alt",""))
            if n and (n in alt or alt in n) and len(alt)>2:
                best=img_url(img,url)
                if best:break
        if not best:
            for row in soup.find_all(["tr","li","article","div"]):
                txt=norm(row.get_text(" ",strip=True))
                if n and n in txt:
                    best=img_url(row.find("img"),url)
                    if best:break
        out[name]=best
    return out

def espn_logos(league):
    data=json.loads(get("https://site.api.espn.com/apis/site/v2/sports/soccer/"+league+"/teams?limit=100"))
    rows=data.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[])
    out=[]
    for row in rows:
        t=row.get("team",row);logos=t.get("logos") or []
        logo=(logos[0].get("href") if logos else "") or t.get("logo") or ""
        name=t.get("displayName") or t.get("name") or ""
        if name and logo:
            aliases=[x for x in [t.get("shortDisplayName"),t.get("name"),t.get("abbreviation")] if x and x!=name]
            out.append({"name":name,"aliases":aliases,"sourceLogo":logo})
    return out

def save_png(url,path):
    raw=get(url,True);im=Image.open(BytesIO(raw)).convert("RGBA")
    box=im.getchannel("A").getbbox()
    if box:im=im.crop(box)
    size=444;scale=min(size/max(1,im.width),size/max(1,im.height))
    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
    rgb=Image.new("RGB",im.size,"white");rgb.paste(im.convert("RGB"),mask=im.getchannel("A"))
    rgb=ImageEnhance.Sharpness(rgb).enhance(1.08).filter(ImageFilter.UnsharpMask(radius=.7,percent=90,threshold=2))
    im=Image.merge("RGBA",(*rgb.split(),im.getchannel("A")))
    canvas=Image.new("RGBA",(512,512),(0,0,0,0))
    canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
    path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path,"PNG",optimize=True)

def run(cfg):
    key=cfg["leagueKey"];teams=[]
    if cfg.get("espn"):
        teams=espn_logos(cfg["espn"])
    else:
        requested=cfg["teams"];lookups=[x.get("lookup",x["name"]) for x in requested]
        found=page_logos(cfg["sourcePage"],lookups)
        for item,lookup in zip(requested,lookups):
            teams.append({"name":item["name"],"aliases":item.get("aliases",[]),"sourceLogo":found.get(lookup,"")})
    built=[];missing=[];folder=ROOT/"assets"/"football"/"teams"/key
    for team in teams:
        src=team.get("sourceLogo","");name=team["name"];target=folder/(slug(name)+".png")
        try:
            if not src:raise ValueError("no source logo")
            save_png(src,target)
            built.append({"name":name,"aliases":team.get("aliases",[]),"logo":"/"+target.relative_to(ROOT).as_posix(),"sourceLogo":src,"quality":"512x512 transparent contain"})
        except Exception as ex:
            print(key,name,ex);missing.append(name)
    payload={"version":1,"leagueKey":key,"league":cfg["league"],"season":"2026/27","updatedAt":datetime.now(timezone.utc).isoformat(),"count":len(built),"teams":built,"missing":missing,"source":cfg.get("sourcePage") or ("ESPN "+cfg.get("espn",""))}
    (ROOT/cfg["output"]).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(key,"built",len(built),"missing",missing)
