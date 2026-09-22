#!/bin/bash
LABEL="com.williamcole.chimetimer"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$PLIST_DST"
echo "Uninstalled. Live files and log preserved at $HOME/Library/Application Support/ChimeTimer"
