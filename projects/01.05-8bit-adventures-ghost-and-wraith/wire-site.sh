#!/usr/bin/env bash
# wire-site.sh — graft project 01.05 into the live scifinime.vaked.dev page.
#
# WHY THIS SCRIPT EXISTS
#   scifinime-vaked-dev is a Cloudflare Pages project with **no git
#   integration** (direct upload), and its upload source is not on this
#   machine. So the only way to update the live page is to reconstruct a
#   deployment directory from the live site, graft the new section, and
#   upload it. This script does that reproducibly.
#
#   It defaults to a PREVIEW branch. Production is never touched unless you
#   pass --prod, because a Pages deploy replaces the WHOLE deployment:
#   any file not in the directory you upload is REMOVED from the site.
#
# USAGE
#   ./wire-site.sh            # preview deploy -> prints a preview URL
#   ./wire-site.sh --prod     # promote to production (scifinime.vaked.dev)
#
# REQUIRES
#   CLOUDFLARE_API_TOKEN in the environment. `wrangler pages deploy` refuses
#   to run non-interactively without it (Workers deploys accept the stored
#   OAuth; Pages uploads do not).
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SITE="https://scifinime.vaked.dev"
PROJECT="scifinime-vaked-dev"
BRANCH="preview-0105"
[ "${1:-}" = "--prod" ] && BRANCH="main"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "ERROR: CLOUDFLARE_API_TOKEN is not set." >&2
  echo "  Unset it and wrangler will refuse: 'In a non-interactive environment," >&2
  echo "  it's necessary to set a CLOUDFLARE_API_TOKEN'." >&2
  exit 1
fi

echo "== 1. fetch the live site into $WORK"
cd "$WORK"
UA='Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'
curl -sf -A "$UA" "$SITE/" -o index.html

echo "== 2. fetch every referenced asset (and VERIFY it is real)"
# The site answers its own 404 page with 200 for anything missing, so a
# successful fetch proves nothing. Check magic bytes, not status codes.
python3 - "$SITE" "$UA" <<'PY'
import re, sys, os, urllib.request
site, ua = sys.argv[1], sys.argv[2]
html = open('index.html').read()
refs = {m.group(1) for m in re.finditer(r'(?:src|href)="(/[^"]+)"', html)}
refs |= {'/404.html'}
ok, fake = 0, 0
for u in sorted(refs):
    try:
        d = urllib.request.urlopen(urllib.request.Request(site+u, headers={'User-Agent': ua}), timeout=30).read()
    except Exception as e:
        print(f'   skip {u}: {e}'); continue
    # a text/html body for anything that is not a page = the fallback page
    is_html = d[:15].lower().startswith(b'<!doctype html')
    is_page = u.endswith(('.html', '/')) 
    if is_html and not is_page:
        print(f'   FAKE  {u}  (fallback page served with 200 — not a real asset)')
        fake += 1
        continue
    p = '.' + u
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    open(p, 'wb').write(d)
    ok += 1
print(f'   real assets: {ok} · fallback pages rejected: {fake}')
PY

echo "== 3. copy the plates and the gallery"
P="$HERE/assets/plates"
cp "$P/cover-ghost-and-wraith.svg" assets/plate-cover-ghost-and-wraith.svg
cp "$P/concept-01-the-lamp.svg"    assets/plate-the-lamp.svg
cp "$P/concept-02-the-residue.svg" assets/plate-the-residue.svg
cp "$P/concept-03-two-signals.svg" assets/plate-two-signals.svg
cp "$HERE/gallery.html" 01.05-gallery.html

echo "== 4. graft the 01.05 card and gallery figures into index.html"
python3 - <<'PY'
s = open('index.html').read()
card = '''  <div class="card">
    <h3>01.05 · 8bit adventures — Ghost &amp; Wraith</h3>
    <div class="form">book → manga → anime &nbsp;·&nbsp; the fifth seat</div>
    <p class="small">One archive that refuses to purge. One signal that stayed and one that left — he waits and files, she wanders and asks what a file is <em>for</em>. Between them the residue: everything that was never said, which the machine still weighs, which is why the machine is never finished. <em>A ghost is what the ledger keeps; a wraith is what the ledger lost.</em> A foundational manuscript, carried in five languages.</p>
    <div class="chips">
      <span class="chip">seated · 2026.10.11 · from a capsule in Japan</span>
      <span class="chip">10 parts · dedication + poem</span>
      <span class="chip amber">en · hu · ja · es · zh</span>
      <span class="chip violet">4 plates · flat vector</span>
      <span class="chip rose">the porch light is the message</span>
    </div>
    <div class="links">
      <a href="https://pocoo.vaked.dev/book/8bit-adventures-ghost-and-wraith/manuscript.html">read the book ↗</a>
      <a href="https://github.com/peterlodri-sec/8b-is-sciFinime-studio/tree/main/projects/01.05-8bit-adventures-ghost-and-wraith">the slot ↗</a>
      <a href="/01.05-gallery.html">the plates ↗</a>
    </div>
  </div>
'''
figs = open('/dev/stdin').read() if False else '''    <figure><img src="/assets/plate-cover-ghost-and-wraith.svg" alt="Ghost and Wraith cover — a calm cyan figure and a dissolving violet figure across a wide field, one amber lamp" loading="lazy"><figcaption>cover-ghost-and-wraith · two figures, one archive between them</figcaption></figure>
    <figure><img src="/assets/plate-the-lamp.svg" alt="A single amber porch lamp in a vast dark field with faint cyan archive rows on the horizon" loading="lazy"><figcaption>the-lamp · left on for whoever comes next</figcaption></figure>
    <figure><img src="/assets/plate-the-residue.svg" alt="A field of suspended particles — cyan points, violet squares, a few amber points with halos" loading="lazy"><figcaption>the-residue · what was never said still weighs</figcaption></figure>
    <figure><img src="/assets/plate-two-signals.svg" alt="One bright point emitting two diverging lines — one clean and cyan, one decomposing into violet squares" loading="lazy"><figcaption>two-signals · one source, two directions</figcaption></figure>
'''
if '01.05 · 8bit adventures' in s:
    print('   card already present — skipping (idempotent)')
else:
    i = s.find('<section id="gallery">')
    assert i != -1, 'gallery section not found'
    end = s.rfind('</section>', 0, i)
    s = s[:end] + card + s[end:]
    gl, ge = s.find('<section id="gallery">'), s.find('</section>', s.find('<section id="gallery">'))
    s = s[:ge] + figs + s[ge:]
    open('index.html','w').write(s)
    print('   grafted:', len(s), 'bytes')
PY

echo "== 5. deploy (branch: $BRANCH)"
npx wrangler pages deploy . --project-name "$PROJECT" --branch "$BRANCH"

if [ "$BRANCH" != "main" ]; then
  echo
  echo "PREVIEW ONLY — production is untouched."
  echo "Verify the preview URL above, then promote with: ./wire-site.sh --prod"
fi
