from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "uaap" / "uaap-hero.webp"
OUT = ROOT / "assets" / "uaap" / "uaap-hero-hq.webp"

TARGET = (2560, 1440)

def center_crop_16_9(im):
    w, h = im.size
    target_ratio = 16 / 9
    ratio = w / h
    if abs(ratio - target_ratio) < 0.002:
        return im
    if ratio > target_ratio:
        new_w = int(round(h * target_ratio))
        left = max(0, (w - new_w) // 2)
        return im.crop((left, 0, left + new_w, h))
    new_h = int(round(w / target_ratio))
    top = max(0, (h - new_h) // 2)
    return im.crop((0, top, w, top + new_h))

if not SRC.exists():
    raise SystemExit(f"Missing source: {SRC}")

im = Image.open(SRC).convert("RGB")
source_size = im.size
im = center_crop_16_9(im)

# High-quality two-pass resampling reduces blockiness while retaining crisp logo edges.
mid = (max(im.width, 1920), max(im.height, 1080))
if im.size != mid:
    im = im.resize(mid, Image.Resampling.LANCZOS)
im = im.filter(ImageFilter.GaussianBlur(radius=0.18))
im = im.resize(TARGET, Image.Resampling.LANCZOS)
im = ImageEnhance.Contrast(im).enhance(1.035)
im = ImageEnhance.Sharpness(im).enhance(1.18)
im = im.filter(ImageFilter.UnsharpMask(radius=1.25, percent=165, threshold=2))

OUT.parent.mkdir(parents=True, exist_ok=True)
im.save(OUT, "WEBP", quality=91, method=6)

print(f"UAAP hero HQ: {source_size[0]}x{source_size[1]} -> {TARGET[0]}x{TARGET[1]}")
print(f"Output: {OUT} ({OUT.stat().st_size} bytes)")
