"""Build the stand-alone home-screen version of the game into docs/ (served by GitHub Pages).

index.html at the repo root is the single source: it is written as page content
(no <html>/<head>) so it can also be published as a Claude artifact. This script
wraps it in a full document with the iPhone web-app tags, a manifest, icons and
an offline service worker.

Usage: python3 tools/build_app.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
BG = (12, 13, 17)
BLUE = (47, 107, 255)
VERSION = "4"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Game">
<meta name="theme-color" content="#0C0D11">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
<style>
html{box-sizing:border-box;height:100%;background:var(--bg,#0C0D11);overscroll-behavior:none;
  padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font-size:14px;overscroll-behavior:none}
img{max-width:100%}
</style>
</head>
<body>
"""

TAIL = """
<script>
if('serviceWorker' in navigator && location.protocol==='https:'){
  addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));
}
</script>
</body>
</html>
"""

SW = """const CACHE='game-v%s';
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['./','./index.html','./icon-180.png'])));self.skipWaiting()});
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
// Network first, so a new version shows up as soon as you are online; the cache covers offline play.
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r})
    .catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('./index.html'))));
});
""" % VERSION

MANIFEST = """{
  "name": "Game",
  "short_name": "Game",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0C0D11",
  "theme_color": "#0C0D11",
  "icons": [
    {"src": "icon-180.png", "sizes": "180x180", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
"""


def icon(size: int) -> Image.Image:
    # The first level in one picture: a single blue dot, about to grow.
    scale = 4
    s = size * scale
    im = Image.new("RGB", (s, s), BG)
    d = ImageDraw.Draw(im)
    r = s * 0.25
    cx, cy = s * 0.5, s * 0.5
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE)
    return im.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    game = (ROOT / "index.html").read_text(encoding="utf-8")
    (OUT / "index.html").write_text(HEAD + game + TAIL, encoding="utf-8")
    (OUT / "sw.js").write_text(SW, encoding="utf-8")
    (OUT / "manifest.webmanifest").write_text(MANIFEST, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    icon(180).save(OUT / "icon-180.png")
    icon(512).save(OUT / "icon-512.png")
    print("Built", OUT)


if __name__ == "__main__":
    main()
