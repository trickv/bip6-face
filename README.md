# bip6-face — "GLX Gears"

An old-school-Linux Zepp OS watchface for the Amazfit Bip 6 (390×450 AMOLED),
in the classic X11 `misc-fixed` 10x20 bitmap font. Three layouts, picked by
day of week:

- **Monday: v9n consulting** — a light, minimal face in the
  [v9n.us](https://v9n.us) design system: navy menu-bar ribbon with the
  wordmark, sans type, and rounded-chip steps/battery.
- **Tue–Fri: glxgears** — the green gear is the second hand (one revolution
  per minute, white marker tooth at 12 o'clock on the minute), with seconds
  in its hub, plus date, steps, battery %, and moon phase.
- **Saturday: xeyes** — the left pupil orbits with the seconds and carries
  the seconds number inside it; the right pupil is a minute hand in
  disguise. (A gravity-driven googly eye is impossible in a watchface:
  the 1.x watchface API has no sensor access, and apiVersion 2.0+ removes
  the hm* globals — verified on-device, see branch `probe-api2`. The real
  googly eyes live in the `xeyes-app/` Mini Program instead.)
- **Sunday: cowsay** — the cow says the time, seconds included.

## Layout

- `app.json` — Zepp OS project manifest (appType `watchface`, Bip 6 deviceSources 9765120 / 9765121 / 10158337)
- `app.js` — required app entry stub
- `watchface/index.js` — the face: background IMG, `IMG_TIME` for the clock, `TEXT_IMG` widgets bound to `data_type.STEP` and `data_type.BATTERY` (the OS updates them automatically)
- `gen_assets.py` — regenerates everything in `assets/bip6/` (gears background, digit sprites, labels, icon, preview) with Pillow
- `assets/bip6/` — generated PNGs
- `xeyes-app/` — bonus Mini Program: true xeyes, both pupils roll toward gravity via the accelerometer (apps get the `@zos` API that watchfaces can't have)
- `v9n-card-app/` — bonus Mini Program: v9n consulting business card — logo screen, then swipe right through QR codes (v9n.us, blog, vCard with cell number)

## Build

```sh
npm i -g @zeppos/zeus-cli   # official Zepp OS CLI (needs Node)
python3 gen_assets.py       # only if you changed the art
python3 gen_version.py      # tiny on-face build stamp (git commit)
zeus build                  # produces dist/*.zab
```

## Install on the watch

1. In the Zepp phone app: Profile → Settings → About → tap the Zepp logo ~7 times to unlock **Developer Mode** (it appears under Settings).
2. `zeus login` (same Zepp account as the phone app), then `zeus preview` — prints a QR code.
3. Zepp app → Profile → your Bip 6 → Developer Mode → scan the QR. The face installs over Bluetooth; pick it in the watch's watchface list (long-press the face or Settings → Watchface).

## Mini apps

The two bonus apps build the same way, each from its own directory:

```sh
cd xeyes-app && zeus build        # or: zeus preview for an install QR
cd v9n-card-app && python3 gen_cards.py && zeus build
```

## Tweak

Edit colors/layout in `gen_assets.py` + coordinates in `watchface/index.js`, rerun the two build steps.
