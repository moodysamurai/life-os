// Praline video-postcards storage worker (Cloudflare R2)
// Routes:
//   PUT    /up/<key>   — upload a clip   (requires Authorization: Bearer <AUTH_TOKEN>)
//   GET    /f/<key>    — stream a clip   (public; keys are unguessable UUIDs)
//   DELETE /f/<key>    — delete a clip   (requires Authorization: Bearer <AUTH_TOKEN>)
// Bindings needed: R2 bucket as BUCKET, secret AUTH_TOKEN

const MAX_BYTES = 26214400; // 25 MB

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,PUT,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Authorization,Content-Type,Range",
  "Access-Control-Expose-Headers": "Content-Range,Content-Length,Accept-Ranges",
  "Access-Control-Max-Age": "86400"
};

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(req.url);
    const authed = req.headers.get("Authorization") === `Bearer ${env.AUTH_TOKEN}`;

    // upload
    if (req.method === "PUT" && url.pathname.startsWith("/up/")) {
      if (!authed) return txt("unauthorized", 401);
      const key = decodeURIComponent(url.pathname.slice(4));
      if (!key || key.includes("..")) return txt("bad key", 400);
      const len = parseInt(req.headers.get("Content-Length") || "0", 10);
      if (len > MAX_BYTES) return txt("too large (25MB max)", 413);
      await env.BUCKET.put(key, req.body, {
        httpMetadata: { contentType: req.headers.get("Content-Type") || "video/mp4" }
      });
      return new Response(JSON.stringify({ ok: true, key }), {
        headers: { ...CORS, "Content-Type": "application/json" }
      });
    }

    // stream (with Range support so <video> can seek)
    if (req.method === "GET" && url.pathname.startsWith("/f/")) {
      const key = decodeURIComponent(url.pathname.slice(3));
      const range = parseRange(req.headers.get("Range"));
      const obj = await env.BUCKET.get(key, range ? { range } : undefined);
      if (!obj) return txt("not found", 404);
      const h = new Headers(CORS);
      h.set("Content-Type", obj.httpMetadata?.contentType || "video/mp4");
      h.set("Accept-Ranges", "bytes");
      h.set("Cache-Control", "public, max-age=31536000, immutable");
      if (range && obj.range) {
        const start = obj.range.offset;
        const end = start + obj.range.length - 1;
        h.set("Content-Range", `bytes ${start}-${end}/${obj.size}`);
        h.set("Content-Length", String(obj.range.length));
        return new Response(obj.body, { status: 206, headers: h });
      }
      h.set("Content-Length", String(obj.size));
      return new Response(obj.body, { status: 200, headers: h });
    }

    // delete
    if (req.method === "DELETE" && url.pathname.startsWith("/f/")) {
      if (!authed) return txt("unauthorized", 401);
      const key = decodeURIComponent(url.pathname.slice(3));
      await env.BUCKET.delete(key);
      return new Response(JSON.stringify({ ok: true }), {
        headers: { ...CORS, "Content-Type": "application/json" }
      });
    }

    return txt("not found", 404);
  }
};

function txt(msg, status) {
  return new Response(msg, { status, headers: CORS });
}

function parseRange(header) {
  if (!header) return null;
  const m = /^bytes=(\d*)-(\d*)$/.exec(header.trim());
  if (!m) return null;
  if (m[1] === "" && m[2] !== "") return { suffix: parseInt(m[2], 10) };
  const offset = parseInt(m[1], 10);
  if (m[2] === "") return { offset };
  return { offset, length: parseInt(m[2], 10) - offset + 1 };
}
