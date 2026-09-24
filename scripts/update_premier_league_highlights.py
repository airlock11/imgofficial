from football_highlights_common import run
run({
  "leagueKey":"soccer",
  "league":"Premier League",
  "output":"premier-league-highlights.json",
  "mode":"youtube",
  "seedVideo":"SxiMucn6hTc",
  "includeAny":["HIGHLIGHT","HIGHLIGHTS","GOALS"],
  "requireAny":["2026/27"],
  "excludeAny":["2025/26","2024/25","CLASSIC","HISTORY"],
  "maxAgeDays":90,
  "sourceName":"Premier League Official YouTube",
  "sourceUrl":"https://www.youtube.com/PremierLeague",
  "limit":12
})
