from pathlib import Path
import requests, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"tat"/"highlights"
OUT.mkdir(parents=True,exist_ok=True)

VIDEOS=["pb7eewi3xZ0","dbOeM6XMaYk","e-5PoM8toIA","Z_K1PIXxncU"]
CANDIDATES=["maxresdefault.jpg","sddefault.jpg","hq720.jpg","hqdefault.jpg"]

session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (IMG Sports Data; TAT thumbnail cache)"})
report={}
for vid in VIDEOS:
    ok=False
    for name in CANDIDATES:
        url=f"https://i.ytimg.com/vi/{vid}/{name}"
        try:
            r=session.get(url,timeout=30)
            if not r.ok or len(r.content)<5000: continue
            if not (r.content.startswith(b"\xff\xd8") or r.content.startswith(b"\x89PNG")): continue
            path=OUT/f"{vid}.jpg"
            path.write_bytes(r.content)
            report[vid]={"source":url,"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest()}
            print(vid,name,len(r.content),report[vid]["sha256"])
            ok=True
            break
        except Exception as e:
            print("ERR",vid,name,e)
    if not ok:
        raise SystemExit(f"No usable thumbnail for {vid}")

hashes=[x["sha256"] for x in report.values()]
if len(set(hashes)) != len(hashes):
    raise SystemExit("Duplicate TAT highlight thumbnails detected")

(OUT/"SOURCES.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
