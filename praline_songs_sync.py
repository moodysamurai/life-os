#!/usr/bin/env python3
"""
Praline soundtrack sync — pulls every Spotify track link from your iMessage
thread with Elina (both directions) and pushes them into the Praline Supabase
row so the "OUR SOUNDTRACK" widget on the Life OS Praline page fills itself in.

Runs automatically via launchd once installed (see praline-songs-setup.md).
Stdlib only — no pip installs needed.

Usage:
  python3 praline_songs_sync.py            # normal sync (read msgs, push new songs)
  python3 praline_songs_sync.py --chats    # list your conversations to find Elina's handle
  python3 praline_songs_sync.py --dry-run  # show what WOULD be pushed, don't write
"""
import json, os, re, sqlite3, shutil, sys, tempfile, time, urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "praline_songs_config.json")
CACHE_PATH = os.path.join(HERE, ".praline_songs_cache.json")
CHAT_DB = os.path.expanduser("~/Library/Messages/chat.db")
APPLE_EPOCH = 978307200  # seconds between 1970-01-01 and 2001-01-01

# match open.spotify.com/track/<id> (with optional /intl-xx/ and query) or spotify:track:<id>
TRACK_RE = re.compile(r"(?:open\.spotify\.com/(?:intl-[a-z]{2}/)?track/|spotify:track:)([A-Za-z0-9]{22})")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"Missing config. Create {CONFIG_PATH} (see praline-songs-setup.md).")
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_cache():
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(c):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(c, f)
    except Exception:
        pass


def open_db_readonly():
    """Copy the DB (+wal/shm) to a temp dir so we never lock the live Messages DB."""
    if not os.path.exists(CHAT_DB):
        sys.exit(f"Cannot find {CHAT_DB}. Is this a Mac with Messages set up?")
    tmp = tempfile.mkdtemp(prefix="praline_msg_")
    dst = os.path.join(tmp, "chat.db")
    try:
        shutil.copy2(CHAT_DB, dst)
        for ext in ("-wal", "-shm"):
            if os.path.exists(CHAT_DB + ext):
                shutil.copy2(CHAT_DB + ext, dst + ext)
    except PermissionError:
        sys.exit("Permission denied reading chat.db. Grant Full Disk Access to the "
                 "program running this script (Terminal / python) in System Settings → "
                 "Privacy & Security → Full Disk Access.")
    conn = sqlite3.connect(dst)
    conn.row_factory = sqlite3.Row
    return conn, tmp


def apple_date_to_ms(val):
    if val is None:
        return None
    val = int(val)
    secs = val / 1e9 if val > 1e12 else float(val)  # ns (modern) vs s (legacy)
    return int((secs + APPLE_EPOCH) * 1000)


def decode_attributed_body(blob):
    """Newer macOS stores message text in a binary attributedBody blob; the URL
    still lives there as plain ASCII, so a lenient decode + regex finds it."""
    if not blob:
        return ""
    try:
        return blob.decode("utf-8", "ignore")
    except Exception:
        try:
            return blob.decode("latin-1", "ignore")
        except Exception:
            return ""


def top_chats(conn, limit=40):
    """Conversations sorted by message count: [(handle, count, last_ms), ...]."""
    q = """
    SELECT h.id AS handle, COUNT(m.ROWID) AS n, MAX(m.date) AS last
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE h.id IS NOT NULL AND h.id != ''
    GROUP BY h.id ORDER BY n DESC LIMIT ?;
    """
    out = []
    for r in conn.execute(q, (limit,)):
        out.append((r["handle"], r["n"], apple_date_to_ms(r["last"])))
    return out


def list_chats(conn):
    """Print conversations so you can identify Elina's handle(s)."""
    print(f"{'MESSAGES':>9}  {'LAST':>12}  HANDLE")
    print("-" * 60)
    for handle, n, ms in top_chats(conn):
        when = time.strftime("%Y-%m-%d", time.localtime(ms / 1000)) if ms else "?"
        print(f"{n:>9}  {when:>12}  {handle}")
    print("\nCopy Elina's handle(s) into elina_handles in praline_songs_config.json.")


