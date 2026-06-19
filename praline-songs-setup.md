# Praline soundtrack — iMessage → Spotify

Auto-fills the **OUR SOUNDTRACK** list on the Praline page with every Spotify
track you and Elina have sent each other on iMessage (both directions).
Everything runs locally on your Mac; the only thing that leaves is the track
list going into your own Supabase row.

## Setup — basically two clicks

Your config (Supabase keys + praline code) has already been filled in and saved
to your **Downloads** folder. So:

1. **Double-click `Praline Songs Setup.command`** in the `life-os` folder.
   It moves the config into place, finds your chat with Elina, runs a first
   sync, and turns on automatic hourly updates.
2. If it asks for **Full Disk Access**: it'll open the right settings pane —
   switch **Terminal** on, then double-click the setup file again. (macOS
   requires this by hand; it's the one thing I can't do for you.)

That's it. Open the Praline page and the songs appear under **OUR SOUNDTRACK**.
From then on it refreshes itself every hour — nothing else to do.

## If you ever need it

- **Run a sync right now:** `launchctl start com.pratham.pralinesongs`
- **Wrong chat picked / change it:** `python3 praline_songs_sync.py --setup`
- **See your conversations:** `python3 praline_songs_sync.py --chats`
- **Preview without pushing:** `python3 praline_songs_sync.py --dry-run`
- **Turn it off:** `launchctl unload ~/Library/LaunchAgents/com.pratham.pralinesongs.plist`
- **Log:** `~/life-os/.praline_songs.log`

## Notes
- Only **track** links are collected (not albums/playlists) — actual songs.
- A track you sent is tagged **Pratham** (red); one Elina sent, **Elina** (mint).
- Dedupe is by Spotify track id, so re-sharing a song won't duplicate it.
- The widget only *adds* songs (no delete button yet — ask if you want one).
- `praline_songs_config.json` is gitignored, so your key is never committed.
