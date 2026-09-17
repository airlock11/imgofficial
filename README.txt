IMG Upcoming Events Live Fix

Replace BOTH files:
1. index.html in GitHub
2. worker.js in the Cloudflare Worker and GitHub

Keep the existing BALLDONTLIE_API_KEY Cloudflare secret unchanged.

Important fix: ESPN scoreboard requests no longer send a custom User-Agent header, which can cause ESPN's edge to reject the request. The Worker also reports how many ESPN sources failed in the /events JSON response.
