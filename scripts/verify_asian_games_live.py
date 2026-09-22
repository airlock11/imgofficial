#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"youtube-live.json"
KEY=os.environ["YOUTUBE_API_KEY"]
UA="IMG-Sports-Live-Verify/1.0"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.load(r)

def details(ids):
    if not ids:
        return {}
    params=urllib.parse.urlencode({
        "part":"snippet,status,liveStreamingDetails",
        "id":",".join(ids),
        "key":KEY
    })
    data=get_json("https://www.googleapis.com/youtube/v3/videos?"+params)
    return {x.get("id"):x for x in data.get("items",[]) if x.get("id")}

def is_live_now(row):
    sn=row.get("snippet",{})
    live=row.get("liveStreamingDetails",{})
    return (
        sn.get("liveBroadcastContent")=="live"
        and bool(live.get("actualStartTime"))
        and not bool(live.get("actualEndTime"))
    )

def valid_asian_title(title):
    upper=str(title or "").upper()
    tagged=(
        "ASIAN GAMES" in upper
        or "AICHI-NAGOYA" in upper
        or "AICHI NAGOYA" in upper
        or "AICHI 2026" in upper
    )
    blocked=("HIGHLIGHTS","REPLAY","FULL MATCH","FULL GAME","OPENING CEREMONY",
             "CLOSING CEREMONY","DRAW CEREMONY","PRESS CONFERENCE","INTERVIEW","PODCAST")
    return tagged and not any(x in upper for x in blocked)

def main():
    if not OUT.exists():
        return
    payload=json.loads(OUT.read_text("utf-8"))
    streams=list(payload.get("streams",[]))
    asian=[x for x in streams if x.get("leagueKey")=="asian_games"]
    ids=[]
    for x in asian:
        vid=(x.get("stream") or {}).get("videoId")
        if vid and vid not in ids:
            ids.append(vid)

    current={}
    for i in range(0,len(ids),50):
        current.update(details(ids[i:i+50]))

    now=datetime.now(timezone.utc).isoformat()
    kept=[]
    removed=[]
    for item in streams:
        if item.get("leagueKey")!="asian_games":
            kept.append(item)
            continue
        stream=item.get("stream") or {}
        vid=stream.get("videoId")
        row=current.get(vid)
        title=(row or {}).get("snippet",{}).get("title") or item.get("title") or stream.get("title") or ""
        channel=(row or {}).get("snippet",{}).get("channelTitle") or stream.get("channel") or ""
        channel_ok="one sports" in str(channel).lower()
        title_ok=valid_asian_title(title)
        if row:
            live_ok=is_live_now(row)
            if not (live_ok and channel_ok and title_ok):
                removed.append(vid or item.get("eventId"))
                continue
        else:
            # Short fail-open grace period only for previously verified One Sports
            # Asian Games streams when the YouTube API temporarily omits a video.
            try:
                last=datetime.fromisoformat(str(item.get("lastVerifiedLiveAt") or stream.get("lastVerifiedLiveAt") or "").replace("Z","+00:00"))
                age=(datetime.now(timezone.utc)-last.astimezone(timezone.utc)).total_seconds()
            except Exception:
                age=999999
            if not (channel_ok and title_ok and age <= 180):
                removed.append(vid or item.get("eventId"))
                continue
        item["title"]=title
        item["verificationStatus"]="verified"
        item["lastVerifiedLiveAt"]=now
        stream["title"]=title
        stream["channel"]=channel
        stream["verificationStatus"]="verified"
        stream["lastVerifiedLiveAt"]=now
        item["stream"]=stream
        kept.append(item)

    payload["streams"]=kept
    payload["updatedAt"]=now
    payload["asianGamesVerification"]={
        "checkedAt":now,
        "method":"YouTube videos API exact-video verification",
        "verifiedLiveCount":sum(1 for x in kept if x.get("leagueKey")=="asian_games"),
        "removedCount":len(removed)
    }
    OUT.write_text(json.dumps(payload,indent=2)+"\n","utf-8")
    print("Asian Games exact live verification:",payload["asianGamesVerification"],"removed",removed)

if __name__=="__main__":
    main()
