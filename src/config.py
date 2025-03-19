import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.json")
BANDS_PATH = os.path.join(os.path.dirname(__file__), "data/psm1000_bands.json")

def load_config():
    """Load configuration from config.json in the project root."""
    with open(CONFIG_PATH, "r") as f:
        config_data = json.load(f)
    
    # Ensure test_mode exists in the config
    if "test_mode" not in config_data:
        config_data["test_mode"] = False  # Default to False if not specified

    return config_data

def load_bands():
    """Load available PSM 1000 frequency bands."""
    with open(BANDS_PATH, "r") as f:
        bands_data = json.load(f)
    if isinstance(bands_data, dict) and "bands" in bands_data:
        return bands_data["bands"]
    return bands_data

CONFIG = load_config()
BANDS = load_bands()

# Band override
if "selected_band" in CONFIG:
    selected_band_name = CONFIG["selected_band"]
    print(f"🔍 Looking for band: {selected_band_name}")
    band = next((b for b in BANDS if b["band"] == selected_band_name), None)
    if band:
        print(f"✅ Band found: {band}")
        CONFIG["start_frequency"] = band["frequency_range_hz"]["start"]
        CONFIG["end_frequency"] = band["frequency_range_hz"]["end"]
        print(f"🎯 Overridden CONFIG: {CONFIG}")
    else:
        print(f"⚠️ Warning: Selected band '{selected_band_name}' not found in psm1000_bands.json!")

print(f"📜 FINAL CONFIG: {CONFIG}")
