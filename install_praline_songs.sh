#!/bin/bash
# Installs the Praline soundtrack sync as a launchd agent that runs every hour.
# Run once:  bash ~/life-os/install_praline_songs.sh
set -e

PLIST_SRC="/Users/pratham/life-os/com.pratham.pralinesongs.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.pratham.pralinesongs.plist"
CONFIG="/Users/pratham/life-os/praline_songs_config.json"

if [ ! -f "$CONFIG" ]; then
  echo "✗ $CONFIG not found."
  echo "  Copy praline_songs_config.example.json → praline_songs_config.json and fill it in first."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DST"

# reload if already loaded
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"

echo "✓ Installed. The sync now runs at login and every hour."
echo "  Log:        /Users/pratham/life-os/.praline_songs.log"
echo "  Run now:    launchctl start com.pratham.pralinesongs"
echo "  Stop/remove: launchctl unload \"$PLIST_DST\""
