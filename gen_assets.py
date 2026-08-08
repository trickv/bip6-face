#!/usr/bin/env python3
"""Generate all image assets for the bip6-face watchface.

Produces, under assets/bip6/:
  background.png          390x450 glxgears-inspired background (red/green/blue gears)
  icon.png                192x192 app icon (red gear)
  preview.png             390x450 preview with sample data baked in
  time/0.png..9.png       large white digits for HH:MM
  time/colon.png          colon separator
  steps/0.png..9.png      small green digits
  batt/0.png..9.png       small blue digits
  batt/percent.png        blue '%' unit
  label_steps.png         'STEPS' label
  label_batt.png          'BATTERY' label
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 390, 450
SS = 4  # supersampling factor for antialiased gears
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "bip6")

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED = (215, 60, 50)
GREEN = (60, 190, 80)
BLUE = (70, 110, 230)


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


def glyph(ch, cell_w, cell_h, font_size, color, out_path):
    img = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, font_size)
    l, t, r, b = d.textbbox((0, 0), ch, font=font)
    x = (cell_w - (r - l)) // 2 - l
    y = (cell_h - (b - t)) // 2 - t
    d.text((x, y), ch, font=font, fill=color + (255,), stroke_width=2, stroke_fill=(0, 0, 0, 200))
    img.save(out_path)


def make_fonts():
    os.makedirs(os.path.join(OUT, "time"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "steps"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "batt"), exist_ok=True)
    for i in range(10):
        glyph(str(i), 60, 104, 92, (255, 255, 255), os.path.join(OUT, "time", f"{i}.png"))
        glyph(str(i), 26, 40, 34, GREEN, os.path.join(OUT, "steps", f"{i}.png"))
        glyph(str(i), 26, 40, 34, BLUE, os.path.join(OUT, "batt", f"{i}.png"))
    glyph(":", 26, 104, 92, (255, 255, 255), os.path.join(OUT, "time", "colon.png"))
    glyph("%", 34, 40, 34, BLUE, os.path.join(OUT, "batt", "percent.png"))


def make_label(text, color, out_path):
    font = ImageFont.truetype(FONT_PATH, 20)
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=font)
    img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - l, 4 - t), text, font=font, fill=color + (255,))
    img.save(out_path)


def make_icon():
    size = (192, 192)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.alpha_composite(gear_layer(size, 96, 96, 88, 12, RED, 34))
    img.alpha_composite(gear_layer(size, 150, 150, 40, 8, dim(GREEN, 0.9), 15, 0.3))
    img.save(os.path.join(OUT, "icon.png"))


def make_preview(bg):
    """Preview with sample data baked in, mirroring the widget layout in index.js."""
    img = bg.copy()

    def paste_row(parts, y, gap=0):
        total = sum(Image.open(p).width for p in parts) + gap * (len(parts) - 1)
        x = (W - total) // 2
        for p in parts:
            g = Image.open(p).convert("RGBA")
            img.alpha_composite(g, (x, y))
            x += g.width + gap
    t = os.path.join(OUT, "time")
    paste_row([f"{t}/1.png", f"{t}/0.png", f"{t}/colon.png", f"{t}/0.png", f"{t}/8.png"], 108)
    lbl = Image.open(os.path.join(OUT, "label_steps.png")).convert("RGBA")
    img.alpha_composite(lbl, ((W - lbl.width) // 2, 258))
    s = os.path.join(OUT, "steps")
    paste_row([f"{s}/8.png", f"{s}/4.png", f"{s}/7.png", f"{s}/6.png"], 286)
    lbl = Image.open(os.path.join(OUT, "label_batt.png")).convert("RGBA")
    img.alpha_composite(lbl, ((W - lbl.width) // 2, 344))
    b = os.path.join(OUT, "batt")
    paste_row([f"{b}/7.png", f"{b}/3.png", f"{b}/percent.png"], 372)
    img.convert("RGB").save(os.path.join(OUT, "preview.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    bg = make_background()
    make_fonts()
    make_label("STEPS", (170, 170, 170), os.path.join(OUT, "label_steps.png"))
    make_label("BATTERY", (170, 170, 170), os.path.join(OUT, "label_batt.png"))
    make_icon()
    make_preview(bg)
    print("assets written to", OUT)
