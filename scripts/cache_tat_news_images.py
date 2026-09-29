from pathlib import Path
import requests, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"tat"/"news"
OUT.mkdir(parents=True,exist_ok=True)

ASSETS={
  "leg-1-champions.png":"https://cdn.prod.website-files.com/69a01736018fd24d4bed7e60/6a279c9681ee2e9d052f7403_TAT%20-%20championship%20image.png",
  "leg-2-laizhou.png":"https://cdn.prod.website-files.com/69a01736018fd24d4bed7e60/6a2f9d1cbe544df3944921d6_Laizhou%2C%20China%20(1).png",
  "leg-3-chengdu.jpg":"https://cdn.prod.website-files.com/69a01736018fd24d4bed7e60/6a5e005c7e841f9b10074526_Weixin%20Image_20260720155229_4349_676.jpg",
}

s=requests.Session()
s.headers.update({"User-Agent":"IMG-Sports-Data/1.0 (TAT news image cache)"})
report={}
for name,url in ASSETS.items():
    r=s.get(url,timeout=45)
    r.raise_for_status()
    if len(r.content)<5000:
        raise SystemExit(f"{name}: image too small ({len(r.content)} bytes)")
    (OUT/name).write_bytes(r.content)
    report[name]={"source":url,"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest()}
    print(name,len(r.content),report[name]["sha256"])
(OUT/"SOURCES.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
