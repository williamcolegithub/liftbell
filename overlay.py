#!/usr/bin/env python3
"""Floating rep counter overlay. Launched by chime.py after each chime.

Usage: overlay.py [exercise name]
"""
import sys

import objc
from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered, NSBezierPath, NSButton, NSBezelStyleInline, NSColor,
    NSEvent, NSEventTypeApplicationDefined, NSFloatingWindowLevel,
    NSFont, NSFontWeightBold, NSFontWeightMedium, NSScreen,
    NSSpeechSynthesizer, NSTextField, NSTextAlignmentCenter, NSWindow,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSObject, NSPoint, NSTimer


class ClickableWindow(NSWindow):
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True

    def cancelOperation_(self, sender):  # Escape key closes overlay
        self.delegate().closeOverlay_(sender)


class FirstClickButton(NSButton):
    """Registers the click even when the overlay isn't the active app."""
    def acceptsFirstMouse_(self, event):
        return True


class CircleButton(FirstClickButton):
    """FirstClickButton with a filled circle behind the title."""
    def drawRect_(self, rect):
        COLOR_CLOSE_BG.setFill()
        NSBezierPath.bezierPathWithOvalInRect_(self.bounds()).fill()
        objc.super(CircleButton, self).drawRect_(rect)

REPS = 12
READY_SECONDS = 5
PHASE_SECONDS = 0.5
SPEECH_RATE_NAME = 200   # words per minute for the exercise name
SPEECH_RATE_BEAT = 340   # fast enough to finish each cue inside one beat
PHASES = [
    ("DOWN", "direction"),
    ("3", "count"),
    ("2", "count"),
    ("1", "count"),
    ("UP", "direction"),
    ("1", "count"),
    ("2", "count"),
]

COLOR_DOWN = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.4, 0.8, 1.0, 1.0)
COLOR_UP = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.6, 0.3, 1.0)
COLOR_COUNT = NSColor.whiteColor()
COLOR_BG = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.08, 0.12, 0.88)
COLOR_MUTED = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.4)
COLOR_ACTIVE = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.4, 1.0, 0.6, 1.0)
COLOR_CLOSE_BG = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.18)


def make_label(frame, size, weight=NSFontWeightBold):
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setAlignment_(NSTextAlignmentCenter)
    label.setFont_(NSFont.systemFontOfSize_weight_(size, weight))
    label.setTextColor_(NSColor.whiteColor())
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    return label


