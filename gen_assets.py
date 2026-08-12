#!/usr/bin/env python3
"""Generate all image assets for the bip6-face watchface.

Digits/labels are rendered in the classic X11 `misc-fixed` 10x20 bitmap font
(from xfonts-base), nearest-neighbor upscaled so every pixel stays a crisp
block — early-xterm style.

Produces, under assets/bip6/:
  background.png          390x450 glxgears-inspired background (red/green/blue gears)
  icon.png                192x192 app icon (red gear)
  preview.png             390x450 preview with sample data baked in
  time/0.png..9.png       big white digits for HH:MM (scale 5)
  time/colon.png          colon separator
  date/0.png..9.png       white digits for MM/DD (scale 2)
  date/slash.png          '/' separator
  week/0.png..6.png       MON..SUN day abbreviations (scale 2)
  steps/0.png..9.png      red digits (scale 2)
  batt/0.png..9.png       green digits (scale 2; green, not blue, so they
                          don't blend into the blue gear behind them)
  batt/percent.png        green '%' unit
  label_steps.png         'STEPS' label
  label_batt.png          'BATTERY' label
  moon/0.png..28.png      36px moon-phase discs for IMG_LEVEL (data_type.MOON
                          reports lunar day 0..28; 0 = new, ~14 = full)
"""
import gzip
import math
import os
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 390, 450
SS = 4  # supersampling factor for antialiased gears
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "bip6")

PCF_GZ = "/usr/share/fonts/X11/misc/10x20-ISO8859-1.pcf.gz"
CELL_W, CELL_H = 10, 20  # misc-fixed 10x20 glyph cell
PAD = 1                  # native padding for the 1px outline

RED = (215, 60, 50)
GREEN = (60, 190, 80)
BLUE = (70, 110, 230)
WHITE = (255, 255, 255)
GRAY = (190, 190, 190)

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

_font = None


def pixel_font():
    global _font
    if _font is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".pcf", delete=False)
        with gzip.open(PCF_GZ, "rb") as f:
            shutil.copyfileobj(f, tmp)
        tmp.close()
        _font = ImageFont.truetype(tmp.name, CELL_H)
    return _font


def pixel_text(text, scale, color, out_path, crop_w=False):
    """Render text in misc-fixed at native size with a 1px black outline,
    then upscale with NEAREST for chunky pixels. crop_w trims empty columns
    (used for the skinny colon)."""
    font = pixel_font()
    nw, nh = CELL_W * len(text) + 2 * PAD, CELL_H + 2 * PAD
    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).text((PAD, PAD), text, font=font, fill=255)
    img = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    black = Image.new("RGBA", (nw, nh), (0, 0, 0, 255))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                img.paste(black, (dx, dy), mask)
    img.paste(Image.new("RGBA", (nw, nh), color + (255,)), (0, 0), mask)
    if crop_w:
        bbox = img.getbbox()
        img = img.crop((max(0, bbox[0] - 1), 0, min(nw, bbox[2] + 1), nh))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(out_path)
    return img.size


def dim(color, f):
    return tuple(int(c * f) for c in color)


def gear_layer(size, cx, cy, outer_r, teeth, color, hole_r, angle_offset=0.0):
    """Draw one flat gear (glxgears style: toothed ring with a big hole) on a new RGBA layer."""
    layer = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy, outer_r, hole_r = cx * SS, cy * SS, outer_r * SS, hole_r * SS
    root_r = outer_r * 0.82
    pts = []
    step = 2 * math.pi / teeth
    # each tooth: rise on outer radius for ~40% of the pitch, valley on root radius
    for i in range(teeth):
        a0 = angle_offset + i * step
        for frac, r in ((0.00, root_r), (0.12, outer_r), (0.38, outer_r), (0.50, root_r)):
            a = a0 + frac * step
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=color + (255,))
    # punch the center hole (raw pixel write, no blending -> true transparency)
    d.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r], fill=(0, 0, 0, 0))
    # subtle inner rim shading for a hint of depth
    rim = hole_r * 1.18
    d.ellipse([cx - rim, cy - rim, cx + rim, cy + rim], outline=dim(color, 0.55) + (255,), width=SS * 3)
    return layer.resize(size, Image.LANCZOS)


def make_background():
    bg = Image.new("RGBA", (W, H), (10, 10, 14, 255))
    # gears dimmed so the white time digits stay readable on top
    f = 0.62
    for args in (
        # big red gear, upper left, partly off-screen
        dict(cx=105, cy=140, outer_r=150, teeth=14, color=dim(RED, f), hole_r=62, angle_offset=0.1),
        # green gear meshing to its right
        dict(cx=320, cy=230, outer_r=105, teeth=10, color=dim(GREEN, f), hole_r=44, angle_offset=0.35),
        # small blue gear, lower left
        dict(cx=95, cy=375, outer_r=90, teeth=10, color=dim(BLUE, f), hole_r=38, angle_offset=0.55),
    ):
        bg.alpha_composite(gear_layer((W, H), **args))
    # darken overall with a soft vertical vignette so foreground text pops
    shade = Image.new("L", (1, H))
    for y in range(H):
        # slightly darker mid-band where the time sits
        shade.putpixel((0, y), int(70 * math.exp(-((y - 160) / 140.0) ** 2)))
    shade = shade.resize((W, H))
    bg = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), bg, shade.point(lambda v: v))
    bg.convert("RGB").save(os.path.join(OUT, "background.png"))
    return bg


