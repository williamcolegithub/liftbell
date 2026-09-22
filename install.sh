#!/bin/bash
# Deploys Chime Timer to ~/Library/Application Support/ChimeTimer and (re)starts it.
# Run this after editing chime.py or overlay.py.
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/Library/Application Support/ChimeTimer"
LABEL="com.williamcole.chimetimer"
PLIST_NAME="$LABEL.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
DOMAIN="gui/$(id -u)"

mkdir -p "$APP_DIR" "$HOME/Library/LaunchAgents"

if [ ! -d "$APP_DIR/.venv" ]; then
    echo "Creating virtualenv..."
    uv venv --quiet "$APP_DIR/.venv"
fi
echo "Installing dependencies..."
uv pip install --quiet --python "$APP_DIR/.venv/bin/python3" -r "$SRC_DIR/requirements.txt"

cp "$SRC_DIR/chime.py" "$SRC_DIR/overlay.py" "$APP_DIR/"
cp "$SRC_DIR/$PLIST_NAME" "$PLIST_DST"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
# bootout returns before the service is gone; wait for it so bootstrap does not fail.
for _ in $(seq 1 50); do
    launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1 || break
    sleep 0.2
done
launchctl bootstrap "$DOMAIN" "$PLIST_DST"

echo ""
echo "Installed. Chime Timer is running in your menu bar (look for ⏱)."
echo "It will auto-start on login."
echo "Live files: $APP_DIR"
echo "Log file:   $APP_DIR/chime_log.txt"
echo ""
echo "To uninstall: ./uninstall.sh"
