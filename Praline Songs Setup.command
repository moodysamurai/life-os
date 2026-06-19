#!/bin/bash
# Double-click this file to set up the Praline soundtrack sync.
# It checks access, finds Elina's chat, runs a first sync, and turns on the
# automatic hourly updates — all in one go.

cd "$(dirname "$0")" || exit 1
DIR="$(pwd)"
CONFIG="$DIR/praline_songs_config.json"
PLIST_DST="$HOME/Library/LaunchAgents/com.pratham.pralinesongs.plist"

echo "════════════════════════════════════════════"
echo "   Praline soundtrack — setup"
echo "════════════════════════════════════════════"

# 1. Make sure we have a REAL config (with your Supabase keys). The Life OS page
#    downloads one for you. A leftover placeholder file doesn't count, so we
#    always prefer the freshly downloaded one.
config_ok() {
  [ -f "$CONFIG" ] && ! grep -q "YOUR-PROJECT" "$CONFIG" && ! grep -q "YOUR-SUPABASE" "$CONFIG"
}
if ! config_ok && [ -f "$HOME/Downloads/praline_songs_config.json" ]; then
  echo "→ Using the config the app downloaded…"
  mv -f "$HOME/Downloads/praline_songs_config.json" "$CONFIG"
fi
if ! config_ok; then
  echo "✗ Couldn't find a filled-in praline_songs_config.json."
  echo "  Ask Claude to re-save the config from the Life OS page, then run this again."
  echo; read -n1 -r -p "Press any key to close…"; exit 1
fi

# 2. Full Disk Access check — try to read the Messages DB.
if ! sqlite3 "$HOME/Library/Messages/chat.db" "SELECT 1 LIMIT 1;" >/dev/null 2>&1; then
  echo
  echo "⚠  Terminal needs permission to read your Messages."
  echo "   Opening the right settings pane now…"
  echo "   → Turn ON 'Terminal' in the list, then run this setup again."
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
  echo; read -n1 -r -p "Press any key to close…"; exit 1
fi

# 3. Detect Elina's chat + run the first sync.
echo
python3 "$DIR/praline_songs_sync.py" --setup || { echo "Setup stopped."; read -n1 -r -p "Press any key to close…"; exit 1; }

# 4. Install the hourly auto-sync.
echo
echo "→ Turning on automatic hourly updates…"
mkdir -p "$HOME/Library/LaunchAgents"
cp "$DIR/com.pratham.pralinesongs.plist" "$PLIST_DST"
launchctl unload "$PLIST_DST" 2>/dev/null
launchctl load "$PLIST_DST"

echo
echo "✓ All set! Your soundtrack will keep itself updated every hour."
echo "  Open the Praline page to see it. (Songs may take a few seconds to load.)"
echo
read -n1 -r -p "Press any key to close…"
