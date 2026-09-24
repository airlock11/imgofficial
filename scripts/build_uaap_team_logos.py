from pathlib import Path
from io import BytesIO
from collections import deque
import urllib.request

from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "uaap" / "teams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; IMG-Sports-AssetBot/1.0; +https://imgofficial.com)"
TEAM_LOGOS = {
    "adamson": "https://uaap.org/images/logos/adu.png",
    "ateneo": "https://uaap.org/images/logos/ateneo.png",
    "dlsu": "https://uaap.org/images/logos/dlsu.png",
    "feu": "https://uaap.org/images/logos/feu.png",
    "nu": "https://uaap.org/images/logos/nu.png",
    "ue": "https://uaap.org/images/logos/ue.png",
    "up": "https://uaap.org/images/logos/up.png",
    "ust": "https://uaap.org/images/logos/ust.png",
}

CANVAS = 512
PADDING = 30

def fetch_image(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://uaap.org/about/university",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(BytesIO(r.read())).convert("RGBA")

def near_white(px):
    r,g,b,a = px
    return a > 0 and r >= 242 and g >= 242 and b >= 242 and max(r,g,b)-min(r,g,b) <= 12

def remove_connected_white_background(im):
    """Only remove near-white pixels connected to an image edge.
    Internal white areas in the logo remain untouched.
    """
    if im.width < 2 or im.height < 2:
        return im
    px = im.load()
    q = deque()
    seen = set()
    for x in range(im.width):
        for y in (0, im.height-1):
            if near_white(px[x,y]):
                q.append((x,y)); seen.add((x,y))
    for y in range(im.height):
        for x in (0, im.width-1):
            if near_white(px[x,y]) and (x,y) not in seen:
                q.append((x,y)); seen.add((x,y))

    while q:
        x,y = q.popleft()
        r,g,b,a = px[x,y]
        px[x,y] = (r,g,b,0)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < im.width and 0 <= ny < im.height and (nx,ny) not in seen and near_white(px[nx,ny]):
                seen.add((nx,ny)); q.append((nx,ny))
    return im

def trim_alpha(im):
    alpha = im.getchannel("A")
    box = alpha.getbbox()
    return im.crop(box) if box else im

def enhance_logo(im):
    im = remove_connected_white_background(im)
    im = trim_alpha(im)

    target = CANVAS - PADDING * 2
    scale = min(target / max(1, im.width), target / max(1, im.height))
    new_size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    im = im.resize(new_size, Image.Resampling.LANCZOS)

    rgb = Image.new("RGB", im.size, "white")
    rgb.paste(im.convert("RGB"), mask=im.getchannel("A"))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.035)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=105, threshold=2))
    sharpened = Image.merge("RGBA", (*rgb.split(), im.getchannel("A")))

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0,0,0,0))
    x = (CANVAS - sharpened.width)//2
    y = (CANVAS - sharpened.height)//2
    canvas.alpha_composite(sharpened, (x,y))
    return canvas

for slug, url in TEAM_LOGOS.items():
    img = fetch_image(url)
    original = img.size
    out = enhance_logo(img)
    target = OUT_DIR / f"{slug}.png"
    out.save(target, "PNG", optimize=True)
    print(f"{slug}: {original[0]}x{original[1]} -> {CANVAS}x{CANVAS} {target.stat().st_size} bytes")
