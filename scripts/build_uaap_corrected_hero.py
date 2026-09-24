from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "uaap" / "uaap-hero-hq-v7.jpg"
OUT = ROOT / "assets" / "uaap" / "uaap-hero-corrected-v10.jpg"
TEAM_DIR = ROOT / "assets" / "uaap" / "teams"

TEAMS = [
    # slug, x fraction, y fraction, badge px, plate color
    ("adamson", 0.073, 0.515, 200, (8, 45, 98)),
    ("dlsu",    0.184, 0.505, 205, (8, 74, 45)),
    ("up",      0.286, 0.500, 205, (100, 20, 35)),
    ("ust",     0.660, 0.515, 205, (126, 90, 12)),
    ("feu",     0.730, 0.515, 200, (13, 76, 47)),
    ("nu",      0.810, 0.525, 200, (22, 49, 95)),
    ("ue",      0.879, 0.525, 190, (118, 17, 24)),
    ("ateneo",  0.953, 0.515, 185, (18, 65, 126)),
]

def fit_rgba(img, box):
    img = img.convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)
    scale = min(box / max(1, img.width), box / max(1, img.height))
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(size, Image.Resampling.LANCZOS)

def add_badge(base, slug, xf, yf, badge, color):
    path = TEAM_DIR / f"{slug}.png"
    if not path.exists():
        raise FileNotFoundError(path)

    logo = fit_rgba(Image.open(path), int(badge * 0.80))
    cx, cy = round(base.width * xf), round(base.height * yf)
    plate = int(badge * 1.03)

    # Local masking plate covers the baked-in stylized mark without altering the banner.
    layer = Image.new("RGBA", base.size, (0,0,0,0))
    draw = ImageDraw.Draw(layer)
    r = plate // 2
    shadow_box = (cx-r+5, cy-r+10, cx+r+5, cy+r+10)
    draw.ellipse(shadow_box, fill=(0,0,0,120))
    plate_box = (cx-r, cy-r, cx+r, cy+r)
    draw.ellipse(plate_box, fill=(*color, 222), outline=(255,255,255,72), width=max(2, badge//70))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(1, badge//80)))
    base.alpha_composite(layer)

    # Crisp logo over the masked original.
    shadow = Image.new("RGBA", base.size, (0,0,0,0))
    sx = cx - logo.width//2 + 5
    sy = cy - logo.height//2 + 8
    black = Image.new("RGBA", logo.size, (0,0,0,210))
    black.putalpha(logo.getchannel("A").filter(ImageFilter.GaussianBlur(5)))
    shadow.alpha_composite(black, (sx, sy))
    base.alpha_composite(shadow)

    x = cx - logo.width//2
    y = cy - logo.height//2
    base.alpha_composite(logo, (x, y))

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    base = Image.open(SOURCE).convert("RGBA")
    if base.width < 2000 or base.height < 1000:
        print(f"Refusing low-resolution source: {base.size}", file=sys.stderr)
        raise SystemExit(2)

    for args in TEAMS:
        add_badge(base, *args)

    rgb = Image.new("RGB", base.size, "black")
    rgb.paste(base.convert("RGB"))
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.55, percent=70, threshold=3))
    rgb.save(OUT, "JPEG", quality=94, subsampling=0, optimize=True, progressive=True)

    print(f"Built {OUT.relative_to(ROOT)} {rgb.width}x{rgb.height} {OUT.stat().st_size} bytes")

if __name__ == "__main__":
    main()
