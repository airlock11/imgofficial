#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html.parser, pathlib, re, subprocess, sys, tempfile
from urllib.parse import urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
TEXT_EXTS={".html",".js",".css",".json",".py",".yml",".yaml",".mjs",".cjs",".xml",".md",".txt"}
ASSET_EXTS={".js",".css",".json",".jpg",".jpeg",".png",".svg",".webp",".gif",".ico",".xml",".txt"}
errors=[]
warnings=[]

class RefParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs=[]
        self.scripts=[]
        self._script=False
        self._buf=[]
        self._script_src=False
        self._script_type=""
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        for key in ("src","href"):
            val=d.get(key)
            if val:self.refs.append((tag,key,val))
        if tag=="script":
            self._script=True
            self._buf=[]
            self._script_src=bool(d.get("src"))
            self._script_type=str(d.get("type") or "").strip().lower()
    def handle_endtag(self,tag):
        if tag=="script" and self._script:
            if not self._script_src and self._script_type in ("","text/javascript","application/javascript","module"):
                self.scripts.append("".join(self._buf))
            self._script=False
            self._buf=[]
            self._script_src=False
            self._script_type=""
    def handle_data(self,data):
        if self._script and not self._script_src:self._buf.append(data)

def local_path(ref,base):
    ref=ref.strip()
    if not ref or ref.startswith(("#","data:","mailto:","tel:","javascript:","blob:","//")):
        return None
    u=urlsplit(ref)
    if u.scheme or u.netloc:return None
    p=u.path
    if not p:return None
    candidate=(ROOT/p.lstrip("/")) if p.startswith("/") else (base.parent/p)
    try:
        candidate=candidate.resolve()
        if candidate.exists():
            return candidate
        if not p.startswith("/"):
            root_candidate=(ROOT/p).resolve()
            if root_candidate.exists():
                return root_candidate
        return candidate
    except:return None

def node_check(code,label):
    if not code.strip():return
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False,encoding="utf-8") as f:
        f.write(code)
        name=f.name
    try:
        proc=subprocess.run(["node","--check",name],capture_output=True,text=True)
        if proc.returncode:
            errors.append(f"{label}: inline JavaScript syntax error: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else 'node --check failed'}")
    finally:
        pathlib.Path(name).unlink(missing_ok=True)

files=[p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]

# 1. Every HTML page: parse, validate inline JavaScript, validate local file refs.
for p in files:
    if p.suffix.lower()!=".html":continue
    text=p.read_text("utf-8",errors="replace")
    parser=RefParser()
    try:parser.feed(text)
    except Exception as ex:errors.append(f"{p.relative_to(ROOT)}: HTML parse failure: {ex}")
    for idx,code in enumerate(parser.scripts,1):
        node_check(code,f"{p.relative_to(ROOT)} inline script #{idx}")
    for tag,key,ref in parser.refs:
        target=local_path(ref,p)
        if target is None:continue
        # Route links such as /scores/ are pages, not file assets. Check explicit assets and scripts/styles/images.
        ext=pathlib.Path(urlsplit(ref).path).suffix.lower()
        if ext in ASSET_EXTS and not target.exists():
            errors.append(f"{p.relative_to(ROOT)}: missing local {key} asset {ref}")

# 2. CSS url(...) references.
css_url=re.compile(r"url\((['\"]?)([^)'\"]+)\1\)",re.I)
for p in files:
    if p.suffix.lower()!=".css":continue
    text=p.read_text("utf-8",errors="replace")
    for _,ref in css_url.findall(text):
        target=local_path(ref,p)
        if target is None:continue
        ext=pathlib.Path(urlsplit(ref).path).suffix.lower()
        if ext in ASSET_EXTS and not target.exists():
            errors.append(f"{p.relative_to(ROOT)}: missing CSS asset {ref}")

# 3. Removed league contract: these must not reappear in active UI/data configuration.
removed=re.compile(r"\b(?:cba|wcba)\b",re.I)
for rel in ["app.js","sports/index.html","score-league-user-logos.js","league-data-registry.json","extended-sports-data.json"]:
    p=ROOT/rel
    if p.exists() and removed.search(p.read_text("utf-8",errors="replace")):
        errors.append(f"{rel}: removed CBA/WCBA reference remains")

# 4. Detect obvious accidental one-token debris in object/list areas from automated edits.
for rel in ["app.js","sports/index.html","score-league-user-logos.js"]:
    p=ROOT/rel
    if not p.exists():continue
    lines=p.read_text("utf-8",errors="replace").splitlines()
    for i,line in enumerate(lines,1):
        if re.fullmatch(r"\s*[A-Za-z]\s*",line):
            errors.append(f"{rel}:{i}: suspicious stray single-letter line {line.strip()!r}")

# 5. Exact duplicate files and zero-byte text files are maintenance warnings.
groups={}
for p in files:
    if p.suffix.lower() not in TEXT_EXTS:continue
    raw=p.read_bytes()
    if not raw:
        warnings.append(f"{p.relative_to(ROOT)}: zero-byte text file")
    h=hashlib.sha256(raw).hexdigest()
    groups.setdefault(h,[]).append(p.relative_to(ROOT))
for paths in groups.values():
    if len(paths)>1:
        warnings.append("exact duplicate text files: "+", ".join(map(str,paths)))

if warnings:
    print("Repository audit warnings:")
    for w in warnings:print(" -",w)
if errors:
    print("Repository audit failures:",file=sys.stderr)
    for e in errors:print(" -",e,file=sys.stderr)
    raise SystemExit(1)
print(f"Repository audit passed: {len(files)} files checked.")
