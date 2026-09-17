IMG Upcoming Events Fix

Files:
- index.html: replaces the empty Upcoming Events placeholders with a live calendar.
- worker.js: adds /events to the IMG Cloudflare Worker while preserving /games and /news.

Deploy:
1. Replace the GitHub Pages index.html with index.html.
2. Replace the Cloudflare Worker code with worker.js.
3. Keep the existing BALLDONTLIE_API_KEY secret unchanged.

The event calendar uses ESPN public scoreboard feeds for a rolling 7-day window across major sports and refreshes every 15 minutes in the browser. The Worker caches the event response for 5 minutes.
