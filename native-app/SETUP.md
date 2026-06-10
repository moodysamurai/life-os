# Life OS — Native iOS (Capacitor) — for later

This wraps the live PWA in a native iOS shell. It loads
`https://moodysamurai.github.io/life-os`, so it auto-updates whenever you push — no rebuild
needed for content changes.

## ⚠️ Read first — the cost reality
You have a Mac + Xcode but **no paid Apple Developer account ($99/yr)**.

- With a **free** Apple ID signing team, the installed app **stops working after 7 days**.
  You must re-plug each iPhone into this Mac and re-run it from Xcode every week.
- That applies to **both** phones — your girlfriend's iPhone would need to connect to *your*
  Mac weekly. For a daily dashboard this is painful; the installed PWA has none of this.
- The **$99/yr** Apple Developer Program removes the expiry (and unlocks TestFlight, so her
  phone never needs to touch your Mac).

**Recommendation:** stay on the PWA until you're ready to pay the $99. These files are here so
that when you do, native is ~10 minutes away.

## Prerequisites (Mac)
```bash
# Xcode from the App Store, then:
xcode-select --install
sudo gem install cocoapods   # or: brew install cocoapods
node -v                      # need Node 18+
```

## One-time setup
```bash
cd /Users/pratham/life-os/native-app
mkdir -p www && echo '<meta http-equiv="refresh" content="0; url=https://moodysamurai.github.io/life-os">' > www/index.html
npm install
npx cap add ios
npx cap sync ios
npx cap open ios          # opens Xcode
```

## In Xcode
1. Select the **App** target → **Signing & Capabilities**.
2. **Team** → your personal Apple ID (free). Xcode auto-creates a provisioning profile.
3. If the bundle id `com.pratham.lifeos` is taken, change it (e.g. `com.prathamgupta.lifeos`)
   here *and* in `capacitor.config.json`.
4. Plug in the iPhone, select it as the run target, press **▶ Run**.
5. On the phone: Settings → General → VPN & Device Management → trust your developer cert.
6. Repeat the plug-in + Run step on the second iPhone.

## When you get the $99 account
- Enrol at developer.apple.com, then in Xcode the same Team gains distribution rights.
- Use **TestFlight** (Product → Archive → Distribute → TestFlight) so both of you install
  over the air, no expiry, no cable.

## Notes
- This uses `server.url` (loads the live site). Apple may reject a pure web-wrapper from the
  **public** App Store (Guideline 4.2) — fine for personal/TestFlight use.
- For a fully offline native build instead, drop `server` from `capacitor.config.json` and
  copy `index.html`, `manifest.json`, `sw.js`, and the icons into `www/` before `cap sync`.
- App icon: in Xcode, drag the 1024px version into Assets → AppIcon (generate from
  `icon-512.png` or re-render at 1024 from the icon script).
