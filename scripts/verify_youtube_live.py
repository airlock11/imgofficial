#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"youtube-live.json"
KEY=os.environ["YOUTUBE_API_KEY"]
UA="IMG-Sports-Live-Verify/2.0"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.load(r)

def details(ids):
    if not ids:return {}
    params=urllib.parse.urlencode({
        "part":"snippet,status,liveStreamingDetails",
        "id":",".join(ids),
        "key":KEY
    })
    data=get_json("https://www.googleapis.com/youtube/v3/videos?"+params)
    return {x.get("id"):x for x in data.get("items",[]) if x.get("id")}

def live_state(row):
    sn=row.get("snippet",{})
    live=row.get("liveStreamingDetails",{})
    if live.get("actualEndTime"):
        return "ended"
    if sn.get("liveBroadcastContent")=="live":
        return "live"
    if live.get("actualStartTime") and not live.get("actualEndTime"):
        return "live"
    return "not_live"

def valid_asian_title(title):
    upper=str(title or "").upper()
    tagged=("ASIAN GAMES" in upper or "AICHI-NAGOYA" in upper or "AICHI NAGOYA" in upper or "AICHI 2026" in upper)
    blocked=("HIGHLIGHTS","REPLAY","FULL MATCH","FULL GAME","OPENING CEREMONY","CLOSING CEREMONY","DRAW CEREMONY","PRESS CONFERENCE","INTERVIEW","PODCAST")
    return tagged and not any(x in upper for x in blocked)

def age_seconds(value):
    try:
        dt=datetime.fromisoformat(str(value or "").replace("Z","+00:00"))
        return (datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()
    except Exception:
        return 999999

def main():
    if not OUT.exists():
        return
    payload=json.loads(OUT.read_text("utf-8"))
    streams=list(payload.get("streams",[]))
    ids=[]
    for x in streams:
        vid=(x.get("stream") or {}).get("videoId")
        if vid and vid not in ids: ids.append(vid)

    current={}
    for i in range(0,len(ids),50):
        current.update(details(ids[i:i+50]))

    now=datetime.now(timezone.utc).isoformat()
    kept=[]; removed=[]
    for item in streams:
        stream=item.get("stream") or {}
        vid=stream.get("videoId")
        if not vid:
            kept.append(item)
            continue

        row=current.get(vid)
        if row:
            state=live_state(row)
            if state!="live":
                removed.append({"videoId":vid,"leagueKey":item.get("leagueKey"),"reason":state})
                continue

            title=row.get("snippet",{}).get("title") or item.get("title") or stream.get("title") or ""
            channel=row.get("snippet",{}).get("channelTitle") or stream.get("channel") or ""
            if item.get("leagueKey")=="asian_games":
                if "one sports" not in str(channel).lower() or not valid_asian_title(title):
                    removed.append({"videoId":vid,"leagueKey":"asian_games","reason":"source_or_title_invalid"})
                    continue
            item["title"]=title
            stream["title"]=title
            stream["channel"]=channel
        else:
            # Brief fail-open for transient API omission only. Do NOT refresh
            # lastVerifiedLiveAt here; otherwise repeated API omissions could
            # keep a stale/ended stream alive indefinitely.
            last=item.get("lastVerifiedLiveAt") or stream.get("lastVerifiedLiveAt")
            if age_seconds(last)>180:
                removed.append({"videoId":vid,"leagueKey":item.get("leagueKey"),"reason":"api_missing_stale"})
                continue
            item["stream"]=stream
            kept.append(item)
            continue

        item["verificationStatus"]="verified"
        item["lastVerifiedLiveAt"]=now
        stream["verificationStatus"]="verified"
        stream["lastVerifiedLiveAt"]=now
        item["stream"]=stream
        kept.append(item)

    payload["streams"]=kept
    payload["updatedAt"]=now
    payload["liveVerification"]={
        "checkedAt":now,
        "method":"YouTube videos API exact-video verification",
        "verifiedLiveCount":len(kept),
        "removedCount":len(removed),
        "removed":removed
    }
    OUT.write_text(json.dumps(payload,indent=2)+"\n","utf-8")
    print("Exact YouTube live verification:",payload["liveVerification"])

if __name__=="__main__":
    main()
