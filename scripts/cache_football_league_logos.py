from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "football" / "leagues"
OUT.mkdir(parents=True, exist_ok=True)

LEAGUES = {
    "premier-league.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "la-liga.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "serie-a.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/12.png",
    "bundesliga.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/10.png",
    "champions-league.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/2.png",
    "mls.png": "https://a.espncdn.com/i/leaguelogos/soccer/500/19.png",
}

session = requests.Session()
session.headers.update({"User-Agent": "IMG-Sports-Data/1.0 (football league logo cache)"})

lines = ["# Football league logo sources", ""]
for name, url in LEAGUES.items():
    r = session.get(url, timeout=45)
    r.raise_for_status()
    data = r.content
    if len(data) < 1000 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"Invalid PNG for {name}: {len(data)} bytes")
    path = OUT / name
    path.write_bytes(data)
    print(f"{name}: {len(data)} bytes")
    lines.append(f"- `/{path.relative_to(ROOT).as_posix()}` — {url}")

(OUT / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
