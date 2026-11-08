#!/usr/bin/env python3
"""Bump an app.json version before committing a change to that app.

Usage: bump_version.py <dir-or-app.json> [...]
       bump_version.py all          # watchface + every *-app/ directory

Increments version.code and sets version.name to 1.0.<code>, which is the
version zeus prints next to the QR and qr2png.py bakes into the album PNG.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def bump(path):
    p = Path(path)
    if p.is_dir():
        p = p / "app.json"
    data = json.loads(p.read_text())
    v = data["app"]["version"]
    v["code"] += 1
    v["name"] = "1.0.%d" % v["code"]
    p.write_text(json.dumps(data, indent=2) + "\n")
    print(p, "->", v["name"])


targets = sys.argv[1:]
if not targets:
    sys.exit(__doc__)
if targets == ["all"]:
    targets = [HERE] + sorted(HERE.glob("*-app"))
for t in targets:
    bump(t)
