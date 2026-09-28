#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "logos" / "external"
REPORT_PATH = ASSET_DIR / "SOURCES.json"

TEXT_EXTS = {".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json"}
SKIP_DIRS = {
    ".git", "node_modules", "backups", ".venv", "venv",
    "assets/homepage", "assets/logos/external"
}
LOGO_WORDS = (
    "logo", "logos", "crest", "crests", "badge", "badges",
    "emblem", "emblems", "icon", "icons", "flag", "flags",
    "teamlogo", "teamlogos", "league-logo", "league_logo",
    "team-logo", "team_logo", "brandmark"
)
URL_LOGO_MARKERS = (
    "/logo", "/logos/", "logo.", "-logo", "_logo", "/crest", "/badge",
    "/emblem", "/icon", "/flags/", "/flag/", "/teamlogos/",
    "teamlogo", "league_logo", "team_logo"
)
KNOWN_LOGO_HOST_MARKERS = (
    "a.espncdn.com/i/teamlogos/",
    "media.api-sports.io/football/teams/",
    "media.api-sports.io/football/leagues/",
    "cdn.sportmonks.com/images/soccer/teams/",
    "cdn.sportmonks.com/images/soccer/leagues/",
    "images.fotmob.com/image_resources/logo/",
    "ssl.gstatic.com/onebox/media/sports/logos/",
)
IMAGE_EXT_RE = re.compile(r"\.(?:png|jpe?g|webp|gif|svg)(?:[?#][^\s\"'<>)]*)?$", re.I)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)

NON_LOGO_HINTS = (
    "thumbnail", "news", "hero", "background", "poster", "photo",
    "highlight", "youtube", "ytimg", "avatar", "headshot", "article"
)

