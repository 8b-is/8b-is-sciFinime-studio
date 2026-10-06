import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/zimage_plate.py'
spec = importlib.util.spec_from_file_location('zimage_plate', SCRIPT)
plate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plate)


class BlueprintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.home_patch = patch.object(plate.Path, 'home', return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def make_file(self, name):
        path = self.home / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}')
        return path

    def test_explicit_wins_over_environment(self):
        explicit = self.make_file('explicit.json')
        os.environ['COMFYUI_ZIMAGE_BLUEPRINT'] = str(self.home / 'missing.json')
        self.assertEqual(plate.resolve_blueprint(str(explicit)), explicit)

    def test_environment_override(self):
        configured = self.make_file('custom.json')
        os.environ['COMFYUI_ZIMAGE_BLUEPRINT'] = str(configured)
        self.assertEqual(plate.resolve_blueprint(), configured)

    def test_discovery_both_layouts(self):
        standard = self.make_file('ComfyUI/blueprints/' + plate.BLUEPRINT_NAME)
        self.assertEqual(plate.resolve_blueprint(), standard)
        legacy = self.make_file('ComfyUI-Installs/ComfyUI/ComfyUI/blueprints/' + plate.BLUEPRINT_NAME)
        self.assertEqual(plate.resolve_blueprint(), legacy)

    def test_bad_configuration_does_not_fall_back(self):
        self.make_file('ComfyUI/blueprints/' + plate.BLUEPRINT_NAME)
        os.environ['COMFYUI_ZIMAGE_BLUEPRINT'] = str(self.home / 'missing.json')
        with self.assertRaisesRegex(FileNotFoundError, 'Set --blueprint'):
            plate.resolve_blueprint()

    def test_missing_blueprint_cli_fails_before_network(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--prompt', 'test',
            '--blueprint', str(self.home / 'missing.json'), '--url', 'invalid://no-network'],
            capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Set --blueprint', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