def make_fonts():
    for sub in ("time", "date", "week", "steps", "batt"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for i in range(10):
        pixel_text(str(i), 5, WHITE, os.path.join(OUT, "time", f"{i}.png"))
        pixel_text(str(i), 2, WHITE, os.path.join(OUT, "date", f"{i}.png"))
        pixel_text(str(i), 2, RED, os.path.join(OUT, "steps", f"{i}.png"))
        pixel_text(str(i), 2, GREEN, os.path.join(OUT, "batt", f"{i}.png"))
    pixel_text(":", 5, WHITE, os.path.join(OUT, "time", "colon.png"), crop_w=True)
    pixel_text("/", 2, WHITE, os.path.join(OUT, "date", "slash.png"))
    pixel_text("%", 2, GREEN, os.path.join(OUT, "batt", "percent.png"))
    for i, name in enumerate(WEEKDAYS):
        pixel_text(name, 2, WHITE, os.path.join(OUT, "week", f"{i}.png"))
    pixel_text("STEPS", 1, GRAY, os.path.join(OUT, "label_steps.png"))
    pixel_text("BATTERY", 1, GRAY, os.path.join(OUT, "label_batt.png"))


def make_moon():
    """29 moon-phase discs. Illumination from sphere-shading: sun direction
    rotates through the synodic cycle, lit side on the right while waxing
    (northern-hemisphere convention)."""
    os.makedirs(os.path.join(OUT, "moon"), exist_ok=True)
    size = 36
    n = size * SS
    r = n / 2 - SS  # leave a hair of margin
    cx = cy = n / 2
    LIT = (235, 230, 205)
    DARK = (45, 48, 60)
    for day in range(29):
        alpha = 2 * math.pi * day / 29.0  # 0 = new, pi = full
        sin_a, cos_a = math.sin(alpha), math.cos(alpha)
        img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        pix = img.load()
        for py in range(n):
            ny = (py - cy) / r
            for px_ in range(n):
                nx = (px_ - cx) / r
                d2 = nx * nx + ny * ny
                if d2 > 1.0:
                    continue
                z = math.sqrt(1.0 - d2)
                lit = nx * sin_a - z * cos_a > 0
                pix[px_, py] = (LIT if lit else DARK) + (255,)
        img = img.resize((size, size), Image.LANCZOS)
        img.save(os.path.join(OUT, "moon", f"{day}.png"))


def make_icon():
    size = (192, 192)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.alpha_composite(gear_layer(size, 96, 96, 88, 12, RED, 34))
    img.alpha_composite(gear_layer(size, 150, 150, 40, 8, dim(GREEN, 0.9), 15, 0.3))
    img.save(os.path.join(OUT, "icon.png"))


def make_preview(bg):
    """Preview with sample data baked in, mirroring the widget layout in index.js."""
    img = bg.copy()

    def paste(path, x, y):
        g = Image.open(os.path.join(OUT, path)).convert("RGBA")
        img.alpha_composite(g, (x, y))
        return g.width

    def paste_row(parts, y, gap=0):
        widths = [Image.open(os.path.join(OUT, p)).width for p in parts]
        x = (W - (sum(widths) + gap * (len(parts) - 1))) // 2
        for p in parts:
            x += paste(p, x, y) + gap

    # date row: FRI 08/08 (layout mirrors DATE_X/DATE_Y in index.js)
    x = DATE_X
    x += paste("week/4.png", x, DATE_Y) + DATE_GAP
    for p in ("date/0.png", "date/8.png", "date/slash.png", "date/0.png", "date/8.png"):
        x += paste(p, x, DATE_Y)
    paste_row(["time/1.png", "time/0.png", "time/colon.png", "time/0.png", "time/8.png"], TIME_Y)
    paste_row(["label_steps.png"], 252)
    paste_row(["steps/8.png", "steps/4.png", "steps/7.png", "steps/6.png"], 280)
    paste_row(["label_batt.png"], 344)
    paste_row(["batt/7.png", "batt/3.png", "batt/percent.png"], 372)
    paste("moon/18.png", MOON_X, MOON_Y)  # waning gibbous sample
    img.convert("RGB").save(os.path.join(OUT, "preview.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    bg = make_background()
    make_fonts()
    make_moon()
    make_icon()

    # moon disc right of the battery % — the top-right corner gets clipped
    # by the display's rounded physical corners. Battery digits row is
    # y=372 h=44, so 36px disc centers at +4.
    MOON_X, MOON_Y = 300, 376

    # layout constants shared with watchface/index.js — keep in sync
    digit_w = Image.open(os.path.join(OUT, "date", "0.png")).width       # 24
    slash_w = Image.open(os.path.join(OUT, "date", "slash.png")).width   # 24
    week_w = Image.open(os.path.join(OUT, "week", "0.png")).width        # 64
    DATE_GAP = 12
    date_total = week_w + DATE_GAP + 4 * digit_w + slash_w
    DATE_X = (W - date_total) // 2
    DATE_Y = 52
    time_w = 4 * Image.open(os.path.join(OUT, "time", "0.png")).width \
        + Image.open(os.path.join(OUT, "time", "colon.png")).width
    TIME_Y = 108

    make_preview(bg)
    print("assets written to", OUT)
    print(f"index.js constants: WEEK_X={DATE_X} DATE_Y={DATE_Y} "
          f"MONTH_X={DATE_X + week_w + DATE_GAP} TIME_X={(W - time_w) // 2} TIME_Y={TIME_Y} "
          f"(time digits {Image.open(os.path.join(OUT, 'time', '0.png')).width}w, "
          f"colon {Image.open(os.path.join(OUT, 'time', 'colon.png')).width}w, "
          f"labels {Image.open(os.path.join(OUT, 'label_steps.png')).width}x"
          f"{Image.open(os.path.join(OUT, 'label_steps.png')).height} / "
          f"{Image.open(os.path.join(OUT, 'label_batt.png')).width}x"
          f"{Image.open(os.path.join(OUT, 'label_batt.png')).height})")
