import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.config import Settings
from creality_k2_mcp.server import PrinterService


class RecordingClient:
    def __init__(self, *, k2_capable=True):
        self.calls = []
        self.k2_capable = k2_capable

    def get_objects(self, names):
        if not self.k2_capable:
            return {"print_stats": {"state": "standby"}}
        return {
            "print_stats": {"state": "standby"},
            "virtual_sdcard": {},
            "output_pin fan0": {},
            "output_pin fan2": {},
        }

    def post_path(self, path, **params):
        self.calls.append((path, params))
        return {}


class ControlsTests(unittest.TestCase):
    def test_write_tool_is_refused_when_write_is_disabled(self):
        client = RecordingClient()
        service = PrinterService(Settings(host="printer.local"), client=client)

        result = service.pause_print()

        self.assertIn("disabled", result.lower())
        self.assertEqual(client.calls, [])

    def test_temperature_uses_a_named_bounded_command_when_enabled(self):
        client = RecordingClient()
        service = PrinterService(Settings(host="printer.local", allow_write=True), client=client)

        result = service.set_temperature("nozzle", 220)

        self.assertIn("220", result)
        self.assertEqual(client.calls, [("/printer/gcode/script", {"script": "M104 S220"})])

    def test_temperature_above_the_ceiling_never_reaches_the_printer(self):
        client = RecordingClient()
        service = PrinterService(Settings(host="printer.local", allow_write=True), client=client)

        result = service.set_temperature("nozzle", 281)

        self.assertIn("Refused", result)
        self.assertEqual(client.calls, [])

    def test_write_is_refused_when_k2_capabilities_are_not_verified(self):
        client = RecordingClient(k2_capable=False)
        service = PrinterService(Settings(host="printer.local", allow_write=True), client=client)

        result = service.pause_print()

        self.assertIn("K2 capabilities", result)
        self.assertEqual(client.calls, [])



if __name__ == "__main__":
    unittest.main()
