from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter
from rembg import new_session, remove

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SRC = ASSETS / "couple-walk-src.png"
OUT = ASSETS / "couple-hero.webp"
IVORY = (245, 237, 220)
IVORY_WARM = (251, 245, 230)
GOLD_WASH = (242, 230, 201)
TARGET_RATIO = 3 / 4
OUT_W = 1200


def ivory_backdrop(size: tuple[int, int]) -> Image.Image:
    w, h = size
    bg = Image.new("RGB", size, IVORY_WARM)
    wash = Image.new("RGB", size, GOLD_WASH)
    mask = Image.linear_gradient("L").resize((1, h)).resize(size)
    return Image.composite(wash, bg, mask)


def rembg_cutout(src: Image.Image) -> Image.Image:
    buf = BytesIO()
    src.convert("RGB").save(buf, "PNG")
    session = new_session("u2net")
    return Image.open(BytesIO(remove(buf.getvalue(), session=session))).convert("RGBA")


def clean_mask(cut: Image.Image, rgb: Image.Image) -> Image.Image:
    alpha = cut.getchannel("A")
    solid = alpha.point(lambda p: 255 if p > 40 else 0)
    green_mask = Image.new("L", rgb.size, 0)
    src_px = rgb.load()
    out_px = green_mask.load()
    w, h = rgb.size
    for y in range(h):
        for x in range(w):
            pr, pg, pb = src_px[x, y]
            if pg > pr + 14 and pg > pb + 8 and pg > 90:
                out_px[x, y] = 255
    fringe = green_mask.filter(ImageFilter.MaxFilter(5))
    kept = ImageChops.subtract(solid, fringe)
    kept = kept.filter(ImageFilter.MinFilter(3))
    kept = kept.filter(ImageFilter.MaxFilter(3))
    kept = kept.filter(ImageFilter.GaussianBlur(radius=1.1))
    return kept


def grade_subject(rgb: Image.Image, mask: Image.Image) -> Image.Image:
    graded = ImageEnhance.Color(rgb.convert("RGB")).enhance(0.98)
    graded = ImageEnhance.Contrast(graded).enhance(0.99)
    graded = Image.blend(graded, Image.new("RGB", graded.size, IVORY), 0.05)
    out = graded.convert("RGBA")
    out.putalpha(mask)
    return out


def crop_to_ratio(im: Image.Image, mask: Image.Image) -> Image.Image:
    bbox = mask.point(lambda p: 255 if p > 16 else 0).getbbox()
    if not bbox:
        return im

    left, top, right, bottom = bbox
    pad_x = int((right - left) * 0.08)
    pad_top = int((bottom - top) * 0.06)
    pad_bot = int((bottom - top) * 0.04)
    left = max(0, left - pad_x)
    top = max(0, top - pad_top)
    right = min(im.width, right + pad_x)
    bottom = min(im.height, bottom + pad_bot)

    box_w = right - left
    box_h = bottom - top
    if box_w / box_h > TARGET_RATIO:
        new_h = int(box_w / TARGET_RATIO)
        extra = new_h - box_h
        top = max(0, top - extra // 3)
        bottom = min(im.height, top + new_h)
        top = max(0, bottom - new_h)
    else:
        new_w = int(box_h * TARGET_RATIO)
        extra = new_w - box_w
        left = max(0, left - extra // 2)
        right = min(im.width, left + new_w)
        left = max(0, right - new_w)

    cropped = im.crop((left, top, right, bottom))
    tw = OUT_W
    th = int(tw / TARGET_RATIO)
    canvas = ivory_backdrop((tw, th)).convert("RGBA")
    fitted = cropped.resize((tw, th), Image.Resampling.LANCZOS)
    return Image.alpha_composite(canvas, fitted.convert("RGBA"))


def fade_hem(im: Image.Image) -> Image.Image:
    w, h = im.size
    fade = Image.linear_gradient("L").resize((1, h)).resize((w, h))
    fade = fade.point(lambda p: 255 if p < 214 else max(0, int(255 - (p - 214) * 6.2)))
    return Image.composite(im.convert("RGB"), ivory_backdrop((w, h)), fade)


def main() -> None:
    src = Image.open(SRC).convert("RGB")
    print("source", src.size)
    cut = rembg_cutout(src)
    mask = clean_mask(cut, src)
    subject = grade_subject(src, mask)
    composed = Image.alpha_composite(ivory_backdrop(src.size).convert("RGBA"), subject)
    framed = crop_to_ratio(composed, mask)
    out = fade_hem(framed)
    out.convert("RGB").save(OUT, "WEBP", quality=90, method=6)
    print(f"wrote {OUT.name} {OUT.stat().st_size} bytes {out.size}")


if __name__ == "__main__":
    main()