def detect_contact_handles(name="elina"):
    """Best-effort: pull phone/email for a contact whose first name matches `name`
    from the macOS Contacts database. Returns a list (may be empty)."""
    import glob
    handles = []
    pattern = os.path.expanduser(
        "~/Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb")
    for db in glob.glob(pattern) + [os.path.expanduser(
            "~/Library/Application Support/AddressBook/AddressBook-v22.abcddb")]:
        if not os.path.exists(db):
            continue
        try:
            c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            rows = c.execute("""
                SELECT p.ZFULLNUMBER, e.ZADDRESS
                FROM ZABCDRECORD r
                LEFT JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.Z_PK
                LEFT JOIN ZABCDEMAILADDRESS e ON e.ZOWNER = r.Z_PK
                WHERE LOWER(r.ZFIRSTNAME) = ?
            """, (name.lower(),)).fetchall()
            for ph, em in rows:
                if ph:
                    handles.append(re.sub(r"[\s()\-]", "", ph))
                if em:
                    handles.append(em.strip())
            c.close()
        except Exception:
            pass
    # dedupe, keep order
    seen, out = set(), []
    for h in handles:
        if h and h not in seen:
            seen.add(h); out.append(h)
    return out


def interactive_setup(cfg, conn):
    """Fill in elina_handles with as little typing as possible."""
    print("\n— Praline soundtrack setup —\n")
    if not cfg.get("supabase_url") or "YOUR-" in str(cfg.get("supabase_key", "")):
        print("⚠  Supabase keys aren't filled in yet. Use the config file that the")
        print("   Life OS page downloaded for you (praline_songs_config.json).")
        return False

    detected = detect_contact_handles("elina")
    chats = top_chats(conn, 8)
    handle_set = {h for h, _, _ in chats}

    chosen = []
    # If a contact named Elina maps onto an actual conversation, use it automatically.
    auto = [h for h in detected if h in handle_set] or detected
    if auto:
        print("Found Elina in your Contacts:", ", ".join(auto))
        ans = input("Use these? [Y/n] ").strip().lower()
        if ans in ("", "y", "yes"):
            chosen = auto

    if not chosen:
        print("\nYour most active conversations:")
        for i, (h, n, ms) in enumerate(chats, 1):
            when = time.strftime("%Y-%m-%d", time.localtime(ms / 1000)) if ms else "?"
            print(f"  {i}. {h:30}  {n} msgs   (last {when})")
        pick = input("\nWhich number is Elina? (or paste her handle) ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(chats):
            chosen = [chats[int(pick) - 1][0]]
        elif pick:
            chosen = [pick]

    if not chosen:
        print("No handle chosen — aborting setup.")
        return False

    cfg["elina_handles"] = chosen
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"\n✓ Saved Elina's handle(s): {', '.join(chosen)}")
    return True


def fetch_messages_for_handles(conn, handles):
    """All messages (both directions) in any chat that includes one of Elina's handles."""
    if not handles:
        sys.exit("No elina_handles configured. Run with --chats to find them.")
    marks = ",".join("?" * len(handles))
    # chats that contain any of her handles
    chat_rows = conn.execute(f"""
        SELECT DISTINCT chj.chat_id
        FROM chat_handle_join chj
        JOIN handle h ON chj.handle_id = h.ROWID
        WHERE h.id IN ({marks})
    """, handles).fetchall()
    chat_ids = [r["chat_id"] for r in chat_rows]
    if not chat_ids:
        return []
    cmarks = ",".join("?" * len(chat_ids))
    rows = conn.execute(f"""
        SELECT m.text, m.attributedBody, m.is_from_me, m.date
        FROM message m
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        WHERE cmj.chat_id IN ({cmarks})
        ORDER BY m.date ASC
    """, chat_ids).fetchall()
    return rows


def http_get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PralineSync"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def resolve_track(track_id, cache):
    """Return {title, artist, art} using Spotify oEmbed (+ page <title> for artist)."""
    if track_id in cache:
        return cache[track_id]
    url = f"https://open.spotify.com/track/{track_id}"
    title, artist, art = "", "", ""
    # oEmbed: reliable title + album thumbnail, no auth
    try:
        oe = json.loads(http_get("https://open.spotify.com/oembed?url=" + urllib.parse.quote(url, safe="")))
        title = (oe.get("title") or "").strip()
        art = oe.get("thumbnail_url") or ""
    except Exception:
        pass
    # page <title> is reliably "<Song> - song [and lyrics] by <Artist> | Spotify"
    try:
        html = http_get(url)
        m = re.search(r"<title>(.+?) - song(?: and lyrics)? by (.+?) \| Spotify", html)
        if m:
            if not title:
                title = m.group(1).strip()
            artist = m.group(2).strip()
        if not artist:
            md = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if md:
                artist = md.group(1).split("·")[0].strip()
    except Exception:
        pass
    meta = {"title": title or "Unknown track", "artist": artist, "art": art}
    cache[track_id] = meta
    return meta


