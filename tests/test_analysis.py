import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.analysis import analyze_3mf, analyze_gcode


class AnalysisTests(unittest.TestCase):
    def test_analyze_gcode_reads_estimated_time_and_filament(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "part.gcode"
            path.write_text(
                "; estimated printing time = 4h25m\n"
                "; total filament weight [g] = 52.96\n"
                "; total layer number = 1069\nG1 X0\n",
                encoding="utf-8",
            )

            result = analyze_gcode(path)

        self.assertEqual(result["estimated_time"], "4h25m")
        self.assertEqual(result["filament_weight_g"], 52.96)
        self.assertEqual(result["total_layers"], 1069)

    def test_analyze_3mf_reads_embedded_project_settings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "part.3mf"
            settings = {"printer_model": "Creality K2", "layer_height": "0.2"}
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("Metadata/project_settings.config", json.dumps(settings))

            result = analyze_3mf(path)

        self.assertEqual(result["settings_count"], 2)
        self.assertEqual(result["settings"]["printer_model"], "Creality K2")
        self.assertTrue(result["is_k2_project"])


if __name__ == "__main__":
    unittest.main()
