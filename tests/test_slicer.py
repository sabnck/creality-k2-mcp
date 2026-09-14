import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.config import Settings
from creality_k2_mcp.slicer import ProfileCatalog, SlicePlanner


class SlicerTests(unittest.TestCase):
    def test_catalog_rejects_process_for_unknown_nozzle(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "No profiles"):
                ProfileCatalog(Path(directory)).list_for_nozzle("0.4")

    def test_planner_uses_existing_profiles_and_reports_ignored_overrides(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "profiles"
            for kind in ("machine", "process", "filament"):
                (root / kind).mkdir(parents=True)
            self._write_profile(root / "machine" / "Creality K2 0.4 nozzle.json", {})
            self._write_profile(
                root / "process" / "0.20mm Standard @Creality K2 0.4 nozzle.json",
                {"layer_height": "0.2"},
            )
            self._write_profile(
                root / "filament" / "Hyper PLA @Creality K2 0.4 nozzle.json",
                {},
            )
            model = Path(directory) / "model.3mf"
            model.write_bytes(b"not inspected by prepare")
            cli = Path(directory) / "CrealityPrint.exe"
            cli.write_bytes(b"")

            result = SlicePlanner(
                Settings(host="printer.local", cli_path=cli, profiles_path=root)
            ).prepare(
                model=model,
                nozzle="0.4",
                material="Hyper PLA",
                process="Standard",
                overrides={"layer_height": "0.24", "made_up_setting": "no"},
                output_dir=Path(directory) / "output",
            )

        self.assertIn("--slice", result["command"])
        self.assertEqual(result["applied_overrides"], {"layer_height": "0.24"})
        self.assertEqual(result["ignored_overrides"], ["made_up_setting"])

    @staticmethod
    def _write_profile(path: Path, payload: dict):
        path.write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
