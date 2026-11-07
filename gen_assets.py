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
  date/0.png..9.png       white digits for MM/DD and the seconds hub (scale 2)
  gear.png                212px green gear, TIME_POINTER second-hand sprite:
                          one revolution per minute, white marker tooth
                          authored pointing up = start of minute
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


def _pixel_img(lines, scale, color, crop_w=False, line_step=None):
    """Render misc-fixed text (a string, or a list of lines) at native size
    with a 1px black outline, then upscale with NEAREST for chunky pixels.
    crop_w trims empty columns (skinny glyphs like the colon); line_step
    tightens multi-line leading (native px, default CELL_H)."""
    font = pixel_font()
    if isinstance(lines, str):
        lines = [lines]
    step = line_step or CELL_H
    nw = CELL_W * max(len(l) for l in lines) + 2 * PAD
    nh = (len(lines) - 1) * step + CELL_H + 2 * PAD
    mask = Image.new("L", (nw, nh), 0)
    d = ImageDraw.Draw(mask)
    for i, line in enumerate(lines):
        d.text((PAD, PAD + i * step), line, font=font, fill=255)
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
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def pixel_text(text, scale, color, out_path, crop_w=False):
    img = _pixel_img(text, scale, color, crop_w)
    img.save(out_path)
    return img.size


def dim(color, f):
    return tuple(int(c * f) for c in color)


