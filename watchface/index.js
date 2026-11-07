// NOTE: watchfaces are stuck on the 1.x hm* API, which has no module
// loader and no motion sensors; apiVersion 2.0+ removes the hm* globals
// entirely (verified on-device — see the probe-api2 branch). So no
// accelerometer here: the right xeye is a minute hand, and the true
// gravity-driven googly eyes live in the xeyes-app/ Mini Program.
const SCREEN_W = 390

const digitArray = (dir) => [
  dir + '/0.png',
  dir + '/1.png',
  dir + '/2.png',
  dir + '/3.png',
  dir + '/4.png',
  dir + '/5.png',
  dir + '/6.png',
  dir + '/7.png',
  dir + '/8.png',
  dir + '/9.png'
]

const timeDigits = digitArray('time')
const time3Digits = digitArray('time3')
const dateDigits = digitArray('date')
const stepDigits = digitArray('steps')
const battDigits = digitArray('batt')
// Monday v9n face (sans sprites)
const timeVDigits = digitArray('time_v')
const dateVDigits = digitArray('date_v')
const numVDigits = digitArray('num_v')
const weekVArray = [
  'week_v/0.png',
  'week_v/1.png',
  'week_v/2.png',
  'week_v/3.png',
  'week_v/4.png',
  'week_v/5.png',
  'week_v/6.png'
]

// lunar day 0..28 (0 = new, ~14 = full), indexed by data_type.MOON's level
const moonArray = []
for (let i = 0; i < 29; i++) moonArray.push('moon/' + i + '.png')

// MON-first, matching Zepp OS week numbering (1 = Monday)
const weekArray = [
  'week/0.png',
  'week/1.png',
  'week/2.png',
  'week/3.png',
  'week/4.png',
  'week/5.png',
  'week/6.png'
]

// Three layouts: weekdays = glxgears, Saturday = xeyes, Sunday = cowsay.
// The layout is chosen by day of week at build time and re-checked every
// time the face resumes, so the Monday flip happens on first wake.
let timeSensor = null
let widgets = []
let mode = ''

function cw(type, cfg) {
  const w = hmUI.createWidget(type, cfg)
  widgets.push(w)
  return w
}

function dayMode() {
  // time sensor week: 1 = Monday .. 7 = Sunday
  if (timeSensor.week === 1) return 'mon'
  if (timeSensor.week === 6) return 'sat'
  if (timeSensor.week === 7) return 'sun'
  return 'weekday'
}

// WEEK MM/DD row — week images 64px wide + 12px gap, digits 24px, slash 24px
function dateRow(y) {
  cw(hmUI.widget.IMG_WEEK, {
    x: 97,
    y: y,
    week_en: weekArray,
    week_sc: weekArray,
    week_tc: weekArray
  })
  cw(hmUI.widget.IMG_DATE, {
    month_startX: 173,
    month_startY: y,
    month_zero: 1,
    month_en_array: dateDigits,
    month_sc_array: dateDigits,
    month_tc_array: dateDigits,
    month_unit_en: 'date/slash.png',
    month_unit_sc: 'date/slash.png',
    month_unit_tc: 'date/slash.png',
    day_follow: 1,
    day_zero: 1,
    day_en_array: dateDigits,
    day_sc_array: dateDigits,
    day_tc_array: dateDigits
  })
}

// compact weekend footer: steps bottom-left (red), battery bottom-right (green)
function bottomRow() {
  cw(hmUI.widget.TEXT_IMG, {
    x: 30,
    y: 398,
    w: 150,
    h: 44,
    type: hmUI.data_type.STEP,
    font_array: stepDigits,
    align_h: hmUI.align.LEFT
  })
  cw(hmUI.widget.TEXT_IMG, {
    x: 210,
    y: 398,
    w: 150,
    h: 44,
    type: hmUI.data_type.BATTERY,
    font_array: battDigits,
    unit_sc: 'batt/percent.png',
    unit_tc: 'batt/percent.png',
    unit_en: 'batt/percent.png',
    align_h: hmUI.align.RIGHT
  })
}

