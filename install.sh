#!/bin/bash
# Deploys Chime Timer to ~/Library/Application Support/ChimeTimer and (re)starts it.
# Run this after editing chime.py or overlay.py.
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/Library/Application Support/ChimeTimer"
LABEL="com.williamcole.chimetimer"
WINDOW_LABEL="$LABEL.window"
AGENTS="$HOME/Library/LaunchAgents"
DOMAIN="gui/$(id -u)"

mkdir -p "$APP_DIR" "$HOME/Library/LaunchAgents"

if [ ! -d "$APP_DIR/.venv" ]; then
    echo "Creating virtualenv..."
    uv venv --quiet "$APP_DIR/.venv"
fi
echo "Installing dependencies..."
uv pip install --quiet --python "$APP_DIR/.venv/bin/python3" -r "$SRC_DIR/requirements.txt"

cp "$SRC_DIR/chime.py" "$SRC_DIR/overlay.py" "$SRC_DIR/chime-window.sh" "$APP_DIR/"
cp "$SRC_DIR/$LABEL.plist" "$SRC_DIR/$WINDOW_LABEL.plist" "$AGENTS/"

# Stop the app so the new code loads. bootout returns before the service is
# gone, so wait for it.
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
for _ in $(seq 1 50); do
    launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1 || break
    sleep 0.2
done

# The window agent runs chime-window.sh at load, at 10:00 and at 22:00. It
# starts the app inside 10:00-22:00 and stops it outside.
launchctl bootout "$DOMAIN/$WINDOW_LABEL" 2>/dev/null || true
for _ in $(seq 1 50); do
    launchctl print "$DOMAIN/$WINDOW_LABEL" >/dev/null 2>&1 || break
    sleep 0.2
done
launchctl bootstrap "$DOMAIN" "$AGENTS/$WINDOW_LABEL.plist"

echo ""
if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
    echo "Installed. Chime Timer is running in your menu bar (look for ⏱)."
else
    echo "Installed. It is outside 10:00-22:00, so Chime Timer starts at 10:00."
fi
echo "It runs 10:00-22:00 daily and starts at login inside that window."
echo "Live files: $APP_DIR"
echo "Log file:   $APP_DIR/chime_log.txt"
echo ""
echo "To uninstall: ./uninstall.sh"
