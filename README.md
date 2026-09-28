# LiftBell

The bell rings every 30 minutes. You lift.

A macOS menu bar timer that chimes on the half hour and pops up a rep
counter for one short strength set at your desk.

<p align="center">
  <img src="docs/overlay.png" width="368" alt="LiftBell overlay counting rep 6 of 12 for bicep curls">
</p>

## What it does

- Runs 10:00 to 22:00. A schedule agent starts it at 10:00 and stops it at 22:00.
- Menu bar countdown. Chimes when it reaches zero, then restarts.
- 5 seconds after the chime, a floating overlay opens with one exercise:
  wrist curls, bicep curls, overhead press, or bench press. Each exercise
  comes up once before any repeats.
- The overlay shows the exercise for 15 seconds, then counts 12 reps. Each
  rep is DOWN 3 2 1 UP 1 2, half a second
  per beat, spoken aloud. Close it with the X or Escape.
- Menu items: turn off, I responded, view log, reset timer, cycles today.
  Turn off lasts until the next 10:00 start.

## Install

Needs macOS and [uv](https://docs.astral.sh/uv/).

```
./install.sh
```

This copies the scripts to `~/Library/Application Support/ChimeTimer`,
creates a virtualenv there, installs two launch agents, and starts the app
if it is between 10:00 and 22:00. Rerun `install.sh` after editing
`chime.py` or `overlay.py`.

```
./uninstall.sh
```

Stops the app and removes both launch agents. The live folder and log stay.

## Files

- `chime.py`: menu bar app, built on [rumps](https://github.com/jaredks/rumps).
- `overlay.py`: rep counter window, built on PyObjC.
- `chime-window.sh`: starts or stops the app depending on the hour.
- `com.williamcole.chimetimer.plist`: launch agent for the app.
- `com.williamcole.chimetimer.window.plist`: launch agent that runs
  `chime-window.sh` at login, 10:00 and 22:00.

Paths in the plists are hardcoded to the author's home folder. Edit them if
you are not the author.