function buildWeekday() {
  cw(hmUI.widget.IMG, { x: 0, y: 0, src: 'background.png' })

  // the green gear is the "second hand": the OS rotates it about its
  // center 6° per second, one revolution per minute. The sprite is
  // authored with its white marker tooth pointing up, which is the
  // second-0 orientation — so the marker hits 12 o'clock at :00.
  cw(hmUI.widget.TIME_POINTER, {
    second_centerX: 320,
    second_centerY: 230,
    second_posX: 106,
    second_posY: 106,
    second_path: 'gear.png'
  })

  // moon phase disc, right of the battery % (MOON_X/MOON_Y in
  // gen_assets.py) — the top-right corner is clipped by the rounded screen
  cw(hmUI.widget.IMG_LEVEL, {
    x: 300,
    y: 376,
    image_array: moonArray,
    image_length: moonArray.length,
    type: hmUI.data_type.MOON,
    show_level: hmUI.show_level.ONLY_NORMAL
  })

  dateRow(52)

  // HH:MM — digits are 60px wide, colon 35px, so 4*60 + 35 = 275 total.
  // Small seconds (the 24x44 white date digits) sit in the gear's hub —
  // the hub is the rotation pivot, so it stays put under them.
  cw(hmUI.widget.IMG_TIME, {
    hour_zero: 1,
    hour_startX: 57,
    hour_startY: 108,
    hour_array: timeDigits,
    hour_unit_sc: 'time/colon.png',
    hour_unit_tc: 'time/colon.png',
    hour_unit_en: 'time/colon.png',
    minute_follow: 1,
    minute_zero: 1,
    minute_array: timeDigits,
    second_zero: 1,
    second_startX: 296,
    second_startY: 208,
    second_array: dateDigits
  })

  cw(hmUI.widget.IMG, { x: 169, y: 252, src: 'label_steps.png' })
  cw(hmUI.widget.TEXT_IMG, {
    x: 0,
    y: 280,
    w: SCREEN_W,
    h: 44,
    type: hmUI.data_type.STEP,
    font_array: stepDigits,
    align_h: hmUI.align.CENTER_H
  })

  cw(hmUI.widget.IMG, { x: 159, y: 344, src: 'label_batt.png' })
  cw(hmUI.widget.TEXT_IMG, {
    x: 0,
    y: 372,
    w: SCREEN_W,
    h: 44,
    type: hmUI.data_type.BATTERY,
    font_array: battDigits,
    unit_sc: 'batt/percent.png',
    unit_tc: 'batt/percent.png',
    unit_en: 'batt/percent.png',
    align_h: hmUI.align.CENTER_H
  })
}

// xeyes geometry (from gen_assets.py)
const EYE_L_X = 110
const EYE_L_Y = 195
const EYE_R_X = 280
const EYE_R_Y = 195
const PUPIL_ORBIT = 38 // max pupil-center offset from the eye center
const PUPIL_C = 21 // pupil_dot.png top-left -> center
const SEC_DIG_W = 12 // secs/ digit size
const SEC_DIG_H = 22

let secPupil = null
let secDigit1 = null
let secDigit2 = null
let minutePupil = null
let satTimer = null

function placePupil(w, cx, cy) {
  w.setProperty(hmUI.prop.MORE, { x: cx - PUPIL_C, y: cy - PUPIL_C })
}

function tickSat() {
  // left eye: pupil orbits with the seconds, number riding inside it
  const s = timeSensor.second
  const a = (s * 6 * Math.PI) / 180
  const lx = EYE_L_X + Math.round(PUPIL_ORBIT * Math.sin(a))
  const ly = EYE_L_Y - Math.round(PUPIL_ORBIT * Math.cos(a))
  placePupil(secPupil, lx, ly)
  secDigit1.setProperty(hmUI.prop.MORE, {
    x: lx - SEC_DIG_W,
    y: ly - SEC_DIG_H / 2,
    src: 'secs/' + Math.floor(s / 10) + '.png'
  })
  secDigit2.setProperty(hmUI.prop.MORE, {
    x: lx,
    y: ly - SEC_DIG_H / 2,
    src: 'secs/' + (s % 10) + '.png'
  })

  // right eye: a minute hand in disguise, one revolution per hour
  const am = (timeSensor.minute * 6 * Math.PI) / 180
  placePupil(
    minutePupil,
    EYE_R_X + Math.round(PUPIL_ORBIT * Math.sin(am)),
    EYE_R_Y - Math.round(PUPIL_ORBIT * Math.cos(am))
  )
}

function startSat() {
  if (satTimer !== null) return
  try {
    tickSat()
    satTimer = timer.createTimer(250, 250, tickSat)
  } catch (e) {}
}

function stopSat() {
  if (satTimer !== null) {
    timer.stopTimer(satTimer)
    satTimer = null
  }
}

function buildSaturday() {
  // xeyes, live edition: a 4 Hz timer slides the pupil sprites around.
  cw(hmUI.widget.IMG, { x: 0, y: 0, src: 'bg_sat.png' })
  secPupil = cw(hmUI.widget.IMG, {
    x: EYE_L_X - PUPIL_C,
    y: EYE_L_Y - PUPIL_C,
    src: 'pupil_dot.png'
  })
  secDigit1 = cw(hmUI.widget.IMG, {
    x: EYE_L_X - SEC_DIG_W,
    y: EYE_L_Y - SEC_DIG_H / 2,
    src: 'secs/0.png'
  })
  secDigit2 = cw(hmUI.widget.IMG, {
    x: EYE_L_X,
    y: EYE_L_Y - SEC_DIG_H / 2,
    src: 'secs/0.png'
  })
  minutePupil = cw(hmUI.widget.IMG, {
    x: EYE_R_X - PUPIL_C,
    y: EYE_R_Y - PUPIL_C,
    src: 'pupil_dot.png'
  })
  dateRow(52)
  cw(hmUI.widget.IMG_TIME, {
    hour_zero: 1,
    hour_startX: 57,
    hour_startY: 296,
    hour_array: timeDigits,
    hour_unit_sc: 'time/colon.png',
    hour_unit_tc: 'time/colon.png',
    hour_unit_en: 'time/colon.png',
    minute_follow: 1,
    minute_zero: 1,
    minute_array: timeDigits
  })
  bottomRow()
  startSat()
}

