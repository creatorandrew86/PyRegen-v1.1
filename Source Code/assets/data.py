from pathlib import Path
import json

ASSETS_DIR = Path(__file__).resolve().parent

with open(ASSETS_DIR / "ThermalConductivityData.json", "r", encoding="utf-8") as f:
    THERMAL_CONDUCTIVITY_DATA = json.load(f)

with open(ASSETS_DIR / "NozzleData.json", "r", encoding="utf-8") as f:
    NOZZLE_DATA = json.load(f)