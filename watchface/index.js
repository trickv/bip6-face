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
const dateDigits = digitArray('date')
const stepDigits = digitArray('steps')
const battDigits = digitArray('batt')

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

WatchFace({
  onInit() {},

  build() {
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 0,
      y: 0,
      src: 'background.png'
    })

    // moon phase disc, right of the battery % (MOON_X/MOON_Y in
    // gen_assets.py) — the top-right corner is clipped by the rounded screen
    hmUI.createWidget(hmUI.widget.IMG_LEVEL, {
      x: 300,
      y: 376,
      image_array: moonArray,
      image_length: moonArray.length,
      type: hmUI.data_type.MOON,
      show_level: hmUI.show_level.ONLY_NORMAL
    })

    // WEEK MM/DD row — week images 64px wide + 12px gap, digits 24px, slash 24px
    hmUI.createWidget(hmUI.widget.IMG_WEEK, {
      x: 97,
      y: 52,
      week_en: weekArray,
      week_sc: weekArray,
      week_tc: weekArray
    })

    hmUI.createWidget(hmUI.widget.IMG_DATE, {
      month_startX: 173,
      month_startY: 52,
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

    // HH:MM — digits are 60px wide, colon 35px, so 4*60 + 35 = 275 total
    hmUI.createWidget(hmUI.widget.IMG_TIME, {
      hour_zero: 1,
      hour_startX: 57,
      hour_startY: 108,
      hour_array: timeDigits,
      hour_unit_sc: 'time/colon.png',
      hour_unit_tc: 'time/colon.png',
      hour_unit_en: 'time/colon.png',
      minute_follow: 1,
      minute_zero: 1,
      minute_array: timeDigits
    })

    hmUI.createWidget(hmUI.widget.IMG, {
      x: 169,
      y: 252,
      src: 'label_steps.png'
    })

    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 0,
      y: 280,
      w: SCREEN_W,
      h: 44,
      type: hmUI.data_type.STEP,
      font_array: stepDigits,
      align_h: hmUI.align.CENTER_H
    })

    hmUI.createWidget(hmUI.widget.IMG, {
      x: 159,
      y: 344,
      src: 'label_batt.png'
    })

    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
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
  },

  onDestroy() {}
})
