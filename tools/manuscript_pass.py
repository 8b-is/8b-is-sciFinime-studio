#!/usr/bin/env python3
"""manuscript_pass.py — convert a studio prose chapter into the pocoo
manuscript's HTML conventions (the `book/<slug>/manuscript.html` lane).

  uv run tools/manuscript_pass.py prose/chapter-07-the-patients.md 7 \
    "chapter seven — the patients" > /tmp/ch7.html

What it does (matching the seated conventions, learned from the 10-05
syncs): strips the title/date lines and the `*next:*` footer, splits
`* * *` scene breaks into `<div class="stone">∿</div>`, joins soft
wraps, maps *em* / **strong** / `>` blockquotes, escapes entities.

Then: insert the fragment before the garden section in
`pocoo.vaked.dev/book/sandbox-in-the-shell/manuscript.html`, bump the
garden/pilot section numbers, and copy the file over
`demos/book/sandbox-in-the-shell.html` (byte-identical twin; the build
copies both to dist). See lap 8 / lap 16 of the studio log for the full
procedure.
"""

import html
import re
import sys


def convert(path: str, num: int, title: str) -> str:
    src = open(path, encoding="utf-8").read()
    lines = src.split("\n")
    body = []
    for i, ln in enumerate(lines):
        if i == 0 and ln.startswith("# "):
            continue
        if ln.strip().startswith("*Sandbox in the Shell"):
            continue
        body.append(ln)
    text = "\n".join(body)
    idx = text.rfind("\n---")
    text = text[:idx].strip()
    if text.startswith("---"):
        text = text[3:].strip()

    out = [f'<h1 class="chapter"><span class="num">§{num}</span>{title}</h1>']
    for si, seg in enumerate(re.split(r"\n\s*\*\s*\*\s*\*\s*\n", text)):
        if si > 0:
            out.append('<div class="stone">∿</div>')
        for p in (x.strip() for x in re.split(r"\n\s*\n", seg)):
            if not p:
                continue
            if p.startswith(">"):
                q = " ".join(l.lstrip("> ").strip() for l in p.split("\n") if l.strip())
                q = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html.escape(q, quote=False))
                out.append(f"<blockquote><p>{q}</p></blockquote>")
                continue
            joined = " ".join(l.strip() for l in p.split("\n") if l.strip())
            joined = html.escape(joined, quote=False)
            joined = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", joined)
            joined = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", joined)
            out.append(f"<p>{joined}</p>")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    chapter, num, title = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    print(convert(chapter, num, title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
