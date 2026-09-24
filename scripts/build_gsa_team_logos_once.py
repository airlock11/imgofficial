import io,json,re,sys,urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageEnhance,ImageFilter
import cairosvg
ROOT=Path(__file__).resolve().parents[1]
key,url=sys.argv[1],sys.argv[2]
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 IMG-Sports-Assets/1.0","Accept-Language":"en-US,en;q=0.8"})
def norm(v):return re.sub(r"[^a-z0-9]+"," ",str(v or "").lower()).strip()
def slug(v):return re.sub(r"[^a-z0-9]+","-",str(v or "").lower()).strip("-")
r=S.get(url,timeout=30);r.raise_for_status();soup=BeautifulSoup(r.text,"html.parser")
found={}
for img in soup.find_all("img"):
    alt=re.sub(r"\s+"," ",img.get("alt","")).strip()
    m=re.match(r"logo\s+of\s+(.+)",alt,re.I)
    if not m:continue
    name=m.group(1).strip()
    if re.search(r"\b20\d\d(?:/20\d\d)?$",name):continue
    src=img.get("data-src") or img.get("data-lazy-src") or img.get("data-original") or img.get("src") or ""
    if src and not src.startswith("data:"):found.setdefault(norm(name),(name,urllib.parse.urljoin(url,src)))
folder=ROOT/"assets"/"football"/"teams"/key;folder.mkdir(parents=True,exist_ok=True)
out={};failed=[]
for _,(name,src) in found.items():
    try:
        rr=S.get(src,timeout=30);rr.raise_for_status();raw=rr.content
        if "svg" in rr.headers.get("content-type","").lower() or raw.lstrip().startswith(b"<svg"):
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
        out[name]="/"+path.relative_to(ROOT).as_posix()
    except Exception as e:failed.append(name)
print(json.dumps({"logos":out,"failed":failed},ensure_ascii=False))
