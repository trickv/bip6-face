#!/usr/bin/env python3
"""Turn the half-block QR from a `zeus preview` terminal capture into a PNG,
annotated with the app/face name, build time, and git revision so installs
are tellable apart in a photo album.

Usage: qr2png.py <capture.txt> <out.png> [label]

Takes the LAST QR block in the capture (tmux scrollback accumulates old
ones). If no label is given, uses the "[Device] name-version" line zeus
prints above the QR.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MODULE = 8      # pixels per QR module
QUIET = 4       # quiet-zone modules on each side
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def parse_blocks(lines):
    """Split capture into contiguous half-block QR line groups, keeping the
    non-QR line that precedes each (zeus prints '[Device] app-version' there)."""
    blocks, cur, context, last_text = [], [], [], ""
    for line in lines:
        if re.search(r"[█▀▄]", line):
            cur.append(line.rstrip())
        else:
            if cur:
                blocks.append((last_text, cur))
                cur = []
            if line.strip():
                last_text = line.strip()
    if cur:
        blocks.append((last_text, cur))
    return blocks


def block_to_matrix(qr_lines):
    width = max(len(l) for l in qr_lines)
    rows = []
    for l in qr_lines:
        l = l.ljust(width)
        top, bot = [], []
        for ch in l:
            t, b = {"█": (1, 1), "▀": (1, 0), "▄": (0, 1)}.get(ch, (0, 0))
            top.append(t)
            bot.append(b)
        rows.append(top)
        rows.append(bot)
    while rows and not any(rows[0]):
        rows.pop(0)
    while rows and not any(rows[-1]):
        rows.pop()
    xs = [i for r in rows for i, v in enumerate(r) if v]
    x0, x1 = min(xs), max(xs)
    return [r[x0 : x1 + 1] for r in rows]


def git_rev():
    here = Path(__file__).resolve().parent
    try:
        rev = subprocess.run(
            ["git", "-C", here, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", here, "status", "--porcelain"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return rev + ("+" if dirty else "")
    except Exception:
        return "?"


def main():
    src, dst = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else None

    blocks = parse_blocks(Path(src).read_text(encoding="utf8").splitlines())
    if not blocks:
        sys.exit("no QR block found in " + src)
    context, qr_lines = blocks[-1]
    if label is None:
        m = re.search(r"\[[^\]]+\]\s*(\S.*)", context)
        label = m.group(1).strip() if m else "unknown app"

    rows = block_to_matrix(qr_lines)
    qw = (len(rows[0]) + 2 * QUIET) * MODULE
    qh = (len(rows) + 2 * QUIET) * MODULE

    stamp = time.strftime("%Y-%m-%d %H:%M") + "  ·  " + git_rev()
    f_big = ImageFont.truetype(FONT_BOLD, 24)
    f_small = ImageFont.truetype(FONT, 18)
    caption_h = 70

    # White-on-black, matching the terminal QR (scans fine inverted).
    img = Image.new("L", (qw, qh + caption_h), 0)
    px = img.load()
    for gy, row in enumerate(rows):
        for gx, v in enumerate(row):
            if v:
                x0 = (gx + QUIET) * MODULE
                y0 = (gy + QUIET) * MODULE
                for dy in range(MODULE):
                    for dx in range(MODULE):
                        px[x0 + dx, y0 + dy] = 255

    d = ImageDraw.Draw(img)
    d.text((qw // 2, qh), label, font=f_big, fill=255, anchor="ma")
    d.text((qw // 2, qh + 32), stamp, font=f_small, fill=200, anchor="ma")

    img.save(dst)
    print("ok", img.size, "label:", label, "stamp:", stamp)


if __name__ == "__main__":
    main()
