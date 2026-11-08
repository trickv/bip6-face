// xeyes for the Bip 6 — the Mini Program the watchface couldn't be.
// Both pupils roll toward gravity, straight from the accelerometer.
// (Watchfaces are stuck on the 1.0 API with no sensor access; apps are not.)
import * as hmUI from '@zos/ui'
import { Accelerometer, FREQ_MODE_HIGH } from '@zos/sensor'
import { setPageBrightTime, pauseDropWristScreenOff } from '@zos/display'

// eye geometry, same art as the Saturday watchface (bg.png / pupil.png)
const EYE_L_X = 110
const EYE_L_Y = 195
const EYE_R_X = 280
const EYE_R_Y = 195
const PUPIL_ORBIT = 38
const PUPIL_C = 21 // pupil.png top-left -> center

// accelerometer reading (cm/s^2) at which the pupils peg their orbit;
// ~600 is roughly a 37-degree tilt. At rest the sensor reads the reaction
// force (opposite gravity; x right, y toward 12 o'clock), so screen-x
// flips and sensor-y maps straight onto screen-y-down.
const FULL = 600
const SMOOTH = 0.45 // per-update low-pass so the eyes glide, not jitter

let accel = null
let pupilL = null
let pupilR = null
let curX = 0
let curY = 0

function update() {
  let tx = 0
  let ty = 0
  try {
    const v = accel.getCurrent()
    tx = (-v.x * PUPIL_ORBIT) / FULL
    ty = (v.y * PUPIL_ORBIT) / FULL
  } catch (e) {}
  const m = Math.sqrt(tx * tx + ty * ty)
  if (m > PUPIL_ORBIT) {
    tx = (tx * PUPIL_ORBIT) / m
    ty = (ty * PUPIL_ORBIT) / m
  }
  curX += (tx - curX) * SMOOTH
  curY += (ty - curY) * SMOOTH
  const ox = Math.round(curX)
  const oy = Math.round(curY)
  pupilL.setProperty(hmUI.prop.MORE, {
    x: EYE_L_X + ox - PUPIL_C,
    y: EYE_L_Y + oy - PUPIL_C
  })
  pupilR.setProperty(hmUI.prop.MORE, {
    x: EYE_R_X + ox - PUPIL_C,
    y: EYE_R_Y + oy - PUPIL_C
  })
}

Page({
  onInit() {},

  build() {
    try {
      hmUI.setStatusBarVisible(false)
    } catch (e) {}
    hmUI.createWidget(hmUI.widget.IMG, { x: 0, y: 0, src: 'bg.png' })
    pupilL = hmUI.createWidget(hmUI.widget.IMG, {
      x: EYE_L_X - PUPIL_C,
      y: EYE_L_Y - PUPIL_C,
      src: 'pupil.png'
    })
    pupilR = hmUI.createWidget(hmUI.widget.IMG, {
      x: EYE_R_X - PUPIL_C,
      y: EYE_R_Y - PUPIL_C,
      src: 'pupil.png'
    })

    // keep the show on stage while you play with it
    try {
      setPageBrightTime({ brightTime: 300000 })
      pauseDropWristScreenOff({ duration: 300000 })
    } catch (e) {}

    accel = new Accelerometer()
    try {
      accel.setFreqMode(FREQ_MODE_HIGH)
    } catch (e) {}
    accel.onChange(update)
    accel.start()
  },

  onDestroy() {
    if (accel) {
      try {
        accel.offChange(update)
        accel.stop()
      } catch (e) {}
    }
  }
})
