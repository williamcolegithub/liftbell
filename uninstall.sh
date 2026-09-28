#!/bin/bash
LABEL="com.williamcole.chimetimer"
AGENTS="$HOME/Library/LaunchAgents"
launchctl bootout "gui/$(id -u)/$LABEL.window" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$AGENTS/$LABEL.plist" "$AGENTS/$LABEL.window.plist"
echo "Uninstalled. Live files and log preserved at $HOME/Library/Application Support/ChimeTimer"
