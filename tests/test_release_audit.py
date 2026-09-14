import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit_public_release import audit


class ReleaseAuditTests(unittest.TestCase):
    def test_audit_rejects_a_private_ip(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bad.txt").write_text("host=" + "192.168." + "1.127", encoding="utf-8")

            result = audit(root)

        self.assertTrue(result.has_errors)
        self.assertIn("private network address", "\n".join(result.errors))

    def test_audit_accepts_a_public_placeholder(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.example").write_text("K2_HOST=YOUR_PRINTER_HOST\n", encoding="utf-8")

            result = audit(root)

        self.assertFalse(result.has_errors)

    def test_audit_rejects_print_artifacts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "personal-print.gcode").write_text("G1 X0", encoding="utf-8")

            result = audit(root)

        self.assertTrue(result.has_errors)
        self.assertIn("forbidden artifact", "\n".join(result.errors))


if __name__ == "__main__":
    unittest.main()
