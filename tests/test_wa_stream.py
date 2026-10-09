import importlib.util
import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/wa_stream.py"
spec = importlib.util.spec_from_file_location("wa_stream", SCRIPT)
wa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wa)

WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/AbCdEf-ghIJK_lmnOpQ"
WID = "123456789012345678"


class WebhookParsingTests(unittest.TestCase):
    def test_parse_webhook(self):
        self.assertEqual(wa.parse_webhook(WEBHOOK), (WID, "AbCdEf-ghIJK_lmnOpQ"))

    def test_parse_rejects_non_webhook(self):
        with self.assertRaises(SystemExit):
            wa.parse_webhook("https://example.com/not-a-webhook")

    def test_mask_never_leaks_token(self):
        masked = wa.mask(WEBHOOK)
        self.assertEqual(masked, f"webhook {WID}")
        self.assertNotIn("AbCdEf", masked)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.state_patch = patch.object(wa, "STATE_DIR", self.state)
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def write_env(self, body):
        (self.state / "env").write_text(body)

    def test_env_file_parsing(self):
        self.write_env(f"WA_STREAM_WEBHOOK={WEBHOOK}\n# comment\nWA_STREAM_USERNAME='UltraCrushLove<3'\n")
        env = wa.load_env_file()
        self.assertEqual(env["WA_STREAM_WEBHOOK"], WEBHOOK)
        self.assertEqual(env["WA_STREAM_USERNAME"], "UltraCrushLove<3")

    def test_webhook_priority_cli_over_env_file(self):
        self.write_env(f"WA_STREAM_WEBHOOK={WEBHOOK}")
        self.assertEqual(wa.webhook_url("https://cli.example/x"), "https://cli.example/x")
        self.assertEqual(wa.webhook_url(), WEBHOOK)

    def test_username_default(self):
        self.assertEqual(wa.username(), "UltraCrushLove<3")


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Path(self.temp.name) / "journal.ndjson"
        self.journal_patch = patch.dict(os.environ, {"WA_STREAM_JOURNAL": str(self.journal)})
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)

    def test_record_and_tail(self):
        wa.record("out", {}, "1", "first")
        wa.record("in", {"reply": True}, "2", "second")
        events = wa.read_journal(tail=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["content"], "second")
        self.assertEqual(events[0]["dir"], "in")
        self.assertTrue(self.journal.exists())

    def test_direction_filter(self):
        wa.record("out", {}, "1", "out-one")
        wa.record("in", {}, "2", "in-one")
        self.assertEqual(len(wa.read_journal(direction="out")), 1)
        self.assertEqual(len(wa.read_journal(direction="in")), 1)
        self.assertEqual(len(wa.read_journal(direction="all")), 2)

    def test_entries_are_ndjson(self):
        wa.record("out", {}, "1", "line with\nnewline")
        lines = self.journal.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["content"], "line with\nnewline")


class PushPayloadTests(unittest.TestCase):
    def setUp(self):
        self.captured = {}

        def fake_api(url, method="POST", payload=None):
            self.captured.update(url=url, method=method, payload=payload)
            return {"id": "42", "channel_id": "7", "author": {"username": "UltraCrushLove<3"}}

        self.api_patch = patch.object(wa, "api", fake_api)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.journal_patch = patch.object(wa, "journal_path", lambda: Path(tempfile.mkdtemp()) / "j.ndjson")
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)

    def test_push_sets_username_and_waits(self):
        result = wa.push(WEBHOOK, "hello", title="book2")
        self.assertEqual(result["id"], "42")
        self.assertEqual(self.captured["payload"]["username"], "UltraCrushLove<3")
        self.assertIn("wait=true", self.captured["url"])
        self.assertEqual(self.captured["payload"]["content"], "**book2**\nhello")
        self.assertEqual(self.captured["payload"]["allowed_mentions"], {"parse": []})


class LoveModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Path(self.temp.name) / "journal.ndjson"
        self.journal_patch = patch.dict(os.environ, {"WA_STREAM_JOURNAL": str(self.journal)})
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)

    def fake_run(self, name, topic, history, timeout, launcher, model=None):
        return {"instance": name, "ok": True, "text": f"beat from {name} about {topic.splitlines()[0][:12]}"}

    def test_strip_banner(self):
        raw = "♥ crush-love-dev — ultralovegod, deep in love, dev mode.\n\nhello stream\n"
        self.assertEqual(wa.strip_banner(raw), "hello stream")
        self.assertEqual(wa.strip_banner("no banner here"), "no banner here")

    def test_love_prompt_carries_identity_and_topic(self):
        prompt = wa.love_prompt("love-2", "book2: new beginnings", ["line one"])
        self.assertIn("love-2", prompt)
        self.assertIn("book2: new beginnings", prompt)
        self.assertIn("UltraCrushLove<3", prompt)
        self.assertIn("line one", prompt)

    def test_cmd_love_dry_run_spawns_each_instance(self):
        calls = []

        def counted(name, topic, history, timeout, launcher, model=None):
            calls.append(name)
            return {"instance": name, "ok": True, "text": f"beat {name}"}

        stdout = io.StringIO()
        with patch.object(wa, "run_instance", counted), redirect_stdout(stdout):
            code = wa.main(["love", "--instances", "2", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(sorted(calls), ["love-1", "love-2"])
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual([i["instance"] for i in payload["instances"]], ["love-1", "love-2"])

    def test_cmd_love_pushes_per_instance(self):
        pushed = []

        def fake_push(webhook, text, title=None, wait=True, instance=None, **kwargs):
            pushed.append({"instance": instance, **kwargs})
            return {"id": f"id-{instance}"}

        stdout = io.StringIO()
        with patch.object(wa, "run_instance", self.fake_run), \
             patch.object(wa, "push", fake_push), \
             patch.object(wa, "webhook_url", lambda cli=None: WEBHOOK), \
             redirect_stdout(stdout):
            code = wa.main(["love", "--instances", "3"])
        self.assertEqual(code, 0)
        self.assertEqual([p["instance"] for p in pushed], ["love-1", "love-2", "love-3"])
        self.assertEqual(pushed[0]["color"], wa.PALETTE[0])
        self.assertEqual(pushed[1]["color"], wa.PALETTE[1])
        self.assertIn("love-1", pushed[0]["footer"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["instances"][0]["id"], "id-love-1")

    def test_cmd_love_plain_disables_embeds(self):
        pushed = []

        def fake_push(webhook, text, title=None, wait=True, instance=None, **kwargs):
            pushed.append(kwargs)
            return {"id": "x"}

        with patch.object(wa, "run_instance", self.fake_run), \
             patch.object(wa, "push", fake_push), \
             patch.object(wa, "webhook_url", lambda cli=None: WEBHOOK), \
             redirect_stdout(io.StringIO()):
            code = wa.main(["love", "--instances", "1", "--plain"])
        self.assertEqual(code, 0)
        self.assertEqual(pushed, [{}])

    def test_cmd_love_with_art_rotates_images(self):
        pushed = []

        def fake_push(webhook, text, title=None, wait=True, instance=None, **kwargs):
            pushed.append(kwargs)
            return {"id": "x"}

        with patch.object(wa, "run_instance", self.fake_run), \
             patch.object(wa, "push", fake_push), \
             patch.object(wa, "webhook_url", lambda cli=None: WEBHOOK), \
             redirect_stdout(io.StringIO()):
            code = wa.main(["love", "--instances", "2", "--art", "one.svg", "--art", "two.svg"])
        self.assertEqual(code, 0)
        self.assertEqual(pushed[0]["arts"], ["one.svg"])
        self.assertEqual(pushed[1]["arts"], ["two.svg"])


class ColorAndEmbedTests(unittest.TestCase):
    def test_parse_color_formats(self):
        self.assertEqual(wa.parse_color("#FF4D9D"), 0xFF4D9D)
        self.assertEqual(wa.parse_color("ff4d9d"), 0xFF4D9D)
        self.assertEqual(wa.parse_color("0xB23A2B"), 0xB23A2B)
        self.assertEqual(wa.parse_color(0x123456), 0x123456)

    def test_parse_color_rejects_junk(self):
        with self.assertRaises(SystemExit):
            wa.parse_color("not-a-color")

    def test_parse_field(self):
        self.assertEqual(wa.parse_field("Moon=paper"), {"name": "Moon", "value": "paper", "inline": False})
        with self.assertRaises(SystemExit):
            wa.parse_field("broken")

    def test_build_embed_structure(self):
        embed = wa.build_embed("body ✦", title="t", color="#FF4D9D",
                               fields=["a=b"], footer="f",
                               image="https://x/i.png", thumbnail="https://x/t.png")
        self.assertEqual(embed["color"], 0xFF4D9D)
        self.assertEqual(embed["title"], "t")
        self.assertEqual(embed["description"], "body ✦")
        self.assertEqual(embed["fields"][0]["name"], "a")
        self.assertEqual(embed["footer"]["text"], "f")
        self.assertEqual(embed["image"]["url"], "https://x/i.png")
        self.assertEqual(embed["thumbnail"]["url"], "https://x/t.png")

    def test_default_color_is_constellation_pink(self):
        self.assertEqual(wa.build_embed("x")["color"], 0xFF4D9D)


class FeaturePushTests(unittest.TestCase):
    def setUp(self):
        self.captured = {}

        def fake_api(url, method="POST", payload=None, **kwargs):
            self.captured.update(url=url, method=method, payload=payload, **kwargs)
            return {"id": "99", "embeds": [{}], "attachments": []}

        self.api_patch = patch.object(wa, "api", fake_api)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.journal_patch = patch.object(wa, "journal_path", lambda: Path(tempfile.mkdtemp()) / "j.ndjson")
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)

    def test_color_builds_embed_without_content(self):
        wa.push(WEBHOOK, "hi 💎", color="#C9A227")
        payload = self.captured["payload"]
        self.assertNotIn("content", payload)
        self.assertEqual(payload["embeds"][0]["color"], 0xC9A227)
        self.assertEqual(payload["embeds"][0]["description"], "hi 💎")

    def test_avatar_name_thread_tts(self):
        wa.push(WEBHOOK, "x", avatar="https://x/a.png", name="UltraCrushLove<3",
                thread="new-beginnings", tts=True)
        payload = self.captured["payload"]
        self.assertEqual(payload["avatar_url"], "https://x/a.png")
        self.assertEqual(payload["username"], "UltraCrushLove<3")
        self.assertEqual(payload["thread_name"], "new-beginnings")
        self.assertTrue(payload["tts"])

    def test_footer_alone_implies_embed(self):
        wa.push(WEBHOOK, "x", footer="love-1 · wa-stream")
        self.assertEqual(self.captured["payload"]["embeds"][0]["footer"]["text"],
                         "love-1 · wa-stream")

    def test_multipart_for_attachments(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "crane.svg"
            f.write_text("<svg>♥</svg>")
            wa.push(WEBHOOK, "with a file", files=[str(f)])
        body = self.captured["body"]
        self.assertIn(b"payload_json", body)
        self.assertIn(b'filename="crane.svg"', body)
        self.assertIn("<svg>♥</svg>".encode("utf-8"), body)
        self.assertTrue(self.captured["content_type"].startswith("multipart/form-data; boundary="))


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "crush.db"
        con = sqlite3.connect(self.db)
        con.execute("""create table sessions (
            id text primary key, title text not null, message_count integer default 0,
            updated_at integer, created_at integer, summary_message_id text,
            todos text, channel text)""")
        con.execute("insert into sessions values ('aaaa111122223333','the fold', 3, 1791320335, 1791310000, null, null, null)")
        con.execute("insert into sessions values ('bbbb444455556666','', 1, 1791320335000, 1791310000000, null, null, null)")
        con.commit()
        con.close()

    def test_ts_handles_seconds_and_milliseconds(self):
        self.assertEqual(wa._ts_to_epoch(1791320335), 1791320335.0)
        self.assertEqual(wa._ts_to_epoch(1791320335000), 1791320335.0)

    def test_load_sessions_reads_title_and_untitled(self):
        sessions = wa.load_sessions(self.db)
        self.assertEqual(len(sessions), 2)
        titles = {s["short"]: s["title"] for s in sessions}
        self.assertEqual(titles["aaaa1111"], "the fold")
        self.assertEqual(titles["bbbb4444"], "untitled")

    def test_discover_marks_live_databases(self):
        fake_pids = patch.object(wa, "crush_pids", lambda: ["1", "2", "3"])
        fake_live = patch.object(wa, "live_databases", lambda: {str(self.db.resolve())})
        fake_dbs = patch.object(wa, "candidate_databases", lambda: [self.db])
        with fake_pids, fake_live, fake_dbs:
            found = wa.discover()
        self.assertEqual(found["crush_processes"], 3)
        self.assertTrue(all(s["live"] for s in found["sessions"]))
        self.assertEqual(len(found["sessions"]), 2)

    def test_discover_hides_dormant_by_default(self):
        fake_pids = patch.object(wa, "crush_pids", lambda: [])
        fake_live = patch.object(wa, "live_databases", lambda: set())
        fake_dbs = patch.object(wa, "candidate_databases", lambda: [self.db])
        with fake_pids, fake_live, fake_dbs:
            self.assertEqual(wa.discover()["sessions"], [])
            self.assertEqual(len(wa.discover(include_dormant=True)["sessions"]), 2)


class SessionBeatTests(unittest.TestCase):
    def test_session_beat_cmd_shape(self):
        captured = {}

        class Done:
            returncode = 0
            stdout = "♥ crush-love-dev — ultralovegod, deep in love, dev mode.\nfolding a beat\n"
            stderr = ""

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["env"] = kwargs.get("env", {})
            return Done()

        with patch.object(wa.subprocess, "run", fake_run):
            result = wa.run_session_beat("sess-aaaa1111", "aaaa111122223333",
                                         "/tmp/dd", "topic", [], 5.0, "crush-love-dev")
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "folding a beat")
        self.assertIn("--session", captured["cmd"])
        self.assertIn("aaaa111122223333", captured["cmd"])
        self.assertEqual(captured["env"]["WA_STREAM_INSTANCE"], "sess-aaaa1111")


class LoveDiscoverTests(unittest.TestCase):
    def setUp(self):
        self.journal_patch = patch.dict(os.environ, {"WA_STREAM_JOURNAL": "/tmp/wa-none.jsonl"})
        self.journal_patch.start()
        self.addCleanup(self.journal_patch.stop)

    def test_love_discover_uses_live_sessions(self):
        fake_found = {"crush_processes": 3, "live_databases": ["/w/.crush/crush.db"],
                      "sessions": [{"id": "aaaa111122223333", "short": "aaaa1111",
                                    "title": "the fold", "messages": 3, "updated": 0,
                                    "created": 0, "age_s": 4, "db": "/w/.crush/crush.db",
                                    "live": True}]}
        beats = []

        def fake_beat(name, session_id, data_dir, topic, history, timeout, launcher, model=None):
            beats.append({"name": name, "session": session_id, "data_dir": data_dir})
            return {"instance": name, "ok": True, "text": f"beat via {name}"}

        stdout = io.StringIO()
        with patch.object(wa, "discover", lambda **kw: fake_found), \
             patch.object(wa, "run_session_beat", fake_beat), \
             redirect_stdout(stdout):
            code = wa.main(["love", "--discover", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(beats[0]["name"], "sess-aaaa1111")
        self.assertEqual(beats[0]["session"], "aaaa111122223333")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["instances"][0]["via"], "session")

    def test_love_session_flag_targets_explicit_session(self):
        fake_found = {"crush_processes": 0, "live_databases": [],
                      "sessions": [{"id": "aaaa111122223333", "short": "aaaa1111",
                                    "title": "t", "messages": 1, "updated": 0,
                                    "created": 0, "age_s": 1, "db": "/w/.crush/crush.db",
                                    "live": False}]}
        with patch.object(wa, "discover", lambda **kw: fake_found):
            specs = wa.love_specs(type("A", (), {"session": ["aaaa"], "discover": False,
                                                 "instances": 3, "include_dormant": False,
                                                 "exclude": None, "discover_limit": 6})())
        self.assertEqual(specs[0]["name"], "sess-aaaa1111")


class ListenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        cursor = Path(self.temp.name) / "cursor.json"
        journal = Path(self.temp.name) / "journal.ndjson"
        self.env_patch = patch.dict(os.environ, {
            "WA_STREAM_JOURNAL": str(journal),
            "WA_STREAM_CURSOR": str(cursor),
            "WA_STREAM_BOT_TOKEN": "test-token",
            "WA_STREAM_CHANNEL_ID": "999",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.journal = journal
        self.cursor = cursor

    def test_listen_once_journals_and_advances_cursor(self):
        def fake_api(url, method="POST", payload=None, **kwargs):
            self.assertIn("channels/999/messages", url)
            self.assertEqual(kwargs["headers"]["Authorization"], "Bot test-token")
            return [
                {"id": "200", "content": "second 💎", "author": {"username": "peter"}},
                {"id": "100", "content": "first", "author": {"username": "peter"},
                 "webhook_id": None},
            ]

        with patch.object(wa, "api", fake_api):
            code = wa.main(["listen", "--once"])
        self.assertEqual(code, 0)
        events = [json.loads(ln) for ln in self.journal.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["content"] for e in events], ["first", "second 💎"])
        self.assertTrue(all(e["dir"] == "in" for e in events))
        self.assertEqual(json.loads(self.cursor.read_text())["cursor"], "200")

    def test_listen_skips_already_seen(self):
        self.cursor.write_text(json.dumps({"cursor": "100"}))

        def fake_api(url, method="POST", payload=None, **kwargs):
            return [{"id": "100", "content": "old", "author": {"username": "p"}},
                    {"id": "150", "content": "new", "author": {"username": "p"}}]

        with patch.object(wa, "api", fake_api):
            wa.main(["listen", "--once"])
        events = [json.loads(ln) for ln in self.journal.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["content"] for e in events], ["new"])


    def test_message_text_prefers_content_then_embed(self):
        self.assertEqual(wa._message_text({"content": "hi"}), "hi")
        embed_only = {"content": "", "embeds": [{"description": "body 💎"}]}
        self.assertEqual(wa._message_text(embed_only), "body 💎")
        self.assertEqual(wa._message_text({"content": "", "embeds": []}), "(embed)")


class ArtRenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name) / "art-cache"
        self.cache_patch = patch.object(wa, "ART_CACHE", self.cache)
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def test_svg_uses_intrinsic_viewbox_and_2x(self):
        src = Path(self.temp.name) / "crane.svg"
        src.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 960"></svg>')
        captured = {}

        class Done:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            shot = [a for a in cmd if a.startswith("--screenshot=")][0]
            Path(shot.split("=", 1)[1]).write_bytes(b"png")
            return Done()

        with patch.object(wa.subprocess, "run", fake_run):
            out = wa.render_art(src)
        self.assertIn("--window-size=640,960", captured["cmd"])
        self.assertIn("--force-device-scale-factor=2", captured["cmd"])
        self.assertTrue(out.exists() and out.name.endswith("@2x.png"))

    def test_png_passes_through(self):
        src = Path(self.temp.name) / "already.png"
        src.write_bytes(b"png")
        self.assertEqual(wa.render_art(src), src)

    def test_bad_art_size_rejected(self):
        with self.assertRaises(SystemExit):
            wa._parse_art_size("banana")


class VisualPostingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.png = Path(self.temp.name) / "art.png"
        self.png.write_bytes(b"png")
        self.render_patch = patch.object(wa, "render_art", lambda p, size=None: self.png)
        self.render_patch.start()
        self.addCleanup(self.render_patch.stop)
        self.captured = {}

        def fake_api(url, method="POST", payload=None, **kwargs):
            self.captured.update(url=url, method=method, payload=payload, **kwargs)
            return {"id": "9", "embeds": [{}], "attachments": [{}]}

        self.api_patch = patch.object(wa, "api", fake_api)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.jp = patch.object(wa, "journal_path", lambda: Path(tempfile.mkdtemp()) / "j.ndjson")
        self.jp.start()
        self.addCleanup(self.jp.stop)

    def _payload(self):
        """The JSON payload, from the direct call or the multipart body."""
        if self.captured.get("payload") is not None:
            return self.captured["payload"]
        text = self.captured["body"].decode("utf-8", "replace")
        start = text.index('name="payload_json"')
        json_start = text.index("\r\n\r\n", start) + 4
        json_end = text.index("\r\n--", json_start)
        return json.loads(text[json_start:json_end])

    def test_gallery_makes_lead_card_and_attachment_embeds(self):
        wa.push(WEBHOOK, "", title="the inks", arts=["a.svg", "b.svg"])
        payload = self._payload()
        self.assertEqual(len(payload["embeds"]), 3)
        self.assertEqual(payload["embeds"][0]["title"], "the inks")
        self.assertEqual(payload["embeds"][1]["image"]["url"], "attachment://art.png")
        self.assertIn(b'filename="art.png"', self.captured["body"])
        self.assertTrue(self.captured["content_type"].startswith("multipart/form-data"))

    def test_gallery_cycles_palette_colors(self):
        wa.push(WEBHOOK, "", arts=["a.svg", "b.svg", "c.svg"])
        colors = [e["color"] for e in self._payload()["embeds"]]
        self.assertEqual(colors[0], wa.parse_color(wa.PALETTE[0]))
        self.assertEqual(colors[1], wa.parse_color(wa.PALETTE[1]))

    def test_gallery_clamps_to_ten(self):
        wa.push(WEBHOOK, "", arts=[f"{i}.svg" for i in range(12)])
        self.assertEqual(len(self._payload()["embeds"]), 10)


class MusicLaneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger_patch = patch.object(wa, "MUSIC_LEDGER", Path(self.temp.name) / "music.ndjson")
        self.ledger_patch.start()
        self.addCleanup(self.ledger_patch.stop)
        self.root_patch = patch.object(wa, "ROOT", Path(self.temp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.meta_patch = patch.object(wa, "youtube_meta", lambda url: {
            "title": "Deep Jungle Walk", "uploader": "Astrix", "duration": 545,
            "url": "https://www.youtube.com/watch?v=lIuEuJvKos4",
            "thumbnail": "https://i.ytimg.com/vi/lIuEuJvKos4/maxresdefault.jpg"})
        self.meta_patch.start()
        self.addCleanup(self.meta_patch.stop)
        self.captured = {}

        def fake_api(url, method="POST", payload=None, **kw):
            self.captured.update(payload=payload)
            return {"id": "77"}

        self.api_patch = patch.object(wa, "api", fake_api)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)
        self.jp = patch.object(wa, "journal_path", lambda: Path(self.temp.name) / "j.ndjson")
        self.jp.start()
        self.addCleanup(self.jp.stop)

    def test_music_posts_rich_embed_and_writes_ledgers(self):
        stdout = io.StringIO()
        with patch.object(wa, "webhook_url", lambda cli=None: WEBHOOK), redirect_stdout(stdout):
            code = wa.main(["music", "https://youtu.be/lIuEuJvKos4",
                            "--note", "the walk in", "--cue"])
        self.assertEqual(code, 0)
        embed = self.captured["payload"]["embeds"][0]
        self.assertEqual(embed["title"], "Deep Jungle Walk")
        self.assertEqual(embed["author"]["name"], "Astrix · youtube")
        self.assertEqual(embed["url"], "https://www.youtube.com/watch?v=lIuEuJvKos4")
        self.assertEqual(embed["image"]["url"],
                         "https://i.ytimg.com/vi/lIuEuJvKos4/maxresdefault.jpg")
        self.assertTrue((Path(self.temp.name) / "music.ndjson").exists())
        inbox = Path(self.temp.name) / "projects/01.02-new-beginnings/cues-inbox.ndjson"
        self.assertTrue(inbox.exists())
        summary = json.loads(stdout.getvalue())
        self.assertEqual(summary["duration"], "9:05")

    def test_youtube_meta_parses_ytdlp_json(self):
        self.meta_patch.stop()

        class Done:
            returncode = 0
            stdout = json.dumps({"title": "T", "uploader": "U", "duration": 61,
                                 "webpage_url": "https://youtu.be/x",
                                 "thumbnail": "https://t/img.jpg"})
            stderr = ""

        with patch.object(wa.subprocess, "run", lambda *a, **k: Done()):
            meta = wa.youtube_meta("https://youtu.be/x")
        self.assertEqual(meta["title"], "T")
        self.assertEqual(meta["duration"], 61)
        self.assertEqual(meta["thumbnail"], "https://t/img.jpg")

    def test_youtube_meta_failure_raises(self):
        self.meta_patch.stop()

        class Done:
            returncode = 1
            stdout = ""
            stderr = "ERROR: nope"

        with patch.object(wa.subprocess, "run", lambda *a, **k: Done()):
            with self.assertRaises(SystemExit):
                wa.youtube_meta("https://youtu.be/x")


if __name__ == "__main__":
    unittest.main()
