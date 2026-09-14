import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp.server.mcpserver import Image

from creality_k2_mcp.config import Settings
from creality_k2_mcp.server import PrinterService, create_server


class FakeClient:
    def get_objects(self, names):
        return {
            "print_stats": {"state": "printing", "print_duration": 3600},
            "virtual_sdcard": {"progress": 0.5, "layer": 2, "layer_count": 4},
            "output_pin fan0": {"value": 1.0},
            "output_pin fan2": {"value": 0.5},
        }


class ServerTests(unittest.TestCase):
    def test_snapshot_returns_mcp_image_for_a_jpeg(self):
        service = PrinterService(
            Settings(host="printer.local"),
            client=FakeClient(),
            snapshot_fetcher=lambda: b"\xff\xd8fake-jpeg",
        )

        result = service.snapshot()

        self.assertIsInstance(result, Image)

    def test_status_includes_a_derived_remaining_estimate(self):
        service = PrinterService(Settings(host="printer.local"), client=FakeClient())

        result = service.printer_status()

        self.assertEqual(result["remaining"], "01:00:00")

    def test_create_server_registers_the_k2_tools(self):
        server = create_server(Settings(host="printer.local"))

        self.assertEqual(server.name, "creality-k2-mcp")


if __name__ == "__main__":
    unittest.main()
