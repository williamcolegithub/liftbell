#!/usr/bin/env python3
import datetime
import os
import random
import subprocess
import threading
import time

import rumps

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "chime_log.txt")
STATE_FILE = os.path.join(APP_DIR, "state.txt")
SOUND_FILE = "/System/Library/Sounds/Glass.aiff"
VOLUME = 3.0
INTERVAL_SECONDS = 30 * 60
OVERLAY_DELAY = 20
OVERLAY_SCRIPT = os.path.join(APP_DIR, "overlay.py")
PYTHON = os.path.join(APP_DIR, ".venv", "bin", "python3")
EXERCISES = ["Wrist curls", "Bicep curls", "Overhead press", "Bench press"]


class ChimeApp(rumps.App):
    def __init__(self):
        super().__init__(f"⏱ {INTERVAL_SECONDS // 60:02d}:00", quit_button="Quit")
        self.toggle_item = rumps.MenuItem("Turn off", callback=self.toggle_timer)
        self.responded_item = rumps.MenuItem("I responded", callback=self.log_response)
        self.view_log_item = rumps.MenuItem("View log", callback=self.view_log)
        self.reset_item = rumps.MenuItem("Reset timer", callback=self.reset_timer)
        self.status_item = rumps.MenuItem("Cycles today: 0 / 0")
        self.status_item.set_callback(None)
        self.menu = [self.toggle_item, self.responded_item, self.view_log_item, self.reset_item, None, self.status_item]
        self.enabled = self._load_enabled()
        self.overlay_timer = None
        self.exercise_bag = []
        self.today = datetime.date.today()
        self.chimes_today = 0
        self.responses_today = 0
        self._refresh_today_counts()
        self._update_status()
        self.next_chime_at = time.monotonic() + INTERVAL_SECONDS
        if not self.enabled:
            self.toggle_item.title = "Turn on"
            self.title = "⏱ off"
        self.tick_timer = rumps.Timer(self.tick, 1)
        self.tick_timer.start()

    def _load_enabled(self):
        try:
            with open(STATE_FILE) as f:
                return f.read().strip() != "off"
        except OSError:
            return True

    def _save_enabled(self):
        with open(STATE_FILE, "w") as f:
            f.write("on" if self.enabled else "off")

    def _roll_day_if_needed(self):
        today = datetime.date.today()
        if today != self.today:
            self.today = today
            self.chimes_today = 0
            self.responses_today = 0

    def _refresh_today_counts(self):
        if not os.path.exists(LOG_FILE):
            return
        today_str = self.today.isoformat()
        with open(LOG_FILE) as f:
            for line in f:
                if line.startswith(today_str):
                    self.responses_today += 1

    def _update_status(self):
        self.status_item.title = f"Cycles today: {self.responses_today} / {self.chimes_today}"

    def tick(self, _):
        if not self.enabled:
            return
        remaining = self.next_chime_at - time.monotonic()
        if remaining <= 0:
            self._fire_chime()
            self.next_chime_at = time.monotonic() + INTERVAL_SECONDS
            remaining = INTERVAL_SECONDS
        mins, secs = divmod(int(remaining + 0.5), 60)
        self.title = f"⏱ {mins:02d}:{secs:02d}"

    def _fire_chime(self):
        self._roll_day_if_needed()
        subprocess.Popen(["afplay", "-v", str(VOLUME), SOUND_FILE])
        self.chimes_today += 1
        self._update_status()
        self.overlay_timer = threading.Timer(OVERLAY_DELAY, self._launch_overlay)
        self.overlay_timer.daemon = True
        self.overlay_timer.start()

    def _next_exercise(self):
        # Deal every exercise once before reshuffling, so none repeats back to back.
        if not self.exercise_bag:
            self.exercise_bag = random.sample(EXERCISES, len(EXERCISES))
        return self.exercise_bag.pop()

    def _launch_overlay(self):
        if self.enabled:
            subprocess.Popen([PYTHON, OVERLAY_SCRIPT, self._next_exercise()])

    def toggle_timer(self, _):
        self.enabled = not self.enabled
        self._save_enabled()
        if not self.enabled and self.overlay_timer is not None:
            self.overlay_timer.cancel()
        if self.enabled:
            self.toggle_item.title = "Turn off"
            self.next_chime_at = time.monotonic() + INTERVAL_SECONDS
        else:
            self.toggle_item.title = "Turn on"
            self.title = "⏱ off"

    def reset_timer(self, _):
        self.next_chime_at = time.monotonic() + INTERVAL_SECONDS

    def log_response(self, _):
        self._roll_day_if_needed()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(timestamp + "\n")
        self.responses_today += 1
        self._update_status()

    def view_log(self, _):
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, "a").close()
        subprocess.Popen(["open", LOG_FILE])


if __name__ == "__main__":
    ChimeApp().run()