class Overlay(NSObject):
    def initWithReps_exercise_(self, reps, exercise):
        self = objc.super(Overlay, self).init()
        if self is None:
            return None
        self.exercise = exercise
        self.rep = 0
        self.phase = 0
        self.total_reps = reps
        self.ready_ticks = READY_SECONDS
        self.audio_on = True
        self.window = None
        self.tick_timer = None
        self.exercise_label = None
        self.rep_label = None
        self.phase_label = None
        self.sound_btn = None
        self.synth = NSSpeechSynthesizer.alloc().initWithVoice_(None)
        return self

    def showWindow(self):
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        screen = NSScreen.mainScreen().frame()
        w, h = 320, 280
        x = (screen.size.width - w) / 2
        y = (screen.size.height - h) / 2 + 100

        self.window = ClickableWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ((x, y), (w, h)), NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        self.window.setLevel_(NSFloatingWindowLevel + 1)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(COLOR_BG)
        self.window.setHasShadow_(True)
        self.window.setDelegate_(self)
        self.window.setAcceptsMouseMovedEvents_(True)

        cv = self.window.contentView()
        cv.setWantsLayer_(True)
        cv.layer().setCornerRadius_(20)
        cv.layer().setMasksToBounds_(True)

        # Labels first, buttons last, so the buttons sit on top for clicks.
        self.exercise_label = make_label(((0, 172), (w, 40)), 24)
        self.exercise_label.setStringValue_(self.exercise)
        self.exercise_label.setTextColor_(COLOR_ACTIVE)

        self.rep_label = make_label(((0, 138), (w, 34)), 20, NSFontWeightMedium)
        self.rep_label.setStringValue_("Get ready...")

        self.phase_label = make_label(((0, 12), (w, 120)), 64)
        self.phase_label.setStringValue_(str(self.ready_ticks))
        self.phase_label.setTextColor_(COLOR_MUTED)

        cv.addSubview_(self.exercise_label)
        cv.addSubview_(self.rep_label)
        cv.addSubview_(self.phase_label)

        close_btn = CircleButton.alloc().initWithFrame_(((w - 68, h - 68), (60, 60)))
        close_btn.setTitle_("✕")
        close_btn.setBezelStyle_(NSBezelStyleInline)
        close_btn.setBordered_(False)
        close_btn.setFont_(NSFont.systemFontOfSize_weight_(26, NSFontWeightMedium))
        close_btn.setTarget_(self)
        close_btn.setAction_(b"closeOverlay:")
        close_btn.setContentTintColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.9))
        cv.addSubview_(close_btn)

        self.sound_btn = FirstClickButton.alloc().initWithFrame_(((8, h - 48), (40, 40)))
        self.sound_btn.setTitle_("🔊" if self.audio_on else "🔇")
        self.sound_btn.setBezelStyle_(NSBezelStyleInline)
        self.sound_btn.setBordered_(False)
        self.sound_btn.setFont_(NSFont.systemFontOfSize_(22))
        self.sound_btn.setTarget_(self)
        self.sound_btn.setAction_(b"toggleSound:")
        cv.addSubview_(self.sound_btn)

        self.window.makeKeyAndOrderFront_(None)

        if self.exercise:
            self._speak(self.exercise, SPEECH_RATE_NAME)
        self._start_timer(1.0)
        app.run()

    @objc.python_method
    def _start_timer(self, interval):
        if self.tick_timer is not None:
            self.tick_timer.invalidate()
        self.tick_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval, self, b"tick:", None, True
        )

    @objc.python_method
    def _shutdown(self):
        self.tick_timer.invalidate()
        self.window.close()
        app = NSApplication.sharedApplication()
        app.stop_(None)
        e = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            NSEventTypeApplicationDefined, NSPoint(0, 0), 0, 0, 0, None, 0, 0, 0
        )
        app.postEvent_atStart_(e, True)

    @objc.python_method
    def _speak(self, text, rate=SPEECH_RATE_BEAT):
        if not self.audio_on:
            return
        # Cut off whatever is still playing so every cue lands on its beat.
        self.synth.stopSpeaking()
        self.synth.setRate_(rate)
        self.synth.startSpeakingString_(text)

    @objc.typedSelector(b"v@:@")
    def toggleSound_(self, sender):
        self.audio_on = not self.audio_on
        self.sound_btn.setTitle_("🔊" if self.audio_on else "🔇")

    @objc.typedSelector(b"v@:@")
    def closeOverlay_(self, sender):
        self._shutdown()

    @objc.typedSelector(b"v@:@")
    def tick_(self, timer):
        if self.ready_ticks > 0:
            self.ready_ticks -= 1
            if self.ready_ticks > 0:
                self.phase_label.setStringValue_(str(self.ready_ticks))
            else:
                self.rep_label.setStringValue_(f"Rep 1 / {self.total_reps}")
                self.phase_label.setStringValue_("")
                self._start_timer(PHASE_SECONDS)
            return

        if self.rep >= self.total_reps:
            self._shutdown()
            return

        text, kind = PHASES[self.phase]

        if kind == "direction":
            self.rep_label.setStringValue_(f"Rep {self.rep + 1} / {self.total_reps}")

        self.phase_label.setStringValue_(text)
        self._speak(text.lower())

        if text == "DOWN":
            self.phase_label.setTextColor_(COLOR_DOWN)
        elif text == "UP":
            self.phase_label.setTextColor_(COLOR_UP)
        else:
            self.phase_label.setTextColor_(COLOR_COUNT)

        self.phase += 1
        if self.phase >= len(PHASES):
            self.phase = 0
            self.rep += 1


if __name__ == "__main__":
    exercise = sys.argv[1] if len(sys.argv) > 1 else ""
    overlay = Overlay.alloc().initWithReps_exercise_(REPS, exercise)
    overlay.showWindow()
