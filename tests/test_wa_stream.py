import importlib.util
import io
import json
import os
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

        def fake_push(webhook, text, title=None, wait=True, instance=None):
            pushed.append(instance)
            return {"id": f"id-{instance}"}

        stdout = io.StringIO()
        with patch.object(wa, "run_instance", self.fake_run), \
             patch.object(wa, "push", fake_push), \
             patch.object(wa, "webhook_url", lambda cli=None: WEBHOOK), \
             redirect_stdout(stdout):
            code = wa.main(["love", "--instances", "3"])
        self.assertEqual(code, 0)
        self.assertEqual(pushed, ["love-1", "love-2", "love-3"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["instances"][0]["id"], "id-love-1")


if __name__ == "__main__":
    unittest.main()
