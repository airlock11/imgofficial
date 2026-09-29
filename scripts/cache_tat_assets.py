from pathlib import Path
import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"tat"
TEAMS=OUT/"teams"
OUT.mkdir(parents=True,exist_ok=True)
TEAMS.mkdir(parents=True,exist_ok=True)

session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (IMG Sports Data; TAT asset cache)"})

ASSETS={
  "tat-logo-white.png":"https://cdn.prod.website-files.com/69a009acf65e4013015cdd50/69d7b2014366e41e8e246be3_TAT_Guideline_ol_logotype-white.png",
  "tat-icon-black.png":"https://cdn.prod.website-files.com/69a009acf65e4013015cdd50/69b7e1ca13c2ad0236a49308_TAT_Guideline_ol_icon-black.png",
  "tat-hero.png":"https://cdn.prod.website-files.com/69a01736018fd24d4bed7e60/6a279c9681ee2e9d052f7403_TAT%20-%20championship%20image.png",
}
def get(url):
    r=session.get(url,timeout=45)
    r.raise_for_status()
    if len(r.content)<500: raise RuntimeError(f"Asset too small: {url}")
    return r.content
for name,url in ASSETS.items():
    data=get(url); (OUT/name).write_bytes(data); print(name,len(data))

KNOWN=[
"donglai cultural and tourism - underdawg hoopers","global billion stars club","guangzhou loong lions ii",
"hong kong eastern","macau black knights","nihon tengus","philippine aces united","qingdao guoxin haitian ii",
"shenzhen new century leopards ii","sichuan blue whales ii","statham academy","thailand titans","vanta black dragons"
]
html=session.get("https://www.theasiantournament.com/all-teams",timeout=45).text
soup=BeautifulSoup(html,"html.parser")
found={}
for heading in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
    name=" ".join(heading.stripped_strings).strip()
    key=name.lower()
    if key not in KNOWN: continue
    node=heading
    img=None
    for _ in range(8):
        node=node.parent
        if node is None: break
        img=node.find("img")
        if img and (img.get("src") or img.get("data-src")): break
    if img:
        src=urljoin("https://www.theasiantournament.com/",img.get("src") or img.get("data-src"))
        found[name]=src

# fallback: homepage team-logo sequence is useful if the teams page markup changes;
# do not guess associations—only save mappings discovered next to headings.
def slug(s):
    return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
report={"leagueAssets":ASSETS,"teams":{},"missing":[]}
for wanted in KNOWN:
    actual=next((n for n in found if n.lower()==wanted),None)
    if not actual:
        report["missing"].append(wanted); continue
    url=found[actual]
    ext=Path(urlparse(url).path).suffix.lower()
    if ext not in {".png",".jpg",".jpeg",".webp",".svg"}: ext=".png"
    filename=slug(actual)+ext
    data=get(url)
    (TEAMS/filename).write_bytes(data)
    report["teams"][actual]={"local":"/assets/tat/teams/"+filename,"source":url,"bytes":len(data)}
    print(actual,filename,len(data))
(OUT/"SOURCES.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if report["missing"]:
    print("Missing team mappings:",report["missing"])
