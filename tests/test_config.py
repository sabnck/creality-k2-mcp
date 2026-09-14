import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.config import Settings


class SettingsTests(unittest.TestCase):
    def test_reads_explicit_local_configuration(self):
        settings = Settings.from_env({
            "K2_HOST": "printer.local",
            "K2_PORT": "7125",
            "K2_ALLOW_WRITE": "1",
        })

        self.assertEqual(settings.base_url, "http://printer.local:7125")
        self.assertTrue(settings.allow_write)

    def test_requires_a_printer_host(self):
        with self.assertRaisesRegex(ValueError, "K2_HOST"):
            Settings.from_env({})


if __name__ == "__main__":
    unittest.main()
