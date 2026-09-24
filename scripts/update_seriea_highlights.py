from football_highlights_common import run
run({
  "leagueKey":"seriea",
  "league":"Serie A",
  "output":"seriea-highlights.json",
  "mode":"youtube",
  "handle":"seriea",
  "includeAny":["HIGHLIGHT"],
  "requireAny":["2026/27"],
  "excludeAny":["PRIMAVERA","WOMEN","FEMMINILE"],
  "maxAgeDays":90,
  "sourceName":"Serie A Official YouTube",
  "sourceUrl":"https://www.youtube.com/@seriea",
  "limit":12
})
