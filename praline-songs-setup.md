# Praline soundtrack — iMessage → Spotify sync

Auto-fills the **OUR SOUNDTRACK** list on the Praline page with every Spotify
track link you and Elina have sent each other on iMessage (both directions).

The Life OS app is a static web page, so it can't read iMessage itself. This
little helper does: it reads your local Messages database on the Mac, pulls out
the Spotify links from your thread with Elina, looks up each track's title /
artist / cover art, and pushes them into the same Supabase row the Praline page
already syncs through. The widget then just shows whatever's in that row.

Everything runs locally on your Mac. Nothing leaves your machine except the
track list going to your own Supabase project.

## One-time setup (≈5 min)

### 1. Grant Full Disk Access
The Messages database is protected by macOS. Give access to whatever will run
the script (the launchd agent runs as your login session, so granting Terminal
is enough for the first manual run, and the agent inherits access):

System Settings → Privacy & Security → **Full Disk Access** → add **Terminal**
(and toggle it on). If you ever see a "permission denied reading chat.db" error,
this is why.

### 2. Fill in the config
```bash
cd ~/life-os
cp praline_songs_config.example.json praline_songs_config.json
open -e praline_songs_config.json    # or edit in any editor
```
Four values:
- **supabase_url / supabase_key** — the same ones the Praline page uses. Find
  them on the Praline page → ⚙ SETUP (or the main Settings → Cloud Sync). Use
  the Praline-dedicated project if you set one, otherwise your main sync project.
- **praline_code** — the code you typed in the Praline Setup box (e.g. `praline-23`).
- **elina_handles** — Elina's phone number(s) / iMessage email(s). Not sure which?
  Run this to list your conversations by message count:
  ```bash
  python3 praline_songs_sync.py --chats
  ```
  Copy her handle(s) into the array, exactly as shown.

### 3. Test it
```bash
python3 praline_songs_sync.py --dry-run   # shows what it found, pushes nothing
python3 praline_songs_sync.py             # actually pushes to the soundtrack
```
Open the Praline page — the songs should appear under **OUR SOUNDTRACK**.

### 4. Turn on the automatic hourly sync
```bash
bash install_praline_songs.sh
```
That installs a launchd agent that re-scans Messages at login and every hour, so
new songs show up on their own. To run it on demand:
`launchctl start com.pratham.pralinesongs`. To stop it:
`launchctl unload ~/Library/LaunchAgents/com.pratham.pralinesongs.plist`.

## Notes
- Only **track** links are collected (not albums/playlists/artists) — "songs".
- Direction: a track sent by you is tagged **Pratham** (red), one Elina sent is
  tagged **Elina** (mint). The earliest time it was shared is kept.
- Dedupe is by Spotify track id, so re-sharing the same song won't duplicate it.
- Deleting a song from the widget isn't wired up — the script only adds. Say the
  word if you want a remove button.
- Logs: `~/life-os/.praline_songs.log`.
- `praline_songs_config.json` and the metadata cache are gitignored — your key
  never gets committed.
