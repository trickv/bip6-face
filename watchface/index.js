const SCREEN_W = 390

const timeDigits = [
  'time/0.png',
  'time/1.png',
  'time/2.png',
  'time/3.png',
  'time/4.png',
  'time/5.png',
  'time/6.png',
  'time/7.png',
  'time/8.png',
  'time/9.png'
]

const stepDigits = [
  'steps/0.png',
  'steps/1.png',
  'steps/2.png',
  'steps/3.png',
  'steps/4.png',
  'steps/5.png',
  'steps/6.png',
  'steps/7.png',
  'steps/8.png',
  'steps/9.png'
]

const battDigits = [
  'batt/0.png',
  'batt/1.png',
  'batt/2.png',
  'batt/3.png',
  'batt/4.png',
  'batt/5.png',
  'batt/6.png',
  'batt/7.png',
  'batt/8.png',
  'batt/9.png'
]

WatchFace({
  onInit() {},

  build() {
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 0,
      y: 0,
      src: 'background.png'
    })

    // HH:MM — digits are 60px wide, colon 26px, so 2*60 + 26 + 2*60 = 266 total
    hmUI.createWidget(hmUI.widget.IMG_TIME, {
      hour_zero: 1,
      hour_startX: (SCREEN_W - 266) / 2,
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
      x: 155,
      y: 258,
      src: 'label_steps.png'
    })

    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 0,
      y: 286,
      w: SCREEN_W,
      h: 40,
      type: hmUI.data_type.STEP,
      font_array: stepDigits,
      align_h: hmUI.align.CENTER_H
    })

    hmUI.createWidget(hmUI.widget.IMG, {
      x: 141,
      y: 344,
      src: 'label_batt.png'
    })

    hmUI.createWidget(hmUI.widget.TEXT_IMG, {
      x: 0,
      y: 372,
      w: SCREEN_W,
      h: 40,
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
