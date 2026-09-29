from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"tat"/"teams"
OUT.mkdir(parents=True,exist_ok=True)

FILES={
  "new-taipei-kings.png":"https://commons.wikimedia.org/wiki/Special:Redirect/file/New%20Taipei%20Kings%20logo.png",
  "taoyuan-taiwan-beer-leopards.webp":"https://commons.wikimedia.org/wiki/Special:Redirect/file/Taoyuan%20Taiwan%20Beer%20Leopards.webp",
}
s=requests.Session()
s.headers.update({"User-Agent":"IMG-Sports-Data/1.0 (team logo cache)"})
for name,url in FILES.items():
    r=s.get(url,timeout=45,allow_redirects=True)
    r.raise_for_status()
    data=r.content
    if len(data)<3000:
        raise SystemExit(f"{name}: asset too small ({len(data)} bytes)")
    (OUT/name).write_bytes(data)
    print(name,len(data),r.url)
