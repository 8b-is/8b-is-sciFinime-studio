import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/screen.py"
spec = importlib.util.spec_from_file_location("screen", SCRIPT)
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


class FindMpvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_explicit_path_wins(self):
        fake = self.home / "mpv"
        fake.write_text("#!/bin/sh\n")
        self.assertEqual(screen.find_mpv(str(fake)), str(fake))

    def test_env_mpv_used_when_no_explicit(self):
        fake = self.home / "mpv"
        fake.write_text("#!/bin/sh\n")
        os.environ["MPV"] = str(fake)
        self.assertEqual(screen.find_mpv(None), str(fake))

    def test_nothing_found_returns_none(self):
        with patch.object(screen.shutil, "which", return_value=None), patch.object(
            screen, "MPV_CANDIDATES", ()
        ), patch.object(screen.Path, "home", return_value=self.home):
            self.assertIsNone(screen.find_mpv(None))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "plate.jpg").write_bytes(b"x")

    def manifest(self, boards, audio=None):
        data = {"title": "t", "boards": boards}
        if audio:
            data["audio"] = audio
        path = self.root / "m.json"
        path.write_text(json.dumps(data))
        return path

    def test_loads_boards_and_durations(self):
        path = self.manifest([
            {"plate": "plate.jpg", "hold": 26, "board": "1.1", "action": "a"},
            {"plate": "plate.jpg", "hold": 8},
        ])
        boards, audio, title = screen.load_manifest(path)
        self.assertEqual(len(boards), 2)
        self.assertEqual(boards[0]["hold"], 26.0)
        self.assertEqual(boards[0]["board"], "1.1")
        self.assertEqual(boards[1]["hold"], 8.0)
        self.assertEqual(audio, [])
        self.assertEqual(title, "t")

    def test_missing_plate_raises(self):
        path = self.manifest([{"plate": "nope.jpg", "hold": 1}])
        with self.assertRaises(SystemExit):
            screen.load_manifest(path)

    def test_empty_boards_raises(self):
        path = self.manifest([])
        with self.assertRaises(SystemExit):
            screen.load_manifest(path)

    def test_audio_resolved(self):
        (self.root / "bed.wav").write_bytes(b"RIFF")
        path = self.manifest([{"plate": "plate.jpg", "hold": 1}], audio=["bed.wav"])
        _, audio, _ = screen.load_manifest(path)
        self.assertEqual(audio, [(self.root / "bed.wav").resolve()])


class ConcatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_concat_has_durations_and_trailing_repeat(self):
        a = self.root / "a.jpg"
        b = self.root / "b.jpg"
        boards = [{"plate": a, "hold": 1.5}, {"plate": b, "hold": 2.25}]
        out = screen.write_concat(boards, self.root / "x.ffconcat")
        text = out.read_text()
        self.assertTrue(text.startswith("ffconcat version 1.0"))
        self.assertIn(f"file '{a}'", text)
        self.assertIn("duration 1.500", text)
        self.assertIn("duration 2.250", text)
        # trailing entry flushes the final hold; no duration on it
        self.assertEqual(text.strip().splitlines()[-1], f"file '{b}'")

    def test_quote_escapes_single_quote(self):
        self.assertEqual(screen._ffconcat_quote(Path("/a'b.jpg")), "'/a'\\''b.jpg'")


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.concat = self.root / "x.ffconcat"
        self.concat.write_text("ffconcat version 1.0\n")
        self.audio = self.root / "bed.wav"
        self.audio.write_bytes(b"RIFF")

    def test_play_command_carries_audio_and_window(self):
        cmd = screen.build_command("/bin/mpv", self.concat, [self.audio])
        self.assertIn("--force-window=yes", cmd)
        self.assertIn(f"--audio-file={self.audio}", cmd)
        self.assertIn("--demuxer-lavf-format=concat", cmd)
        self.assertIn("--demuxer-lavf-o=safe=0", cmd)
        self.assertEqual(cmd[-1], str(self.concat))

    def test_render_command_is_headless(self):
        cmd = screen.build_command("/bin/mpv", self.concat, [self.audio], render_dir=self.root, frames=3)
        self.assertIn("--no-audio", cmd)
        self.assertIn("--vo=image", cmd)
        self.assertIn(f"--vo-image-outdir={self.root}", cmd)
        self.assertIn("--frames=3", cmd)

    def test_no_audio_flag_when_silent(self):
        cmd = screen.build_command("/bin/mpv", self.concat, [])
        self.assertIn("--no-audio", cmd)


class DirTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_dir_sorted_with_hold(self):
        for name in ("b.jpg", "a.png", "notes.txt"):
            (self.root / name).write_bytes(b"x")
        boards, audio, title = screen.boards_from_dir(self.root, 4.0)
        self.assertEqual([b["plate"].name for b in boards], ["a.png", "b.jpg"])
        self.assertTrue(all(b["hold"] == 4.0 for b in boards))
        self.assertEqual(audio, [])
        self.assertEqual(title, self.root.name)

    def test_empty_dir_raises(self):
        with self.assertRaises(SystemExit):
            screen.boards_from_dir(self.root, 4.0)


class DryRunTests(unittest.TestCase):
    def test_dry_run_builds_plan_without_launching(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "plate.jpg").write_bytes(b"x")
        manifest = root / "m.json"
        manifest.write_text(json.dumps({"title": "t", "boards": [{"plate": "plate.jpg", "hold": 5}]}))
        mpv = root / "mpv"
        mpv.write_text("#!/bin/sh\n")
        with patch.object(screen, "probe_mpv", return_value="mpv test"), patch.object(
            screen.subprocess, "run"
        ) as run:
            rc = screen.main([str(manifest), "--mpv", str(mpv), "--dry-run"])
        self.assertEqual(rc, 0)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
