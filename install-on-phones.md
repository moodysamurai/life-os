# Life OS — Install on Your Phones

Site: **https://moodysamurai.github.io/life-os**

Your app is now a proper installable PWA: paper-theme splash screen, real 受付係 home-screen
icon, fullscreen (no browser bars), works offline. No App Store needed.

---

## 1 · Install on each iPhone (you + your girlfriend)

Must be done in **Safari** (Chrome on iOS can't install to the home screen).

1. Open **https://moodysamurai.github.io/life-os** in Safari.
2. Tap the **Share** button (square with an up-arrow, bottom center).
3. Scroll down → **Add to Home Screen**.
4. Name stays **受付係** → tap **Add**.
5. Close Safari. Launch it from the home-screen icon — it opens fullscreen like a native app.

Do this on both phones.

---

## 2 · Shared data (both phones see the same Life OS)

Installing only gives the app *shell*. To make both phones show the **same** tasks, trips,
goals and money, each phone needs the cloud-sync settings entered once.

On iPhone there's no developer console, so use the **in-app Settings**, not the console paste:

1. In the app, tap the **⚙ (gear)** in the top-right nav.
2. Under **Cloud Sync → Configure**, enter the three values from your private
   `life-os-device-setup.md` (Option B → "CLOUD SYNC"):
   - **Project URL**
   - **Anon Key**
   - **Sync ID**  ← *use the same Sync ID on both phones — that's what makes them shared.*
3. Save. Data syncs down automatically within a few seconds.

### Optional — full feature parity (AI suggestions, Apple Calendar, image tools)
If you want the girlfriend's phone to also have the AI features, enter these from the same
`life-os-device-setup.md` (Option B):
- **Claude API key** → Settings → Set Key
- **imgbb / remove.bg keys** (image tools)
- **Apple Calendar** → Configure (only if she wants *your* calendar; otherwise skip)

> Keep `life-os-device-setup.md` private — it holds live keys. For just "same data on both
> phones," only the three Cloud Sync values are required.

---

## 3 · Notes
- **Updates** flow automatically — every time you push to the repo, both installed apps pick
  up the new version on next launch (service worker is network-first).
- If an old version sticks, on the phone: delete the home-screen icon, reopen the site in
  Safari, re-add. (Cache version was bumped to `v4` this deploy.)
- The icon may look like a screenshot for ~a minute after first add while iOS fetches the
  new `apple-touch-icon.png`; the proper 受付係 mark appears shortly.