def supa_get(cfg, row_id):
    url = f"{cfg['supabase_url'].rstrip('/')}/rest/v1/lifeos_sync?id=eq.{urllib.parse.quote(row_id)}&select=data"
    req = urllib.request.Request(url, headers={"apikey": cfg["supabase_key"],
                                               "Authorization": "Bearer " + cfg["supabase_key"]})
    with urllib.request.urlopen(req, timeout=15) as r:
        rows = json.loads(r.read().decode())
    return rows[0]["data"] if rows else {}


def supa_push(cfg, row_id, data):
    url = f"{cfg['supabase_url'].rstrip('/')}/rest/v1/lifeos_sync"
    body = json.dumps({"id": row_id, "data": data,
                       "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "apikey": cfg["supabase_key"], "Authorization": "Bearer " + cfg["supabase_key"],
        "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"})
    urllib.request.urlopen(req, timeout=20).read()


def main():
    args = set(sys.argv[1:])
    cfg = load_config()

    conn, tmp = open_db_readonly()
    try:
        if "--chats" in args:
            list_chats(conn)
            return
        if "--setup" in args:
            if not interactive_setup(cfg, conn):
                return
            cfg = load_config()  # reload with the handles we just saved
        handles = cfg.get("elina_handles", [])
        # auto-fallback: if no handle configured, use the single most-active conversation
        if not handles:
            chats = top_chats(conn, 1)
            if chats:
                handles = [chats[0][0]]
                print(f"No handle configured — defaulting to most active chat: {handles[0]}")
        rows = fetch_messages_for_handles(conn, handles)
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)

    # newest send wins for direction/timestamp; first appearance keeps earliest known
    found = {}  # track_id -> {by, ts}
    for r in rows:
        text = r["text"] or decode_attributed_body(r["attributedBody"])
        if not text or "spotify" not in text.lower():
            continue
        for tid in TRACK_RE.findall(text):
            ts = apple_date_to_ms(r["date"]) or 0
            by = "a" if r["is_from_me"] else "b"
            if tid not in found or ts < found[tid]["ts"]:  # keep the FIRST time it was shared
                found[tid] = {"by": by, "ts": ts}

    if not found:
        print("No Spotify track links found in that thread yet.")
        return

    cache = load_cache()
    songs = []
    for tid, info in found.items():
        meta = resolve_track(tid, cache)
        songs.append({"id": tid, "url": f"https://open.spotify.com/track/{tid}",
                      "title": meta["title"], "artist": meta["artist"], "art": meta["art"],
                      "by": info["by"], "ts": info["ts"]})
    save_cache(cache)
    songs.sort(key=lambda s: s["ts"])
    print(f"Found {len(songs)} unique track(s) in the thread.")

    row_id = "praline_" + cfg["praline_code"].strip().lower()
    if "--dry-run" in args:
        for s in songs:
            who = "Pratham" if s["by"] == "a" else "Elina"
            print(f"  [{who:>7}] {s['title']} — {s['artist']}")
        print(f"\n(dry run — would push to row {row_id})")
        return

    # merge into the live doc: union by id, existing songs win on conflict.
    # Never re-add a track the user deleted in the widget (removedSongs).
    data = supa_get(cfg, row_id)
    existing = data.get("songs") or []
    removed = set(data.get("removedSongs") or [])
    have = {s.get("id") for s in existing}
    merged = existing + [s for s in songs if s["id"] not in have and s["id"] not in removed]
    new_count = len(merged) - len(existing)
    data["songs"] = merged
    supa_push(cfg, row_id, data)
    print(f"Pushed. {new_count} new song(s) added; {len(merged)} total in the soundtrack.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP error talking to Supabase: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")
