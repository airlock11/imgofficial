# IMG + BALLDONTLIE Secure Setup

This package changes IMG's live-score data source to BALLDONTLIE while keeping the API key out of the public website.

## Important
GitHub Pages is static hosting. Do NOT put your BALLDONTLIE key inside `index.html`.

Use a Cloudflare Worker as the secure proxy:

1. Create a Cloudflare account and open **Workers & Pages**.
2. Create a Worker.
3. Paste `worker/worker.js` into the Worker.
4. Add a Worker secret named:
   `BALLDONTLIE_API_KEY`
5. Set its value to your BALLDONTLIE API key.
6. Deploy the Worker.
7. Copy the Worker URL, for example:
   `https://img-sports-api.<your-subdomain>.workers.dev`
8. In `site/index.html`, replace:
   `https://YOUR-WORKER-URL.workers.dev`
   with your actual Worker URL.
9. Upload the updated `site/index.html` to your GitHub Pages repository.

The browser will then call:
IMG website -> Cloudflare Worker -> BALLDONTLIE

The API key stays on the Worker and is not sent to visitors.

## Free BALLDONTLIE
The current free account includes NBA, NFL, MLB and EPL and is limited to 5 requests/minute. The NBA Games endpoint provides real-time data for in-progress games.

Do not publish the API key in GitHub. Since the key was previously pasted into chat, rotate it in your BALLDONTLIE account before production use.
