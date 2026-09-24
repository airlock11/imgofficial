import io,json,re,sys
from pathlib import Path
import requests
from PIL import Image,ImageEnhance,ImageFilter
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
key,code=sys.argv[1],sys.argv[2]
host="site.api."+"espn.com"
url=f"https://{host}/apis/site/v2/sports/soccer/{code}/teams?limit=100"
r0=requests.get(url,timeout=30,headers={"User-Agent":"IMG-Sports-Assets/1.0"})
print("FETCH",r0.status_code,r0.headers.get("content-type"),file=sys.stderr)
r0.raise_for_status()
j=r0.json()
rows=j.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[])
out={};folder=ROOT/"assets"/"football"/"teams"/key
folder.mkdir(parents=True,exist_ok=True)
def slug(v):return re.sub(r"[^a-z0-9]+","-",v.lower()).strip("-")
def norm(v):return re.sub(r"[^a-z0-9]+"," ",v.lower()).strip()
for row in rows:
    t=row.get("team",row);name=t.get("displayName") or t.get("name") or ""
    logos=t.get("logos") or [];src=(logos[0].get("href") if logos else "") or t.get("logo") or ""
    if not name or not src:continue
    r=requests.get(src,timeout=30,headers={"User-Agent":"IMG-Sports-Assets/1.0"});r.raise_for_status();raw=r.content
    if "svg" in r.headers.get("content-type","").lower() or raw.lstrip().startswith(b"<svg"):
        raw=cairosvg.svg2png(bytestring=raw,output_width=1200,output_height=1200)
    im=Image.open(io.BytesIO(raw)).convert("RGBA")
    box=im.getchannel("A").getbbox()
    if box:im=im.crop(box)
    scale=min(448/max(1,im.width),448/max(1,im.height))
    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
    rgb=Image.new("RGB",im.size,"white");rgb.paste(im.convert("RGB"),mask=im.getchannel("A"))
    rgb=ImageEnhance.Sharpness(rgb).enhance(1.08).filter(ImageFilter.UnsharpMask(radius=.75,percent=95,threshold=2))
    im=Image.merge("RGBA",(*rgb.split(),im.getchannel("A")))
    canvas=Image.new("RGBA",(512,512),(0,0,0,0));canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
    path=folder/(slug(name)+".png");canvas.save(path,"PNG",optimize=True)
    local="/"+path.relative_to(ROOT).as_posix()
    for alias in [name,t.get("name"),t.get("shortDisplayName"),t.get("abbreviation")]:
        if alias:out[norm(alias)]=local
print(json.dumps(out,ensure_ascii=False))
