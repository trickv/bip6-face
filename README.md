# bip6-face — "GLX Gears"

An old-school-Linux Zepp OS watchface for the Amazfit Bip 6 (390×450 AMOLED),
in the classic X11 `misc-fixed` 10x20 bitmap font. Three layouts, picked by
day of week:

- **Mon–Fri: glxgears** — the green gear is the second hand (one revolution
  per minute, white marker tooth at 12 o'clock on the minute), with seconds
  in its hub, plus date, steps, battery %, and moon phase.
- **Saturday: xeyes** — the pupils are pointer hands: left eye orbits once
  per minute (seconds), right eye once per hour (minutes).
- **Sunday: cowsay** — the cow says the time.

## Layout

- `app.json` — Zepp OS project manifest (appType `watchface`, Bip 6 deviceSources 9765120 / 9765121 / 10158337)
- `app.js` — required app entry stub
- `watchface/index.js` — the face: background IMG, `IMG_TIME` for the clock, `TEXT_IMG` widgets bound to `data_type.STEP` and `data_type.BATTERY` (the OS updates them automatically)
- `gen_assets.py` — regenerates everything in `assets/bip6/` (gears background, digit sprites, labels, icon, preview) with Pillow
- `assets/bip6/` — generated PNGs

## Build

```sh
npm i -g @zeppos/zeus-cli   # official Zepp OS CLI (needs Node)
python3 gen_assets.py       # only if you changed the art
zeus build                  # produces dist/*.zab
```

## Install on the watch

1. In the Zepp phone app: Profile → Settings → About → tap the Zepp logo ~7 times to unlock **Developer Mode** (it appears under Settings).
2. `zeus login` (same Zepp account as the phone app), then `zeus preview` — prints a QR code.
3. Zepp app → Profile → your Bip 6 → Developer Mode → scan the QR. The face installs over Bluetooth; pick it in the watch's watchface list (long-press the face or Settings → Watchface).

## Tweak

Edit colors/layout in `gen_assets.py` + coordinates in `watchface/index.js`, rerun the two build steps.
