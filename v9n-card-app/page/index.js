// v9n card: logo screen, then swipe right through QR codes
// (v9n.us -> trick.vanstaveren.us -> vCard with cell number).
// Swipe left goes back a card; the side button exits as usual.
import * as hmUI from '@zos/ui'
import {
  onGesture,
  offGesture,
  GESTURE_LEFT,
  GESTURE_RIGHT
} from '@zos/interaction'

const CARDS = ['card0.png', 'card1.png', 'card2.png', 'card3.png']
let idx = 0
let card = null

function show(i) {
  idx = (i + CARDS.length) % CARDS.length
  card.setProperty(hmUI.prop.MORE, { x: 0, y: 0, src: CARDS[idx] })
}

function gesture(event) {
  if (event === GESTURE_RIGHT) {
    show(idx + 1)
    return true // keep swipe-right from exiting the app
  }
  if (event === GESTURE_LEFT) {
    show(idx - 1)
    return true
  }
  return false
}

Page({
  onInit() {},

  build() {
    try {
      hmUI.setStatusBarVisible(false) // full-bleed cards, no title bar
    } catch (e) {}
    card = hmUI.createWidget(hmUI.widget.IMG, { x: 0, y: 0, src: CARDS[0] })
    onGesture({ callback: gesture })
  },

  onDestroy() {
    try {
      offGesture()
    } catch (e) {}
  }
})
