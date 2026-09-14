import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectBoundaryTests(unittest.TestCase):
    def test_example_configuration_has_no_private_network_address(self):
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertNotIn("192.168.", content)
        self.assertIn("YOUR_PRINTER_HOST", content)

    def test_gitignore_excludes_runtime_and_personal_artifacts(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for entry in (".env", "*.gcode", "*.3mf", "runtime/", "__pycache__/"):
            with self.subTest(entry=entry):
                self.assertIn(entry, ignored)


if __name__ == "__main__":
    unittest.main()
