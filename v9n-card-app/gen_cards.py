#!/usr/bin/env python3
"""Render the four v9n-card screens (390x450) into assets/common.s/.

card0: v9n consulting logo card (navy business-card gradient)
card1: QR -> https://v9n.us
card2: QR -> https://trick.vanstaveren.us
card3: QR -> vCard (name, cell, org, url) so people can save + text
"""
import os
import sys

import qrcode
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gen_assets import _sans_img, V9N_SANS, V9N_INK, V9N_GRAY  # noqa: E402

W, H = 390, 450
OUT = os.path.join(os.path.dirname(__file__), "assets", "common.s")
NAVY1, NAVY2 = (44, 62, 80), (52, 73, 94)
ACCENT = (93, 173, 226)
LOGO_BLUE = (169, 199, 224)

VCARD = "\r\n".join([
    "BEGIN:VCARD",
    "VERSION:3.0",
    # N is required for iOS to show a person's name; FN alone gets ignored
    # and the contact card falls back to ORG.
    "N:van Staveren;Patrick;;;",
    "FN:Patrick van Staveren",
    "ORG:v9n consulting",
    "TEL;TYPE=CELL:+13124690036",
    "URL:https://v9n.us",
    "END:VCARD",
])

CARDS = [
    ("card1.png", "https://v9n.us", "v9n.us"),
    ("card2.png", "https://trick.vanstaveren.us", "trick.vanstaveren.us"),
    ("card3.png", VCARD, "save my number"),
]


def navy_gradient(w, h):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = (x / (w - 1) + 0.5) / 1.5  # lean diagonal-ish
        c = tuple(int(a + (b - a) * min(1, t)) for a, b in zip(NAVY1, NAVY2))
        d.rectangle([x, 0, x, h], fill=c + (255,))
    return img


def dots(img, active, color, y=None):
    d = ImageDraw.Draw(img)
    y = y if y is not None else H - 26
    total = 4
    for i in range(total):
        x = W // 2 + (i - (total - 1) / 2) * 26
        r = 5 if i == active else 3
        fill = color + (255,) if i == active else tuple(
            int(c * 0.55) for c in color) + (255,)
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def make_logo_card():
    img = navy_gradient(W, H)
    wm1 = _sans_img("v9n", 56, (255, 255, 255))
    wm2 = _sans_img("consulting", 56, LOGO_BLUE, V9N_SANS)
    total_h = wm1.height + 6 + wm2.height
    y0 = (H - total_h) // 2 - 20
    img.alpha_composite(wm1, ((W - wm1.width) // 2, y0))
    img.alpha_composite(wm2, ((W - wm2.width) // 2, y0 + wm1.height + 6))
    # accent rule under the wordmark, fading to the right like v9n.us
    d = ImageDraw.Draw(img)
    ry = y0 + total_h + 24
    for x in range(60, W - 60):
        t = (x - 60) / (W - 120)
        a = 1.0 - 1.2 * t if t <= 0.5 else 0.4 * (1 - (t - 0.5) * 2)
        base = img.getpixel((x, ry))[:3]
        c = tuple(int(n + (acc - n) * max(0, a)) for n, acc in zip(base, ACCENT))
        d.rectangle([x, ry, x, ry + 2], fill=c + (255,))
    hint = _sans_img("swipe right for QR codes", 22, LOGO_BLUE, V9N_SANS)
    img.alpha_composite(hint, ((W - hint.width) // 2, H - 72))
    dots(img, 0, LOGO_BLUE)
    img.convert("RGB").save(os.path.join(OUT, "card0.png"))


def make_qr_card(path, data, caption, index):
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       border=0)
    qr.add_data(data)
    qr.make(fit=True)
    n = qr.modules_count
    box = max(2, 310 // n)
    size = n * box
    q = qr.make_image(fill_color="black", back_color="white").resize(
        (size, size), Image.NEAREST)
    img.paste(q, ((W - size) // 2, 54))
    cap = _sans_img(caption, 26, V9N_INK)
    img.alpha_composite(cap, ((W - cap.width) // 2, 54 + size + 18))
    dots(img, index, V9N_GRAY)
    img.convert("RGB").save(os.path.join(OUT, path))
    print(f"{path}: {n}x{n} modules at {box}px -> {size}px  ({caption})")


def make_icon():
    img = navy_gradient(192, 192)
    wm = _sans_img("v9n", 64, (255, 255, 255))
    img.alpha_composite(wm, ((192 - wm.width) // 2, (192 - wm.height) // 2))
    img.save(os.path.join(OUT, "icon.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_logo_card()
    for i, (path, data, caption) in enumerate(CARDS, start=1):
        make_qr_card(path, data, caption, i)
    make_icon()
    print("cards written to", OUT)