def gear_layer(size, cx, cy, outer_r, teeth, color, hole_r, angle_offset=0.0,
               marker_color=None):
    """Draw one flat gear (glxgears style: toothed ring with a big hole) on a new RGBA layer.
    marker_color, if given, highlights tooth 0 as an index marker."""
    layer = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy, outer_r, hole_r = cx * SS, cy * SS, outer_r * SS, hole_r * SS
    root_r = outer_r * 0.82
    pts = []
    step = 2 * math.pi / teeth
    # each tooth: rise on outer radius for ~40% of the pitch, valley on root radius
    tooth_fracs = ((0.00, root_r), (0.12, outer_r), (0.38, outer_r), (0.50, root_r))
    for i in range(teeth):
        a0 = angle_offset + i * step
        for frac, r in tooth_fracs:
            a = a0 + frac * step
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=color + (255,))
    if marker_color:
        # repaint tooth 0 (flank-tip-flank quad, closed via a root-circle arc)
        quad = [(cx + r * math.cos(angle_offset + frac * step),
                 cy + r * math.sin(angle_offset + frac * step))
                for frac, r in tooth_fracs]
        d.polygon(quad, fill=marker_color + (255,))
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
        # (the green gear is a separate rotating sprite now — see make_gear)
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
    for sub in ("time", "time3", "date", "week", "steps", "batt", "secs"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    for i in range(10):
        pixel_text(str(i), 5, WHITE, os.path.join(OUT, "time", f"{i}.png"))
        pixel_text(str(i), 1, WHITE, os.path.join(OUT, "secs", f"{i}.png"))
        pixel_text(str(i), 3, WHITE, os.path.join(OUT, "time3", f"{i}.png"))
        pixel_text(str(i), 2, WHITE, os.path.join(OUT, "date", f"{i}.png"))
        pixel_text(str(i), 2, RED, os.path.join(OUT, "steps", f"{i}.png"))
        pixel_text(str(i), 2, GREEN, os.path.join(OUT, "batt", f"{i}.png"))
    pixel_text(":", 5, WHITE, os.path.join(OUT, "time", "colon.png"), crop_w=True)
    pixel_text(":", 3, WHITE, os.path.join(OUT, "time3", "colon.png"), crop_w=True)
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


GEAR_SIZE = 212           # sprite canvas, 2 * outer_r + 2
GEAR_CX, GEAR_CY = 320, 230  # on-screen rotation center (where the bg gear was)


def make_gear():
    """The green gear as a TIME_POINTER second-hand sprite: one full turn per
    minute. Authored with the white marker tooth pointing straight up, which
    is how pointer images are drawn at second 0."""
    c = GEAR_SIZE // 2
    teeth = 10
    step = 2 * math.pi / teeth
    # tooth 0's tip (fracs 0.12..0.38, center 0.25) points up (-pi/2)
    angle = -math.pi / 2 - 0.25 * step
    img = gear_layer((GEAR_SIZE, GEAR_SIZE), c, c, c - 1, teeth,
                     dim(GREEN, 0.62), 44, angle_offset=angle,
                     marker_color=(235, 235, 235))
    img.save(os.path.join(OUT, "gear.png"))


# ---- weekend faces ---------------------------------------------------------
# Saturday: xeyes. index.js moves the pupil sprites with setProperty on a
# timer: the left pupil orbits with the seconds (number riding inside it),
# the right pupil rolls toward gravity from the accelerometer.
EYE_L = (110, 195)
EYE_R = (280, 195)
EYE_RX, EYE_RY = 72, 95
PUPIL_R, PUPIL_ORBIT = 19, 38


def make_bg_sat():
    bg = Image.new("RGBA", (W, H), (10, 10, 14, 255))
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for cx, cy in (EYE_L, EYE_R):
        # gray rim so the eye edge reads against the black background
        d.ellipse([(cx - EYE_RX - 6) * SS, (cy - EYE_RY - 6) * SS,
                   (cx + EYE_RX + 6) * SS, (cy + EYE_RY + 6) * SS],
                  fill=(95, 95, 100, 255))
        d.ellipse([(cx - EYE_RX) * SS, (cy - EYE_RY) * SS,
                   (cx + EYE_RX) * SS, (cy + EYE_RY) * SS],
                  fill=(228, 228, 232, 255))
    bg.alpha_composite(layer.resize((W, H), Image.LANCZOS))
    bg.convert("RGB").save(os.path.join(OUT, "bg_sat.png"))
    return bg


def make_pupil_dot():
    """Plain pupil disc sprite; index.js places it by its top-left corner,
    so the center offset is half the sprite size."""
    pad = 2
    w = 2 * (PUPIL_R + pad)
    layer = Image.new("RGBA", (w * SS, w * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = (PUPIL_R + pad) * SS
    d.ellipse([c - PUPIL_R * SS, c - PUPIL_R * SS,
               c + PUPIL_R * SS, c + PUPIL_R * SS], fill=(22, 22, 28, 255))
    layer.resize((w, w), Image.LANCZOS).save(os.path.join(OUT, "pupil_dot.png"))
    return w // 2  # top-left -> center offset for index.js


# Sunday: cowsay, time in the speech bubble. Everything but the live digits
# is baked into bg_sun.png.
COW = [
    "\\   ^__^",
    " \\  (oo)\\______",
    "    (__)\\      )\\/\\",
    "        ||----w |",
    "        ||     ||",
]
TIME3_Y = 100
BOTTOM_Y = 398  # shared steps/battery row on both weekend faces


def make_bg_sun():
    bg = Image.new("RGBA", (W, H), (10, 10, 14, 255))
    dig3 = _pixel_img("0", 3, WHITE)
    dig2 = _pixel_img("0", 2, WHITE)
    c3 = _pixel_img(":", 3, WHITE, crop_w=True).width
    time3_w = 4 * dig3.width + c3
    # seconds tail inside the bubble: baked scale-2 colon + two live digits
    sec_colon = _pixel_img(":", 2, WHITE, crop_w=True)
    sec_w = 4 + sec_colon.width + 4 + 2 * dig2.width
    lt = _pixel_img("<", 3, WHITE)
    gt = _pixel_img(">", 3, WHITE)
    total = lt.width + 8 + time3_w + sec_w + 8 + gt.width
    bub_x = (W - total) // 2
    time3_x = bub_x + lt.width + 8
    sec2_y = TIME3_Y + dig3.height - dig2.height  # baseline-align with HH:MM
    colon_x = time3_x + time3_w + 4
    sec2_x = colon_x + sec_colon.width + 4
    bg.alpha_composite(lt, (bub_x, TIME3_Y))
    bg.alpha_composite(gt, (bub_x + lt.width + 8 + time3_w + sec_w + 8, TIME3_Y))
    bg.alpha_composite(sec_colon, (colon_x, sec2_y))
    border = _pixel_img("_" * 16, 2, WHITE)
    bg.alpha_composite(border, ((W - border.width) // 2, 54))
    dashes = _pixel_img("-" * 16, 2, WHITE)
    bg.alpha_composite(dashes, ((W - dashes.width) // 2, 156))
    cow = _pixel_img(COW, 2, GRAY, line_step=16)
    bg.alpha_composite(cow, ((W - cow.width) // 2, 210))
    bg.convert("RGB").save(os.path.join(OUT, "bg_sun.png"))
    return bg, time3_x, sec2_x, sec2_y


def paste_on(img, path, x, y):
    g = Image.open(os.path.join(OUT, path)).convert("RGBA")
    img.alpha_composite(g, (x, y))
    return g.width


def bottom_row_preview(img):
    """Sample steps (left) and battery (right) like the weekend bottomRow()."""
    x = 30
    for p in ("steps/8.png", "steps/4.png", "steps/7.png", "steps/6.png"):
        x += paste_on(img, p, x, BOTTOM_Y)
    parts = ["batt/7.png", "batt/3.png", "batt/percent.png"]
    x = 360 - sum(Image.open(os.path.join(OUT, p)).width for p in parts)
    for p in parts:
        x += paste_on(img, p, x, BOTTOM_Y)


def date_row_preview(img, week_png, y):
    x = DATE_X
    x += paste_on(img, week_png, x, y) + DATE_GAP
    for p in ("date/1.png", "date/1.png", "date/slash.png", "date/0.png", "date/8.png"):
        x += paste_on(img, p, x, y)


def make_preview_sat(bg):
    img = bg.copy()
    date_row_preview(img, "week/5.png", DATE_Y)
    d = ImageDraw.Draw(img)
    # left pupil at second 42 (252°) with the number riding inside;
    # right pupil rolled toward gravity, down-left
    a = math.radians(252)
    lx = EYE_L[0] + PUPIL_ORBIT * math.sin(a)
    ly = EYE_L[1] - PUPIL_ORBIT * math.cos(a)
    rx = EYE_R[0] - PUPIL_ORBIT * 0.60
    ry = EYE_R[1] + PUPIL_ORBIT * 0.75
    for px_, py in ((lx, ly), (rx, ry)):
        d.ellipse([px_ - PUPIL_R, py - PUPIL_R, px_ + PUPIL_R, py + PUPIL_R],
                  fill=(22, 22, 28, 255))
    paste_on(img, "secs/4.png", int(lx) - 12, int(ly) - 11)
    paste_on(img, "secs/2.png", int(lx), int(ly) - 11)
    x = 57
    for p in ("time/1.png", "time/0.png", "time/colon.png", "time/0.png", "time/8.png"):
        x += paste_on(img, p, x, 296)
    bottom_row_preview(img)
    img.convert("RGB").save(os.path.join(OUT, "preview_sat.png"))


def make_preview_sun(bg, time3_x, sec2_x, sec2_y):
    img = bg.copy()
    date_row_preview(img, "week/6.png", 8)
    x = time3_x
    for p in ("time3/1.png", "time3/0.png", "time3/colon.png", "time3/0.png", "time3/8.png"):
        x += paste_on(img, p, x, TIME3_Y)
    x = sec2_x
    for p in ("date/4.png", "date/2.png"):
        x += paste_on(img, p, x, sec2_y)
    bottom_row_preview(img)
    img.convert("RGB").save(os.path.join(OUT, "preview_sun.png"))


# ---- Monday: v9n consulting -------------------------------------------------
# Light, minimal face in the v9n.us design system: white background,
# #1a1a1a ink, #666 secondary gray, the site's 135-degree 1a1a1a -> 4a4a4a
# gradient on the wordmark, and rounded-rect bordered chips (the
# .contact-email treatment). Sans instead of pixels — Monday means work.
V9N_INK = (26, 26, 26)
V9N_GRAY = (102, 102, 102)
V9N_BORDER = (186, 186, 189)  # rgba(26,26,26,0.3) composited on white
V9N_SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
V9N_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def _sans_img(text, size, color, font_path=V9N_SANS_BOLD, fixed_w=None):
    """Anti-aliased sans text on transparent background. Cell height is
    ascent+descent (constant per size) so baselines line up across sprites;
    fixed_w centers the glyph on a fixed cell for monospaced digit arrays."""
    font = ImageFont.truetype(font_path, size)
    ascent, descent = font.getmetrics()
    h = ascent + descent
    w = max(1, int(round(font.getlength(text))))
    cw_ = fixed_w if fixed_w else w
    img = Image.new("RGBA", (cw_, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((round((cw_ - w) / 2) if fixed_w else 0, 0),
                             text, font=font, fill=color + (255,))
    return img


def make_fonts_v9n():
    for sub in ("time_v", "date_v", "week_v", "num_v"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    tw = int(round(ImageFont.truetype(V9N_SANS_BOLD, 86).getlength("0"))) + 2
    dw = int(round(ImageFont.truetype(V9N_SANS, 30).getlength("0"))) + 2
    nw = int(round(ImageFont.truetype(V9N_SANS_BOLD, 38).getlength("0"))) + 2
    for i in range(10):
        _sans_img(str(i), 86, V9N_INK, fixed_w=tw).save(
            os.path.join(OUT, "time_v", f"{i}.png"))
        _sans_img(str(i), 30, V9N_GRAY, V9N_SANS, fixed_w=dw).save(
            os.path.join(OUT, "date_v", f"{i}.png"))
        _sans_img(str(i), 38, V9N_INK, fixed_w=nw).save(
            os.path.join(OUT, "num_v", f"{i}.png"))
    _sans_img(":", 86, V9N_INK).save(os.path.join(OUT, "time_v", "colon.png"))
    _sans_img("/", 30, V9N_GRAY, V9N_SANS).save(os.path.join(OUT, "date_v", "slash.png"))
    _sans_img("%", 38, V9N_INK).save(os.path.join(OUT, "num_v", "percent.png"))
    week_imgs = [_sans_img(n, 30, V9N_GRAY) for n in WEEKDAYS]
    wk_w = max(im.width for im in week_imgs) + 2
    for i, n in enumerate(WEEKDAYS):
        _sans_img(n, 30, V9N_GRAY, fixed_w=wk_w).save(
            os.path.join(OUT, "week_v", f"{i}.png"))
    return {"tw": tw, "dw": dw, "nw": nw, "wk_w": wk_w,
            "colon_w": Image.open(os.path.join(OUT, "time_v", "colon.png")).width,
            "slash_w": Image.open(os.path.join(OUT, "date_v", "slash.png")).width,
            "time_h": Image.open(os.path.join(OUT, "time_v", "0.png")).height,
            "date_h": Image.open(os.path.join(OUT, "date_v", "0.png")).height}


# chip geometry shared with index.js
V9N_CHIPS = {"steps": (30, 292, 185, 384), "battery": (205, 292, 360, 384)}
V9N_NUM_Y = 330  # TEXT_IMG y inside the chips


def make_bg_mon(f):
    """White page under the v9n.us menu bar: navy ribbon (business-card
    #2c3e50 -> #34495e, 90deg), #5dade2 accent rule fading out to the right,
    wordmark 'v9n' bold white + 'consulting' light #a9c7e0."""
    NAVY1, NAVY2 = (44, 62, 80), (52, 73, 94)
    ACCENT = (93, 173, 226)
    LOGO_BLUE = (169, 199, 224)
    RIBBON_H = 86
    bg = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(bg)
    for x in range(W):
        t = x / (W - 1)
        navy = tuple(int(a + (b - a) * t) for a, b in zip(NAVY1, NAVY2))
        d.rectangle([x, 0, x, RIBBON_H - 1], fill=navy + (255,))
        # accent rule on the ribbon's bottom edge: opaque -> 0.4 at 50% -> 0
        a = 1.0 - 1.2 * t if t <= 0.5 else 0.4 * (1 - (t - 0.5) * 2)
        rule = tuple(int(n + (c - n) * a) for n, c in zip(navy, ACCENT))
        d.rectangle([x, RIBBON_H - 3, x, RIBBON_H - 1], fill=rule + (255,))
    wm1 = _sans_img("v9n ", 40, (255, 255, 255))
    wm2 = _sans_img("consulting", 40, LOGO_BLUE, V9N_SANS)
    x0 = (W - wm1.width - wm2.width) // 2
    wm_y = (RIBBON_H - wm1.height) // 2
    bg.alpha_composite(wm1, (x0, wm_y))
    bg.alpha_composite(wm2, (x0 + wm1.width, wm_y))
    hl_y = RIBBON_H + 4  # keeps the layout math below unchanged
    for name, box in V9N_CHIPS.items():
        d.rounded_rectangle(box, radius=14, outline=V9N_BORDER + (255,), width=3)
        lab = _sans_img(name, 21, V9N_GRAY, V9N_SANS)
        cx = (box[0] + box[2]) // 2
        bg.alpha_composite(lab, (cx - lab.width // 2, box[1] + 10))
    bg.convert("RGB").save(os.path.join(OUT, "bg_mon.png"))

    # layout shared with index.js
    c = {}
    date_total = f["wk_w"] + 10 + 4 * f["dw"] + f["slash_w"]
    c["WEEK_VX"] = (W - date_total) // 2
    c["DATE_VY"] = hl_y + 16
    c["MONTH_VX"] = c["WEEK_VX"] + f["wk_w"] + 10
    time_w = 4 * f["tw"] + f["colon_w"]
    group = time_w + 8 + 2 * f["dw"]
    c["TIME_VX"] = (W - group) // 2
    c["TIME_VY"] = 168
    c["SECV_X"] = c["TIME_VX"] + time_w + 8
    c["SECV_Y"] = c["TIME_VY"] + f["time_h"] - f["date_h"] - 12
    return bg, c


def make_preview_mon(bg, f, c):
    img = bg.copy()
    x = c["WEEK_VX"]
    x += paste_on(img, "week_v/0.png", x, c["DATE_VY"]) + 10
    for p in ("date_v/1.png", "date_v/1.png", "date_v/slash.png",
              "date_v/1.png", "date_v/0.png"):
        x += paste_on(img, p, x, c["DATE_VY"])
    x = c["TIME_VX"]
    for p in ("time_v/1.png", "time_v/0.png", "time_v/colon.png",
              "time_v/0.png", "time_v/8.png"):
        x += paste_on(img, p, x, c["TIME_VY"])
    x = c["SECV_X"]
    for p in ("date_v/3.png", "date_v/7.png"):
        x += paste_on(img, p, x, c["SECV_Y"])
    for name, digits in (("steps", "8476"), ("battery", "73%")):
        box = V9N_CHIPS[name]
        parts = ["num_v/percent.png" if ch == "%" else f"num_v/{ch}.png"
                 for ch in digits]
        tot = sum(Image.open(os.path.join(OUT, p)).width for p in parts)
        x = (box[0] + box[2]) // 2 - tot // 2
        for p in parts:
            x += paste_on(img, p, x, V9N_NUM_Y)
    img.convert("RGB").save(os.path.join(OUT, "preview_mon.png"))


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
    # green second-gear at sample second 42: 42 * 6 = 252° clockwise
    # (PIL rotates counterclockwise for positive angles, hence the minus)
    gear = Image.open(os.path.join(OUT, "gear.png")).rotate(-252, resample=Image.BICUBIC)
    img.alpha_composite(gear, (GEAR_CX - GEAR_SIZE // 2, GEAR_CY - GEAR_SIZE // 2))
    # seconds digits in the gear hub (SEC_X/SEC_Y in index.js)
    paste("date/4.png", GEAR_CX - 24, GEAR_CY - 22)
    paste("date/2.png", GEAR_CX, GEAR_CY - 22)
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
    make_gear()
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

    # weekend faces
    bg_sat = make_bg_sat()
    pupil_c = make_pupil_dot()
    bg_sun, TIME3_X, SEC2_X, SEC2_Y = make_bg_sun()
    make_preview_sat(bg_sat)
    make_preview_sun(bg_sun, TIME3_X, SEC2_X, SEC2_Y)

    # Monday: v9n consulting
    fv = make_fonts_v9n()
    bg_mon, cv = make_bg_mon(fv)
    make_preview_mon(bg_mon, fv, cv)
    print("v9n constants:", " ".join(f"{k}={v}" for k, v in cv.items()),
          f"CHIPS={V9N_CHIPS} NUM_Y={V9N_NUM_Y} "
          f"num_h={Image.open(os.path.join(OUT, 'num_v', '0.png')).height}")

    print("assets written to", OUT)
    secd = Image.open(os.path.join(OUT, "secs", "0.png"))
    print(f"weekend constants: EYE_L={EYE_L} EYE_R={EYE_R} "
          f"PUPIL_ORBIT={PUPIL_ORBIT} PUPIL_C={pupil_c} "
          f"SEC_DIG={secd.width}x{secd.height} "
          f"TIME3_X={TIME3_X} TIME3_Y={TIME3_Y} "
          f"SEC2_X={SEC2_X} SEC2_Y={SEC2_Y} BOTTOM_Y={BOTTOM_Y}")
    print(f"index.js constants: WEEK_X={DATE_X} DATE_Y={DATE_Y} "
          f"MONTH_X={DATE_X + week_w + DATE_GAP} TIME_X={(W - time_w) // 2} TIME_Y={TIME_Y} "
          f"GEAR_CENTER=({GEAR_CX},{GEAR_CY}) GEAR_POS={GEAR_SIZE // 2} "
          f"SEC_X={GEAR_CX - 24} SEC_Y={GEAR_CY - 22} "
          f"(time digits {Image.open(os.path.join(OUT, 'time', '0.png')).width}w, "
          f"colon {Image.open(os.path.join(OUT, 'time', 'colon.png')).width}w, "
          f"labels {Image.open(os.path.join(OUT, 'label_steps.png')).width}x"
          f"{Image.open(os.path.join(OUT, 'label_steps.png')).height} / "
          f"{Image.open(os.path.join(OUT, 'label_batt.png')).width}x"
          f"{Image.open(os.path.join(OUT, 'label_batt.png')).height})")
