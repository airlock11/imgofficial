#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright
from update_asian_games_web import scrape_live

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"asian-games-live.json"
JST=timezone(timedelta(hours=9))

def main():
    day=datetime.now(JST).strftime("%Y-%m-%d")
    games=[]
    with sync_playwright() as p:
        try:
            browser=p.chromium.launch(channel="chrome",headless=True)
        except Exception:
            browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1200},locale="en-US")
        try:
            games=scrape_live(page,day)
        finally:
            browser.close()

    now=datetime.now(timezone.utc).isoformat()
    payload={
        "special":True,
        "league":"Asian Games",
        "live":bool(games),
        "updatedAt":now,
        "sourceName":"Aichi-Nagoya 2026 Official Live Results",
        "sourceUrl":"https://results.asiangames2026.org/#/schedule/live",
        "games":games
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n","utf-8")
    print("asian-games-live",len(games))

if __name__=="__main__":
    main()
