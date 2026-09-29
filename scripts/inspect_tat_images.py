import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL="https://www.theasiantournament.com/"
html=requests.get(URL,timeout=30,headers={"User-Agent":"Mozilla/5.0"}).text
soup=BeautifulSoup(html,"html.parser")
items=[]
for img in soup.find_all("img"):
    src=img.get("src") or img.get("data-src") or ""
    alt=img.get("alt") or ""
    cls=" ".join(img.get("class") or [])
    parent=" ".join((img.parent.get("class") or []) if getattr(img,"parent",None) else [])
    if src:
        items.append({"src":urljoin(URL,src),"alt":alt,"class":cls,"parentClass":parent,"width":img.get("width"),"height":img.get("height")})
for link in soup.find_all("link"):
    rel=" ".join(link.get("rel") or [])
    href=link.get("href") or ""
    if href and ("icon" in rel.lower() or "apple" in rel.lower()):
        items.append({"src":urljoin(URL,href),"alt":"favicon","class":rel,"parentClass":"","width":None,"height":None})
print(json.dumps(items,indent=2))
open("tat-site-image-report.json","w",encoding="utf-8").write(json.dumps(items,indent=2))
