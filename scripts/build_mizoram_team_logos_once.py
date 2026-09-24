import io,json,re\n# One-time asset build; remove after crest integration.
from pathlib import Path
import requests
from PIL import Image,ImageEnhance,ImageFilter
ROOT=Path(__file__).resolve().parents[1]
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 IMG-Sports-Assets/1.0"})
SOURCES={
"Aizawl FC":"https://assets.offsidescores.com/teams/pics/c9596297-1382-4b84-a052-37a6b82a77fa638623424669504982.png",
"Mizoram Police FC":"https://img.sofascore.com/api/v1/team/830187/image",
"Chanmari FC":"https://img.thesports.com/football/team/205111004b08c5b99ee531ade038964e.png",
"MLS FC":"https://assets.offsidescores.com/team/pics/60bb8cae-2245-4186-9712-69fe957dfbc8639238613771796158.webp",
"Saikhamakawn FC":"https://assets.offsidescores.com/team/pics/8ef13223-ed94-4372-a6d0-2181436a1c04639238612986771799.webp",
"Ramthar Veng FC":"https://assets.offsidescores.com/team/pics/50960c64-aa1b-4d34-ba7a-3c2859b34e61639232661222927255.webp",
"Dinthar FC":"https://assets.offsidescores.com/team/pics/e625e7d7-eade-4f6a-acf7-a3d9602a36b8639238613167011847.webp",
"Kanan FC":"https://assets.offsidescores.com/team/pics/b532c001-b543-450e-82f7-7c1df35191a0639241202221647606.webp"}
def slug(v): return re.sub(r"[^a-z0-9]+","-",v.lower()).strip("-")
folder=ROOT/"assets"/"football"/"teams"/"mizoram_pl";folder.mkdir(parents=True,exist_ok=True)
out={};missing=[]
for name,src in SOURCES.items():
    try:
        r=S.get(src,timeout=30);r.raise_for_status()
        im=Image.open(io.BytesIO(r.content)).convert("RGBA")
        box=im.getchannel("A").getbbox()
        if box: im=im.crop(box)
        scale=min(448/max(1,im.width),448/max(1,im.height))
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
        rgb=Image.new("RGB",im.size,"white");rgb.paste(im.convert("RGB"),mask=im.getchannel("A"))
        rgb=ImageEnhance.Sharpness(rgb).enhance(1.08).filter(ImageFilter.UnsharpMask(radius=.75,percent=95,threshold=2))
        im=Image.merge("RGBA",(*rgb.split(),im.getchannel("A")))
        canvas=Image.new("RGBA",(512,512),(0,0,0,0));canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2))
        path=folder/(slug(name)+".png");canvas.save(path,"PNG",optimize=True)
        out[name]="/"+path.relative_to(ROOT).as_posix()
    except Exception as e:
        print(name,e);missing.append(name)
print(json.dumps({"logos":out,"missing":missing},ensure_ascii=False))
