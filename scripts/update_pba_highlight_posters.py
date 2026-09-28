#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "pba-official.json"
OUT = ROOT / "assets" / "pba" / "highlights"
OUT.mkdir(parents=True, exist_ok=True)

def run(cmd):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)

def make_poster(video_id: str, out: Path):
    with tempfile.TemporaryDirectory(prefix="pba-short-") as td:
        td = Path(td)
        template = td / f"{video_id}.%(ext)s"

        # Video-only is enough and avoids unnecessary audio bandwidth.
        run([
            "yt-dlp",
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "-f", "bestvideo[height<=1920]/best[height<=1920]/best",
            "-o", str(template),
            f"https://www.youtube.com/shorts/{video_id}",
        ])

        media = next((p for p in td.iterdir() if p.is_file()), None)
        if not media:
            raise RuntimeError(f"No downloaded media for {video_id}")

        # Extract a clean frame near the start. Keep the source vertical
        # geometry and cap width at 1080 for sharp mobile cards.
        run([
            "ffmpeg", "-y",
            "-ss", "1.25",
            "-i", str(media),
            "-frames:v", "1",
            "-vf", "scale='min(1080,iw)':-2:flags=lanczos",
            "-q:v", "2",
            str(out),
        ])

        if not out.exists() or out.stat().st_size < 20_000:
            raise RuntimeError(f"Poster output invalid for {video_id}")

def main():
    obj = json.loads(DATA.read_text(encoding="utf-8"))
    shorts = obj.get("shorts") or []
    shorts = [x for x in shorts if x.get("id")][:10]
    if not shorts:
        print("No PBA Shorts found.")
        return 0

    failures = {}
    for item in shorts:
        video_id = str(item["id"]).strip()
        out = OUT / f"{video_id}.jpg"
        try:
            make_poster(video_id, out)
            print(f"POSTER {video_id}: {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
        except Exception as e:
            failures[video_id] = str(e)
            print(f"FAILED {video_id}: {e}")

    report = {
        "requested": len(shorts),
        "created": len(shorts) - len(failures),
        "failed": failures,
        "posters": {
            str(x["id"]): f"/assets/pba/highlights/{x['id']}.jpg"
            for x in shorts
            if (OUT / f"{x['id']}.jpg").exists()
        },
    }
    (OUT / "posters.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Require all current visible highlight posters to succeed.
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
