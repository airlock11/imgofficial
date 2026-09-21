#!/usr/bin/env python3
import json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"special-sports-data.json"
JST=timezone(timedelta(hours=9))
TODAY=datetime.now(JST).strftime("%Y-%m-%d")
BASE="https://results.asiangames2026.org"
SCHEDULE=f"{BASE}/#/schedule/daily/{TODAY}"

def summarize_json(value, depth=0):
    if depth>2:
        return type(value).__name__
    if isinstance(value,dict):
        return {str(k):summarize_json(v,depth+1) for k,v in list(value.items())[:24]}
    if isinstance(value,list):
        return [summarize_json(x,depth+1) for x in value[:3]]
    return value if isinstance(value,(str,int,float,bool)) or value is None else type(value).__name__

def main():
    captured=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1200},locale="en-US")

        def on_response(resp):
            try:
                ct=(resp.headers.get("content-type") or "").lower()
                if "json" not in ct:
                    return
                if "asiangames2026.org" not in resp.url:
                    return
                data=resp.json()
                captured.append((resp.url,data))
            except Exception:
                pass

        page.on("response",on_response)
        page.goto(SCHEDULE,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(10000)

        body=page.locator("body").inner_text(timeout=10000)
        print("ASIAN_GAMES_PAGE",page.url)
        print("ASIAN_GAMES_BODY_BEGIN")
        print(body[:12000])
        print("ASIAN_GAMES_BODY_END")

        links=page.locator("a").evaluate_all("""els => els.slice(0,250).map(a => ({text:(a.innerText||'').trim(),href:a.href}))""")
        print("ASIAN_GAMES_LINKS",json.dumps(links,ensure_ascii=False)[:12000])

        print("ASIAN_GAMES_JSON_COUNT",len(captured))
        for url,data in captured[-40:]:
            try:
                print("ASIAN_GAMES_JSON",url,json.dumps(summarize_json(data),ensure_ascii=False)[:6000])
            except Exception:
                print("ASIAN_GAMES_JSON",url,type(data).__name__)

        browser.close()

    # Probe-only safety for the first run: preserve published data until the
    # official page schema is identified from the captured responses.
    if OUT.exists():
        data=json.loads(OUT.read_text("utf-8"))
        data.setdefault("leagues",{}).setdefault("asian_games",{})["autoUpdateSource"]=SCHEDULE
        data["leagues"]["asian_games"]["autoUpdateProbeAt"]=datetime.now(timezone.utc).isoformat()
        OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf-8")

if __name__=="__main__":
    main()
