# Video Postcards — one-time Cloudflare R2 setup

Storage for Praline video postcards. Free tier: 10 GB storage, zero egress — roughly a decade of postcards. Takes ~10 minutes. Elina does NOT need to do any of this; she only pastes the worker URL + token into her Praline setup panel.

## 1. Create the R2 bucket

1. Go to https://dash.cloudflare.com → R2 Object Storage (you may need to add a card for identity verification — free tier stays free).
2. Create bucket → name it `praline-postcards` → Create.

## 2. Create the worker

1. Dashboard → Workers & Pages → Create → Worker.
2. Name it `praline-postcards` → Deploy (the hello-world placeholder).
3. Edit code → replace everything with the contents of `postcards-worker.js` (in this folder) → Deploy.

## 3. Bind the bucket + set the secret

1. Worker → Settings → Bindings → Add → R2 bucket:
   - Variable name: `BUCKET`
   - Bucket: `praline-postcards`
2. Settings → Variables and Secrets → Add → type **Secret**:
   - Name: `AUTH_TOKEN`
   - Value: any long random string, e.g. run `openssl rand -hex 24` in Terminal
3. Deploy again if prompted.

## 4. Connect the app

1. Copy the worker URL (looks like `https://praline-postcards.<your-subdomain>.workers.dev`).
2. In life-os → PRALINE → ⚙ SETUP → "VIDEO POSTCARDS STORAGE": paste the worker URL and the AUTH_TOKEN value.
3. Send Elina the same URL + token (e.g. over Signal/WhatsApp) — she pastes them into her setup panel once. These are stored only in each browser's localStorage, never synced through Supabase.

## Notes

- Clips up to 25 MB each, max 3 per postcard. Postcard metadata (captions, dates, who sent what) syncs through the existing praline Supabase doc, so it appears live on both ends.
- Deleting a postcard in the app also deletes its clips from R2.
- If the token ever leaks, just change the AUTH_TOKEN secret — old links keep playing (playback is public via unguessable UUID keys), but nobody can upload or delete without the new token.
