# IMGOFFICIAL — Free API Edition

Upload `index.html` to the root of your GitHub Pages repository. This is a standalone static site and requires no npm/build step.

It calls TheSportsDB V1 free API using the documented free key `123` and requests today's events. The page refreshes every 60 seconds.

Important: TheSportsDB free access does not provide the premium 2-minute live-score feed for every sport. This version displays only data the free endpoint actually returns; it does not fabricate live scores.

GitHub Pages:
Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save.

For production, keep API credentials/server-side when required and review TheSportsDB's current terms and API limits.
