IMG Website — Guaranteed Highlights build

This build intentionally includes official FIBA highlight cards directly in index.html.
The page therefore displays highlights immediately without waiting for Cloudflare.
The Cloudflare /highlights endpoint is only an enhancement: when it returns valid newer
items, the page replaces the built-in cards with those items. If the endpoint fails,
the built-in official cards remain visible.

Deploy this entire website folder to the GitHub Pages repository, replacing the existing index.html and assets.