def skipped_path(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(rel == d or rel.startswith(d + "/") for d in SKIP_DIRS)

def is_text_candidate(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TEXT_EXTS and not skipped_path(path)

def normalize_url(raw: str) -> str:
    return raw.rstrip("),;]}")

def context_for(text: str, start: int, end: int, radius: int = 260) -> str:
    return text[max(0, start-radius):min(len(text), end+radius)].lower()

def looks_like_logo(url: str, ctx: str) -> bool:
    lu = url.lower()
    context_has_logo_word = any(w in ctx for w in LOGO_WORDS)
    url_has_logo_marker = any(m in lu for m in URL_LOGO_MARKERS)
    known_logo_host = any(m in lu for m in KNOWN_LOGO_HOST_MARKERS)
    key_signal = bool(re.search(
        r"""(?ix)(?:["']?(?:logo|logo_url|logourl|crest|badge|emblem|icon|flag)["']?)\s*[:=]\s*["']?\s*$""",
        ctx[-140:]
    ))
    html_signal = bool(re.search(
        r"<img\b[^>]{0,450}(?:class|id|alt)\s*=\s*[\"'][^\"']*(?:logo|crest|badge|emblem|icon|flag)",
        ctx[-500:]
    ))
    negative = any(h in lu for h in NON_LOGO_HINTS) or any(h in ctx[-100:] for h in NON_LOGO_HINTS)
    positive = context_has_logo_word or url_has_logo_marker or known_logo_host or key_signal or html_signal
    if not positive:
        return False
    if negative and not (key_signal or html_signal or url_has_logo_marker or known_logo_host):
        return False
    return True

def find_candidates():
    refs = {}
    for path in ROOT.rglob("*"):
        if not is_text_candidate(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in URL_RE.finditer(text):
            url = normalize_url(m.group(0))
            lu = url.lower()
            if not (
                IMAGE_EXT_RE.search(url)
                or any(mark in lu for mark in URL_LOGO_MARKERS)
                or any(mark in lu for mark in KNOWN_LOGO_HOST_MARKERS)
            ):
                continue
            ctx = context_for(text, m.start(), m.end())
            if not looks_like_logo(url, ctx):
                continue
            refs.setdefault(url, set()).add(path.relative_to(ROOT).as_posix())
    return refs

def safe_stem(url: str) -> str:
    p = urlparse(url)
    name = unquote(Path(p.path).name) or "logo"
    stem = Path(name).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._").lower() or "logo"
    host = re.sub(r"[^A-Za-z0-9.-]+", "-", p.netloc).strip("-").lower()
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"{host}--{stem}--{digest}"

def extension_from_response(resp: requests.Response, url: str) -> str:
    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
    ctype_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/x-icon": ".ico",
        "image/vnd.microsoft.icon": ".ico",
    }
    if ctype in ctype_map:
        return ctype_map[ctype]
    ext = Path(urlparse(url).path).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico"}:
        return ".jpg" if ext == ".jpeg" else ext
    guessed = mimetypes.guess_extension(ctype) if ctype else None
    return guessed or ".img"

def validate_image_bytes(data: bytes, ext: str) -> bool:
    if len(data) < 100:
        return False
    if ext == ".svg":
        return b"<svg" in data[:4096].lower()
    if ext == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".jpg":
        return data.startswith(b"\xff\xd8\xff")
    if ext == ".gif":
        return data.startswith(b"GIF8")
    if ext == ".webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    if ext == ".ico":
        return data.startswith(b"\x00\x00\x01\x00")
    return True

def download_all(refs):
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "IMG-Sports-Data/1.0 (external logo asset cache)"})
    mapping = {}
    failures = {}
    for url in sorted(refs):
        try:
            resp = session.get(url, timeout=45, allow_redirects=True)
            resp.raise_for_status()
            data = resp.content
            if len(data) > 20 * 1024 * 1024:
                raise RuntimeError(f"asset too large: {len(data)} bytes")
            ext = extension_from_response(resp, url)
            if not validate_image_bytes(data, ext):
                raise RuntimeError(
                    f"response is not a recognized image "
                    f"(content-type={resp.headers.get('content-type')!r}, {len(data)} bytes)"
                )
            filename = safe_stem(url) + ext
            out = ASSET_DIR / filename
            out.write_bytes(data)
            mapping[url] = "/assets/logos/external/" + filename
            print(f"CACHED {url} -> {mapping[url]} ({len(data)} bytes)")
        except Exception as e:
            failures[url] = str(e)
            print(f"FAILED {url}: {e}", file=sys.stderr)
    return mapping, failures

def rewrite_refs(mapping):
    changed_files = []
    for path in ROOT.rglob("*"):
        if not is_text_candidate(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        original = text
        for url, local in mapping.items():
            if url in text:
                text = text.replace(url, local)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed_files.append(path.relative_to(ROOT).as_posix())
    return changed_files

def main():
    refs = find_candidates()
    print(f"Detected {len(refs)} unique external logo URL(s).")
    for url, files in sorted(refs.items()):
        print("FOUND", url, "in", ", ".join(sorted(files)))

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    if not refs:
        REPORT_PATH.write_text(json.dumps({
            "detected": 0,
            "cached": 0,
            "failed": {},
            "remaining_external_logo_urls": {},
            "sources": {}
        }, indent=2) + "\n", encoding="utf-8")
        return 0

    mapping, failures = download_all(refs)
    changed_files = rewrite_refs(mapping)
    remaining = find_candidates()

    report = {
        "detected": len(refs),
        "cached": len(mapping),
        "failed": failures,
        "changed_files": changed_files,
        "remaining_external_logo_urls": {u: sorted(v) for u, v in sorted(remaining.items())},
        "sources": {
            local: {"source_url": url, "referenced_by": sorted(refs[url])}
            for url, local in sorted(mapping.items())
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "detected": len(refs),
        "cached": len(mapping),
        "failed": len(failures),
        "changed_files": len(changed_files),
        "remaining": len(remaining),
    }, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
