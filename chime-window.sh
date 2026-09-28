#!/bin/sh
# Keeps ChimeTimer running only between 10:00 and 22:00. Run by com.williamcole.chimetimer.window
# at 10:00, at 22:00 and at login. Manual: chime-window.sh [start|stop|check]
LABEL=com.williamcole.chimetimer
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_="$(id -u)"
running() { launchctl print "gui/$UID_/$LABEL" >/dev/null 2>&1; }
start() { running || launchctl bootstrap "gui/$UID_" "$PLIST"; }
stop()  { running && launchctl bootout "gui/$UID_/$LABEL" || true; }
case "${1:-check}" in
  start) start ;;
  stop)  stop ;;
  check) H=$(date +%H); if [ "$H" -ge 10 ] && [ "$H" -lt 22 ]; then start; else stop; fi ;;
esac
