#!/usr/bin/env python3
"""Render the current git commit as a tiny build stamp (assets/bip6/version.png).

Run after committing and before `zeus build`; the sprite is gitignored so the
stamp always reflects the HEAD the package was built from ('+' = dirty tree).
Shown centered at the very bottom of every face so a bridge screenshot proves
which build is running.
"""
import subprocess

from PIL import Image

import gen_assets as g


def main():
    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True, check=True).stdout.strip()
    tag = rev + ("+" if dirty else "")
    txt = g._pixel_img(tag, 1, (128, 128, 128))
    strip = Image.new("RGBA", (g.W, txt.height), (0, 0, 0, 0))
    strip.alpha_composite(txt, ((g.W - txt.width) // 2, 0))
    import os
    strip.save(os.path.join(g.OUT, "version.png"))
    print(f"version stamp: {tag} ({txt.width}x{txt.height})")


if __name__ == "__main__":
    main()
