#!/bin/bash
# Double-click to pull in any new Spotify songs right now.
# (Runs through Terminal, which has the Messages permission, so it always works.)
cd "$(dirname "$0")" || exit 1
echo "Syncing your soundtrack…"
echo
python3 praline_songs_sync.py
echo
read -n1 -r -p "Done — press any key to close…"
