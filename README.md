# IMG — BALLDONTLIE Connected Website

This version connects the IMG website to the secure Cloudflare Worker:

https://img-api-proxy.magsipocarnie.workers.dev/games

## Upload to GitHub Pages

1. Extract this ZIP.
2. Upload `index.html` to the root of your GitHub Pages repository.
3. Commit/save the change.
4. Open your IMG website.

## API security

The BALLDONTLIE API key is NOT inside this website.
It is stored as the Cloudflare Worker secret:

BALLDONTLIE_API_KEY

The browser only calls the Cloudflare Worker.

## Current coverage

This build is configured for the NBA games endpoint through the Worker.
The Live Scores page requests today's games and refreshes live data automatically.

No betting odds are included.
