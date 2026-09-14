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

    def test_audit_scans_dotenv_and_sensitive_key_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("API_KEY" + "=real-secret-value", encoding="utf-8")
            (root / "private.pem").write_text("private key material", encoding="utf-8")

            result = audit(root)

        self.assertTrue(result.has_errors)
        errors = "\n".join(result.errors)
        self.assertIn("environment file", errors)
        self.assertIn("sensitive private key file", errors)

    def test_audit_rejects_a_structured_secret_assignment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.json").write_text(
                "{" + '"api_' + 'key": "real-secret-value"' + "}", encoding="utf-8"
            )

            result = audit(root)

        self.assertTrue(result.has_errors)
        self.assertIn("possible secret assignment", "\n".join(result.errors))

    def test_audit_rejects_extensionless_and_putty_private_keys(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "id_rsa").write_text("-----BEGIN " + "OPENSSH PRIVATE KEY-----", encoding="utf-8")
            (root / "printer.ppk").write_text("PuTTY" + "-User-Key-File-2: ssh-rsa", encoding="utf-8")

            result = audit(root)

        self.assertTrue(result.has_errors)
        self.assertGreaterEqual("\n".join(result.errors).count("private key"), 2)


if __name__ == "__main__":
    unittest.main()
