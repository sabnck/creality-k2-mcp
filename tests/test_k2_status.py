import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.profiles import K2Profile


K2_FIXTURE = {
    "extruder": {"temperature": 222.1, "target": 220.0},
    "heater_bed": {"temperature": 49.85, "target": 50.0},
    "print_stats": {
        "filename": "sanitized.gcode",
        "print_duration": 4321.33,
        "state": "printing",
        "message": "",
        "info": {"total_layer": None, "current_layer": None},
    },
    "virtual_sdcard": {
        "progress": 0.2532233326,
        "layer": 175,
        "layer_count": 1069,
    },
    "gcode_move": {"speed_factor": 1.0},
    "toolhead": {"position": [121.42, 120.38, 16.91]},
    "output_pin fan0": {"value": 1.0},
    "output_pin fan2": {"value": 0.8784313725},
}


class K2ProfileTests(unittest.TestCase):
    def test_uses_k2_virtual_sdcard_and_fan_pins(self):
        status = K2Profile().normalize_status(K2_FIXTURE)

        self.assertEqual(status["layer"], {"current": 175, "total": 1069})
        self.assertEqual(status["progress_percent"], 25.3)
        self.assertEqual(status["fans"], {"model_percent": 100, "side_percent": 88})

    def test_does_not_report_missing_vanilla_fan_as_the_model_fan(self):
        status = K2Profile().normalize_status({"fan": {"speed": 1.0}})

        self.assertIsNone(status["fans"]["model_percent"])


if __name__ == "__main__":
    unittest.main()
