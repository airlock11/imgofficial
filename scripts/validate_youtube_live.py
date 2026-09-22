#!/usr/bin/env python3
import json, sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"youtube-live.json"

def fail(msg):
    raise SystemExit("YouTube live validation failed: "+msg)

if not PATH.exists():
    fail("youtube-live.json is missing")

try:
    data=json.loads(PATH.read_text("utf-8"))
except Exception as ex:
    fail("invalid JSON: "+str(ex))

if not isinstance(data,dict):
    fail("root must be an object")

updated=data.get("updatedAt")
try:
    datetime.fromisoformat(str(updated).replace("Z","+00:00"))
except Exception:
    fail("updatedAt is missing or invalid")

streams=data.get("streams")
if not isinstance(streams,list):
    fail("streams must be an array")

seen=set()
for i,item in enumerate(streams):
    if not isinstance(item,dict):
        fail(f"streams[{i}] must be an object")
    stream=item.get("stream")
    if not isinstance(stream,dict):
        fail(f"streams[{i}].stream is missing")
    vid=str(stream.get("videoId") or "")
    if len(vid)!=11:
        fail(f"streams[{i}] has invalid YouTube videoId")
    if vid in seen:
        fail(f"duplicate videoId {vid}")
    seen.add(vid)
    url=str(stream.get("watchUrl") or "")
    if vid not in url or "youtube.com" not in url:
        fail(f"streams[{i}] has invalid watchUrl")
    status=str(item.get("verificationStatus") or stream.get("verificationStatus") or "")
    if status not in {"verified","grace","fallback"}:
        fail(f"streams[{i}] has invalid verificationStatus {status!r}")
    stamp=item.get("lastVerifiedLiveAt") or stream.get("lastVerifiedLiveAt")
    if status in {"verified","grace"}:
        try:
            datetime.fromisoformat(str(stamp).replace("Z","+00:00"))
        except Exception:
            fail(f"streams[{i}] missing valid lastVerifiedLiveAt")

print(f"PASS: youtube-live.json valid with {len(streams)} stream(s)")
