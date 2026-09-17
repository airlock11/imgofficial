IMG Sports Website — Highlights Replacement

Changes in this version:
- Removed the Live Broadcast / Live Streaming section and its popup player.
- Removed all frontend polling of the /broadcasts endpoint.
- Latest Highlights now occupies the position where Live Broadcast was shown.
- Highlights are loaded from the Worker /highlights endpoint.
- Highlights use official sports league, federation and broadcaster YouTube channels only.
- Highlights section hides automatically if no verified highlight videos are returned.
- Highlight cards open an in-site YouTube player.
- Responsive: 4 columns desktop, 2 columns tablet/mobile.
- Highlights refresh every 15 minutes.

Deploy this website ZIP to the GitHub Pages repository.
The Worker ZIP should be deployed separately.
