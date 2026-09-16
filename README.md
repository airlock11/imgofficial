# IMGOFFICIAL — Live Sports Data

A GitHub-ready React + Vite frontend for a live sports data platform.

## Run locally

```bash
npm install
npm run dev
```

Open the local URL shown by Vite.

## Build

```bash
npm run build
```

The production files are created in `dist/`.

## Deploy

This project works well with Vercel, Netlify, Cloudflare Pages, or GitHub Pages (with the appropriate Vite base configuration if deploying under a repository subpath).

### GitHub upload

1. Create a repository named `imgofficial`.
2. Upload all files in this folder to the repository root.
3. Commit the files.
4. Connect the repository to your hosting provider.
5. Set the production domain to `imgofficial.com`.

## Live data

The current interface intentionally uses sample data. To make scores/odds genuinely live, connect a licensed sports-data provider through a secure backend/API layer. Do not put private API keys in frontend source code.

Suggested architecture:

Browser → API/backend → licensed sports-data provider

For real-time streaming, the backend can push updates to browsers with WebSockets or Server-Sent Events.
