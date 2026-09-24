from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGES=[
"leagues/el-salvador-reserves/index.html",
"leagues/serie-a/index.html",
"leagues/bundesliga/index.html",
"leagues/champions-league/index.html",
"leagues/champions-league-women/index.html",
"leagues/mls/index.html",
"leagues/pfl/index.html",
]
OLD='<script src="/football-page.js?v=20260925-highlights2" defer></script>'
NEW='<script src="/football-team-logos.js?v=20260925-teamlogos1" defer></script>\n<script src="/football-page.js?v=20260925-teamlogos1" defer></script>'
for rel in PAGES:
    p=ROOT/rel
    text=p.read_text("utf-8")
    if "football-team-logos.js" not in text:
        if OLD not in text:
            raise SystemExit(f"Missing script anchor: {rel}")
        text=text.replace(OLD,NEW,1)
        p.write_text(text,"utf-8")
    print(rel)