function buildSunday() {
  // cowsay: the bubble, cow, and < > are baked into bg_sun.png;
  // only the scale-3 time digits inside the bubble are live.
  cw(hmUI.widget.IMG, { x: 0, y: 0, src: 'bg_sun.png' })
  dateRow(8)
  cw(hmUI.widget.IMG_TIME, {
    hour_zero: 1,
    hour_startX: 77,
    hour_startY: 100,
    hour_array: time3Digits,
    hour_unit_sc: 'time3/colon.png',
    hour_unit_tc: 'time3/colon.png',
    hour_unit_en: 'time3/colon.png',
    minute_follow: 1,
    minute_zero: 1,
    minute_array: time3Digits,
    // seconds after a colon baked into bg_sun.png, inside the bubble
    second_zero: 1,
    second_startX: 264,
    second_startY: 122,
    second_array: dateDigits
  })
  bottomRow()
}

function buildMonday() {
  // v9n consulting — light minimal face in the v9n.us design system.
  // Wordmark, hairline, and chip outlines are baked into bg_mon.png.
  cw(hmUI.widget.IMG, { x: 0, y: 0, src: 'bg_mon.png' })
  cw(hmUI.widget.IMG_WEEK, {
    x: 112,
    y: 106,
    week_en: weekVArray,
    week_sc: weekVArray,
    week_tc: weekVArray
  })
  cw(hmUI.widget.IMG_DATE, {
    month_startX: 194,
    month_startY: 106,
    month_zero: 1,
    month_en_array: dateVDigits,
    month_sc_array: dateVDigits,
    month_tc_array: dateVDigits,
    month_unit_en: 'date_v/slash.png',
    month_unit_sc: 'date_v/slash.png',
    month_unit_tc: 'date_v/slash.png',
    day_follow: 1,
    day_zero: 1,
    day_en_array: dateVDigits,
    day_sc_array: dateVDigits,
    day_tc_array: dateVDigits
  })
  cw(hmUI.widget.IMG_TIME, {
    hour_zero: 1,
    hour_startX: 57,
    hour_startY: 168,
    hour_array: timeVDigits,
    hour_unit_sc: 'time_v/colon.png',
    hour_unit_tc: 'time_v/colon.png',
    hour_unit_en: 'time_v/colon.png',
    minute_follow: 1,
    minute_zero: 1,
    minute_array: timeVDigits,
    second_zero: 1,
    second_startX: 294,
    second_startY: 218,
    second_array: dateVDigits
  })
  cw(hmUI.widget.TEXT_IMG, {
    x: 30,
    y: 330,
    w: 155,
    h: 44,
    type: hmUI.data_type.STEP,
    font_array: numVDigits,
    align_h: hmUI.align.CENTER_H
  })
  cw(hmUI.widget.TEXT_IMG, {
    x: 205,
    y: 330,
    w: 155,
    h: 44,
    type: hmUI.data_type.BATTERY,
    font_array: numVDigits,
    unit_sc: 'num_v/percent.png',
    unit_tc: 'num_v/percent.png',
    unit_en: 'num_v/percent.png',
    align_h: hmUI.align.CENTER_H
  })
}

function render() {
  mode = dayMode()
  if (mode === 'mon') buildMonday()
  else if (mode === 'sat') buildSaturday()
  else if (mode === 'sun') buildSunday()
  else buildWeekday()
  // tiny build stamp (git commit, baked by gen_version.py at build time)
  cw(hmUI.widget.IMG, { x: 0, y: 426, src: 'version.png' })
}

WatchFace({
  onInit() {},

  build() {
    timeSensor = hmSensor.createSensor(hmSensor.id.TIME)
    render()
    // re-check the day whenever the face wakes; rebuild on a day-class
    // change, and run the Saturday timer only while the screen is on
    hmUI.createWidget(hmUI.widget.WIDGET_DELEGATE, {
      resume_call: function () {
        if (dayMode() !== mode) {
          stopSat()
          widgets.forEach(function (w) {
            hmUI.deleteWidget(w)
          })
          widgets = []
          render()
        } else if (mode === 'sat') {
          startSat()
        }
      },
      pause_call: function () {
        stopSat()
      }
    })
  },

  onDestroy() {
    stopSat()
  }
})
