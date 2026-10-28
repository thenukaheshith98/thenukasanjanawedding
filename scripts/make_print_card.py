import ssl
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PRINT = ROOT / "print"
FONTS = PRINT / "fonts"
OUT_PDF = PRINT / "Sanjana-Thenuka-Invitation-Card.pdf"

# A5 at 300 dpi
W, H = 1748, 2480
IVORY = (245, 237, 220)
IVORY_SOFT = (251, 245, 230)
GOLD = (210, 185, 122)
GOLD_MID = (184, 154, 71)
GOLD_DEEP = (142, 116, 39)
MAROON = (92, 20, 15)
BRONZE = (71, 60, 31)
TAUPE = (124, 106, 72)
ONLINE = "https://thenukaheshith98.github.io/thenukasanjanawedding/"

FONT_URLS = {
    "PlayfairDisplay-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
    "EBGaramond.ttf": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf",
    "CormorantGaramond-Italic.ttf": "https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "AbhayaLibre-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/abhayalibre/AbhayaLibre-Bold.ttf",
}

def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.check_call(
            ["curl.exe", "-k", "-L", "--fail", "-o", str(dest), url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        ctx = ssl._create_unverified_context()
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 invitation-card"})
        with urlopen(req, timeout=60, context=ctx) as res:
            dest.write_bytes(res.read())
    print("downloaded", dest.name, dest.stat().st_size)


def freeze_font(src: Path, dest: Path, weight: int) -> None:
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    font_file = TTFont(src)
    instantiateVariableFont(font_file, {"wght": weight}, inplace=True)
    font_file.save(dest)
    print("froze", dest.name)


def ensure_fonts() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    for name, url in FONT_URLS.items():
        path = FONTS / name
        if not path.exists() or path.stat().st_size < 10000:
            download(url, path)
    if not (FONTS / "Playfair-600.ttf").exists():
        freeze_font(FONTS / "PlayfairDisplay-SemiBold.ttf", FONTS / "Playfair-600.ttf", 600)
    if not (FONTS / "EBGaramond-500.ttf").exists():
        freeze_font(FONTS / "EBGaramond.ttf", FONTS / "EBGaramond-500.ttf", 500)
    if not (FONTS / "EBGaramond-600.ttf").exists():
        freeze_font(FONTS / "EBGaramond.ttf", FONTS / "EBGaramond-600.ttf", 600)
    italic = FONTS / "Cormorant-Italic.ttf"
    if not italic.exists() or italic.stat().st_size < 8000:
        download(
            "https://cdn.jsdelivr.net/fontsource/fonts/cormorant-garamond@5.2.8/latin-500-italic.ttf",
            italic,
        )


FILES = {
    "playfair": "Playfair-600.ttf",
    "body": "EBGaramond-500.ttf",
    "label": "EBGaramond-600.ttf",
    "italic": "Cormorant-Italic.ttf",
    "sinhala": "AbhayaLibre-Bold.ttf",
}

FALLBACK_FILES = {
    "playfair": Path(r"C:\Windows\Fonts\GARABD.TTF"),
    "body": Path(r"C:\Windows\Fonts\GARA.TTF"),
    "label": Path(r"C:\Windows\Fonts\GARABD.TTF"),
    "italic": Path(r"C:\Windows\Fonts\GARAIT.TTF"),
    "sinhala": Path(r"C:\Windows\Fonts\iskpotab.ttf"),
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / FILES[name]
    if not path.exists() or path.stat().st_size < 8000:
        path = FALLBACK_FILES[name]
    return ImageFont.truetype(str(path), size)


def ivory_canvas() -> Image.Image:
    img = Image.new("RGB", (W, H), IVORY_SOFT)
    wash = Image.new("RGB", (W, H), (242, 230, 201))
    mask = Image.linear_gradient("L").resize((1, H)).resize((W, H))
    img = Image.composite(wash, img, mask)
    backdrop = ASSETS / "backdrop.webp"
    if backdrop.exists():
        tex = Image.open(backdrop).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        tex = ImageEnhance.Color(tex).enhance(0.35)
        tex = ImageEnhance.Brightness(tex).enhance(1.18)
        img = Image.blend(img, tex, 0.22)
    return img


def draw_frame(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((36, 36, W - 36, H - 36), radius=28, outline=GOLD, width=4)
    draw.rounded_rectangle((58, 58, W - 58, H - 58), radius=18, outline=(*GOLD_MID, 255), width=2)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, fnt: ImageFont.FreeTypeFont, fill) -> int:
    tw = text_width(draw, text, fnt)
    draw.text(((W - tw) / 2, y), text, font=fnt, fill=fill)
    box = draw.textbbox((0, 0), text, font=fnt)
    return y + (box[3] - box[1])


def tracked(draw: ImageDraw.ImageDraw, text: str, y: int, fnt: ImageFont.FreeTypeFont, fill, tracking=8) -> int:
    widths = []
    for ch in text:
        widths.append(text_width(draw, ch, fnt) if ch != " " else max(10, int(fnt.size * 0.38)))
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = (W - total) / 2
    for ch, cw in zip(text, widths):
        if ch != " ":
            draw.text((x, y), ch, font=fnt, fill=fill)
        x += cw + tracking
    box = draw.textbbox((0, 0), "Hg", font=fnt)
    return y + (box[3] - box[1])


def ornament(draw: ImageDraw.ImageDraw, y: int) -> int:
    cx, left, right = W / 2, 420, W - 420
    draw.line((left, y, cx - 22, y), fill=GOLD_MID, width=2)
    draw.line((cx + 22, y, right, y), fill=GOLD_MID, width=2)
    draw.regular_polygon((cx, y, 9), n_sides=4, rotation=45, fill=GOLD_DEEP)
    return y + 28


def paste_photo(card: Image.Image, box: tuple[int, int, int, int]) -> None:
    photo = Image.open(ASSETS / "couple-hero.webp").convert("RGB")
    x0, y0, x1, y1 = box
    tw, th = x1 - x0, y1 - y0
    fitted = Image.new("RGB", (tw, th), IVORY)
    scale = max(tw / photo.width, th / photo.height)
    nw, nh = int(photo.width * scale), int(photo.height * scale)
    photo = photo.resize((nw, nh), Image.Resampling.LANCZOS)
    fitted.paste(photo, ((tw - nw) // 2, (th - nh) // 6))
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, tw - 1, th - 1), radius=28, fill=255)
    card.paste(fitted, (x0, y0), mask)
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(box, radius=28, outline=GOLD_MID, width=2)


def make_qr() -> Image.Image:
    dest = PRINT / "qr-online.png"
    if not dest.exists():
        url = (
            "https://api.qrserver.com/v1/create-qr-code/?size=440x440&margin=8"
            "&color=5c140f&bgcolor=fbf5e6&data=" + ONLINE
        )
        download(url, dest)
    return Image.open(dest).convert("RGB").resize((220, 220), Image.Resampling.NEAREST)


def front() -> Image.Image:
    card = ivory_canvas()
    draw = ImageDraw.Draw(card)
    draw_frame(draw)

    y = centered(draw, "ශ්‍රී සුභ මංගලම්", 118, font("sinhala", 56), MAROON)
    y = tracked(draw, "YOU ARE INVITED TO THE WEDDING OF", y + 34, font("label", 20), GOLD_DEEP, 7)
    y = ornament(draw, y + 38)

    name_f = font("playfair", 84)
    amp_f = font("italic", 52)
    san, thu, amp = "Sanjana", "Thenuka", "  &  "
    total = text_width(draw, san, name_f) + text_width(draw, amp, amp_f) + text_width(draw, thu, name_f)
    x = (W - total) / 2
    draw.text((x, y + 8), san, font=name_f, fill=MAROON)
    x += text_width(draw, san, name_f)
    draw.text((x, y + 26), amp, font=amp_f, fill=GOLD_DEEP)
    x += text_width(draw, amp, amp_f)
    draw.text((x, y + 8), thu, font=name_f, fill=MAROON)
    y += 118

    def parent_col(cx: float, label: str, names: str, top: int) -> None:
        lf, pf = font("label", 17), font("body", 26)
        lw, nw = text_width(draw, label, lf), text_width(draw, names, pf)
        draw.text((cx - lw / 2, top), label, font=lf, fill=GOLD_DEEP)
        draw.text((cx - nw / 2, top + 34), names, font=pf, fill=BRONZE)

    col_y = y + 16
    parent_col(W * 0.32, "DAUGHTER OF", "Mr. & Mrs. Kaluarachchi", col_y)
    parent_col(W * 0.68, "SON OF", "Mr. & Mrs. Weeratunga", col_y)
    y = col_y + 92

    num_f, side_f = font("playfair", 74), font("label", 22)
    num_w = text_width(draw, "3", num_f)
    cx = W / 2
    draw.text((cx - num_w / 2, y), "3", font=num_f, fill=MAROON)
    for label, side in (("DECEMBER", -1), ("2026", 1)):
        lw = text_width(draw, label, side_f)
        mid = cx + side * 320
        draw.text((mid - lw / 2, y + 22), label, font=side_f, fill=GOLD_DEEP)
        draw.line((mid - 150, y + 40, mid - lw / 2 - 16, y + 40), fill=GOLD_MID, width=2)
        draw.line((mid + lw / 2 + 16, y + 40, mid + 150, y + 40), fill=GOLD_MID, width=2)
    y += 108
    centered(draw, "Thursday, 3rd December 2026", y, font("italic", 30), BRONZE)

    paste_photo(card, (300, y + 64, W - 300, 2135))
    draw = ImageDraw.Draw(card)
    tracked(draw, "PARADISE IN BOLGODA", 2205, font("label", 24), MAROON, 8)
    return card


def event_row(draw: ImageDraw.ImageDraw, y: int, title: str, time: str) -> int:
    draw.rounded_rectangle((240, y, W - 240, y + 148), radius=18, outline=GOLD_MID, width=2)
    title_f, meta_f = font("playfair", 30), font("body", 26)
    draw.text((300, y + 30), title, font=title_f, fill=MAROON)
    draw.text((300, y + 82), time + "   ·   Paradise in Bolgoda", font=meta_f, fill=BRONZE)
    return y + 176


def back() -> Image.Image:
    card = ivory_canvas()
    draw = ImageDraw.Draw(card)
    draw_frame(draw)

    y = tracked(draw, "KINDLY JOIN US", 150, font("label", 20), GOLD_DEEP, 8)
    y = centered(draw, "Together Forever", y + 20, font("playfair", 56), MAROON)
    y = ornament(draw, y + 28)
    invite = (
        "We are delighted to invite you to celebrate\n"
        "the beginning of our forever as we exchange vows\n"
        "surrounded by our loved ones."
    )
    body = font("body", 28)
    for line in invite.split("\n"):
        y = centered(draw, line, y + 8, body, BRONZE) + 8

    y = tracked(draw, "OUR DAY", y + 48, font("label", 20), GOLD_DEEP, 10)
    y = event_row(draw, y + 24, "Ring Ceremony", "10.45 AM")
    y = event_row(draw, y, "Registration", "11.00 AM")

    y += 20
    y = tracked(draw, "VENUE", y, font("label", 20), GOLD_DEEP, 10)
    y = centered(draw, "Paradise in Bolgoda", y + 16, font("playfair", 36), MAROON)
    y = centered(
        draw,
        "67 Meegahawatte Rd, Piliyandala 10300, Sri Lanka",
        y + 16,
        font("body", 26),
        BRONZE,
    )

    y += 48
    y = tracked(draw, "KINDLY REPLY", y, font("label", 20), GOLD_DEEP, 8)
    y = centered(draw, "Please respond by 15th November 2026", y + 14, font("body", 28), BRONZE)

    qr = make_qr()
    qx = (W - qr.width) // 2
    qy = y + 40
    card.paste(qr, (qx, qy))
    draw = ImageDraw.Draw(card)
    centered(draw, "Scan for the online invitation", qy + qr.height + 16, font("body", 22), TAUPE)
    centered(draw, "Sanjana  &  Thenuka", 2260, font("italic", 32), MAROON)
    return card


def main() -> None:
    PRINT.mkdir(parents=True, exist_ok=True)
    ensure_fonts()
    pages = [front().convert("RGB"), back().convert("RGB")]
    pages[0].save(PRINT / "preview-front.png")
    pages[1].save(PRINT / "preview-back.png")
    pages[0].save(
        OUT_PDF,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=pages[1:],
    )
    print("wrote", OUT_PDF, OUT_PDF.stat().st_size)


if __name__ == "__main__":
    main()
