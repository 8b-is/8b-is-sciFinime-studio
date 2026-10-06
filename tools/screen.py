#!/usr/bin/env python3
"""screen.py — the screen: play the boards so the eye gets numbers too.

The sibling of `tools/listen_stems.py` (the ears). Where the ears measure
the stems, the screen *seats the boards* — it turns a screening manifest
(the timed boards) into a playable slideshow, one plate held for one
timecode, over the temp sound bed. The player is **mpv** — the studio does
not reimplement a video path; it drives the sovereign native player.

The player is invoked as a separate process (mpv is GPL; the studio is
MIT — we call it over the CLI, we never link it). See
`docs/screening.md`.

Run from the studio root:

  # dry-run: resolve mpv, build the board list, print the plan (no window)
  uv run tools/screen.py --dry-run

  # screen it (a window opens; space/pause, q/quit; per-board timecodes)
  uv run tools/screen.py

  # headless proof: render the boards to PNGs (works with no display)
  uv run tools/screen.py --render /tmp/screen-out --frames 8

  # encode the screening to a watchable file (ffmpeg; exact holds)
  uv run tools/screen.py --export animatic-01.mp4

  # any directory of plates, fixed hold
  uv run tools/screen.py --dir path/to/plates --hold 4

A screening manifest is JSON (see screen/animatic-01-cold-open.json):

  {
    "title": "animatic 01 · the dissonant frequencies — cold open",
    "audio": ["projects/.../four-four-122.wav"],
    "boards": [
      {"plate": "assets/.../shinjuku-rain.jpg", "hold": 26,
       "board": "1.1", "action": "rain-slicked crossing"}
    ]
  }

Paths in a manifest are relative to the studio root. The board list is an
ffmpeg `concat` document, so mpv honours per-plate durations exactly — the
timecode is the boss. The ears still verify last: a branch may be ranked,
only a verified branch may be bound.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MANIFEST = (
    REPO_ROOT
    / "projects"
    / "01.01-sandbox-in-the-shell"
    / "screen"
    / "animatic-01-cold-open.json"
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".avif", ".jxl"}

# the sovereign player: wherever mpv actually lives on this machine. A build
# off PATH (the .app bundle) is the common macOS reality — do not assume.
MPV_CANDIDATES = (
    "/Applications/mpv.app/Contents/MacOS/mpv",
    "/opt/homebrew/bin/mpv",
    "/usr/local/bin/mpv",
    "/usr/bin/mpv",
)


def find_mpv(explicit: str | None) -> str | None:
    for cand in (explicit, os.environ.get("MPV")):
        if cand and Path(cand).exists():
            return cand
    found = shutil.which("mpv")
    if found:
        return found
    for cand in MPV_CANDIDATES:
        if Path(cand).exists():
            return cand
    local = Path.home() / ".local" / "bin" / "mpv"
    if local.exists():
        return str(local)
    return None


def probe_mpv(mpv: str) -> str:
    try:
        out = subprocess.run(
            [mpv, "--version"], capture_output=True, text=True, timeout=15
        )
        first = (out.stdout or out.stderr).splitlines()
        return first[0].strip() if first else "mpv (version unreadable)"
    except Exception as exc:  # noqa: BLE001 - report, do not crash the plan
        return f"mpv (probe failed: {exc})"


def resolve_plate(raw: str, base: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    for root in (base, REPO_ROOT):
        cand = root / raw
        if cand.exists():
            return cand.resolve()
    return (base / raw).resolve()


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    boards = data.get("boards") or []
    if not boards:
        raise SystemExit(f"manifest has no boards: {path}")
    base = path.parent
    out = []
    for i, b in enumerate(boards, 1):
        plate = resolve_plate(str(b["plate"]), base)
        if not plate.exists():
            raise SystemExit(f"board {i}: plate not found: {plate}")
        hold = float(b.get("hold", 5.0))
        out.append(
            {
                "plate": plate,
                "hold": hold,
                "board": str(b.get("board", i)),
                "action": str(b.get("action", "")),
            }
        )
    audio = [resolve_plate(str(a), base) for a in (data.get("audio") or [])]
    return out, audio, str(data.get("title", path.stem))


def boards_from_dir(directory: Path, hold: float) -> tuple[list[dict], list, str]:
    files = sorted(
        p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS and p.is_file()
    )
    if not files:
        raise SystemExit(f"no images found in {directory}")
    boards = [{"plate": p.resolve(), "hold": hold, "board": str(i), "action": ""} for i, p in enumerate(files, 1)]
    return boards, [], directory.name


def _ffconcat_quote(path: Path) -> str:
    return "'" + str(path).replace("'", "'\\''") + "'"


def write_concat(boards: list[dict], path: Path) -> Path:
    lines = ["ffconcat version 1.0"]
    for b in boards:
        lines.append(f"file {_ffconcat_quote(b['plate'])}")
        lines.append(f"duration {b['hold']:.3f}")
    path.write_text("\n".join(lines) + "\n")
    return path


def build_command(
    mpv: str,
    concat: Path,
    audio: list[Path],
    *,
    render_dir: Path | None = None,
    frames: int | None = None,
    fs: bool = False,
) -> list[str]:
    cmd = [
        mpv,
        "--no-config",
        "--demuxer-lavf-format=concat",
        "--demuxer-lavf-o=safe=0",
        "--image-display-duration=inf",
        "--keep-open=no",
    ]
    if render_dir is not None:
        cmd += [
            "--vo=image",
            "--vo-image-format=png",
            f"--vo-image-outdir={render_dir}",
            "--no-audio",
            "--really-quiet",
        ]
    else:
        cmd += ["--force-window=yes", "--audio-file-auto=no"]
        if fs:
            cmd += ["--fullscreen"]
        if not audio:
            cmd += ["--no-audio"]
    if frames is not None:
        cmd += [f"--frames={frames}"]
    for a in audio:
        cmd += [f"--audio-file={a}"]
    cmd.append(str(concat))
    return cmd


def find_ffmpeg(explicit: str | None = None) -> str | None:
    for cand in (explicit, os.environ.get("FFMPEG")):
        if cand and Path(cand).exists():
            return cand
    found = shutil.which("ffmpeg")
    if found:
        return found
    for cand in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"):
        if Path(cand).exists():
            return cand
    return None


def build_export_command(
    ffmpeg: str,
    boards: list[dict],
    audio: list[Path],
    out: Path,
    *,
    fps: int,
    size: str,
    duration: float | None = None,
) -> list[str]:
    # each board is a still held for its timecode: -loop 1 -t <hold>. Concats
    # the stills in the filter graph (the concat *demuxer* mis-handles still
    # durations in ffmpeg 9), so the holds are exact.
    w, h = size.lower().split("x")
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for b in boards:
        cmd += ["-loop", "1", "-t", f"{b['hold']:.3f}", "-i", str(b["plate"])]
    n = len(boards)
    for a in audio:
        cmd += ["-stream_loop", "-1", "-i", str(a)]
    norm = []
    for i in range(n):
        norm.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps}[v{i}]"
        )
    graph = ";".join(norm) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    cmd += ["-filter_complex", graph, "-map", "[v]"]
    if audio:
        cmd += ["-map", f"{n}:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart"]
    cmd += [str(out)]
    return cmd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="the screen — play the boards via mpv")
    ap.add_argument("manifest", nargs="?", type=Path, default=None,
                    help=f"screening manifest JSON (default: {DEFAULT_MANIFEST.relative_to(REPO_ROOT)})")
    ap.add_argument("--dir", type=Path, default=None, help="a directory of plates (fixed hold)")
    ap.add_argument("--hold", type=float, default=5.0, help="hold per plate for --dir (seconds)")
    ap.add_argument("--mpv", default=None, help="explicit path to the mpv binary")
    ap.add_argument("--edl", type=Path, default=None, help="write the board list here and keep it")
    ap.add_argument("--audio", action="append", default=None, help="audio bed file (repeatable)")
    ap.add_argument("--no-audio", action="store_true", help="silence the screen")
    ap.add_argument("--dry-run", action="store_true", help="build + print the plan; do not launch mpv")
    ap.add_argument("--render", type=Path, default=None, help="headless: render boards to PNGs in this dir")
    ap.add_argument("--frames", type=int, default=None, help="cap frames (useful with --render)")
    ap.add_argument("--fullscreen", action="store_true", help="fullscreen playback")
    ap.add_argument("--export", type=Path, default=None,
                    help="encode the screening to a video file via ffmpeg")
    ap.add_argument("--fps", type=int, default=30, help="export frame rate (default 30)")
    ap.add_argument("--size", default="1280x720", help="export canvas WxH, letterboxed (default 1280x720)")
    ap.add_argument("--duration", type=float, default=None, help="export cap in seconds (preview a long board list)")
    args = ap.parse_args(argv)

    # 1. the source of boards
    if args.dir:
        boards, audio, title = boards_from_dir(args.dir, args.hold)
    else:
        manifest = args.manifest or DEFAULT_MANIFEST
        if not manifest.exists():
            raise SystemExit(f"manifest not found: {manifest} (see docs/screening.md)")
        boards, audio, title = load_manifest(manifest)

    if args.audio:
        audio = [resolve_plate(a, REPO_ROOT) for a in args.audio]
    if args.no_audio:
        audio = []
    for a in audio:
        if not Path(a).exists():
            raise SystemExit(f"audio bed not found: {a}")

    total = sum(b["hold"] for b in boards)

    # 2. the engine — mpv to play/render, ffmpeg to export
    mpv = None
    version = None
    ffmpeg = None
    if args.export:
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            print("ffmpeg not found (needed for --export). "
                  "macOS: brew install ffmpeg · Linux: apt/dnf/pacman install ffmpeg", file=sys.stderr)
            return 127
    else:
        mpv = find_mpv(args.mpv)
        if not mpv:
            print("mpv not found. Install one of:\n"
                  "  macOS: brew install mpv   (or drop mpv.app in /Applications)\n"
                  "  Linux: apt/dnf/pacman install mpv", file=sys.stderr)
            return 127
        version = probe_mpv(mpv)

    # 3. the board list (ffmpeg concat = per-plate timecodes)
    if args.edl:
        concat = write_concat(boards, args.edl)
        tmp = None
    else:
        fd, name = tempfile.mkstemp(suffix=".ffconcat", prefix="screen-")
        os.close(fd)
        concat = write_concat(boards, Path(name))
        tmp = concat

    # 4. the plan
    print(f"screen: {title}")
    if args.export:
        print(f"export: {ffmpeg}")
        print(f"        {args.size} @ {args.fps}fps → {args.export}")
    else:
        print(f"player: {version}")
        print(f"        {mpv}")
    print(f"boards: {len(boards)} · runtime {total:.1f}s ({total / 60:.2f} min)")
    if audio:
        for a in audio:
            print(f"  audio {Path(a).name}")
    for b in boards:
        tag = f"[{b['board']}]" if b["board"] else ""
        action = f"  {b['action']}" if b["action"] else ""
        print(f"  {b['hold']:6.1f}s  {tag:>7}  {Path(b['plate']).name}{action}")
    print(f"board list: {concat}")

    if args.dry_run:
        if tmp:
            tmp.unlink(missing_ok=True)
        print("\ndry-run: verified the player and the board list; nothing launched.")
        return 0

    # 5. seat it
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        cmd = build_export_command(
            ffmpeg, boards, audio, args.export,
            fps=args.fps, size=args.size, duration=args.duration,
        )
        print()
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            print(f"failed to launch {ffmpeg}", file=sys.stderr)
            return 127
        except subprocess.CalledProcessError as exc:
            print(f"ffmpeg exited {exc.returncode}", file=sys.stderr)
            return exc.returncode
        finally:
            if tmp:
                tmp.unlink(missing_ok=True)
        size_bytes = args.export.stat().st_size
        print(f"\nexported {args.export} ({size_bytes / 1e6:.2f} MB)")
        return 0

    if args.render:
        args.render.mkdir(parents=True, exist_ok=True)
        cmd = build_command(mpv, concat, audio, render_dir=args.render, frames=args.frames)
    else:
        cmd = build_command(mpv, concat, audio, frames=args.frames, fs=args.fullscreen)
    print()
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"failed to launch {mpv}", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as exc:
        print(f"mpv exited {exc.returncode}", file=sys.stderr)
        return exc.returncode
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)

    if args.render:
        frames = sorted(p.name for p in args.render.glob("*.png"))
        print(f"\nrendered {len(frames)} frame(s) to {args.render}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
