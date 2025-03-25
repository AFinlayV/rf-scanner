import json
import os
import numpy as np
import pandas as pd

class Logger:
    def __init__(self, config):
        """
        Initializes the Logger.
        Expects config as a dict with at least:
          - "log_directory": directory to store JSON logs.
          - "num_passes_for_average": number of scans to average (optional).
        Assumes CSV export directory is "data/".
        """
        self.log_directory = config.get("log_directory", "logs")
        self.data_directory = "data"
        self.num_passes_for_average = config.get("num_passes_for_average", None)
        self.config = config
        
        os.makedirs(self.log_directory, exist_ok=True)
        os.makedirs(self.data_directory, exist_ok=True)

    def convert_to_dbm(self, value):
        if value <= 0:
            return -120  # Default floor for invalid values
        return round(10 * np.log10(value) - 100, 3)  # Apply calibration offset and round to 1 decimal place

    def save_log(self, scan_data):
        """
        Saves full scan data as a JSON file in the log directory.
        Expects scan_data to include a "timestamp" key.
        Now includes full configuration metadata for reference.
        """
        if self.config.get("test_mode", False):
            print("🧪 Test Mode: Skipping log save.")
            return
        timestamp = scan_data["timestamp"]
        # Load full config from config.json
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        try:
            with open(config_path, "r") as f:
                full_config = json.load(f)
        except Exception as e:
            print(f"⚠️ WARNING: Could not load full config: {e}")
            full_config = {}

        log_entry = {
            "timestamp": timestamp,
            "config": full_config,  # Store full config from file
            "frequencies": scan_data["frequencies"],
            "power_levels": scan_data["power_levels"],
            "location": {
                "city": full_config.get("city", "Unknown"),
                "venue": full_config.get("venue", "Unknown"),
                "zip_code": full_config.get("zip_code", "Unknown")
            }
        }

        filename = os.path.join(self.log_directory, f"scan_{timestamp}.json")
        with open(filename, "w") as f:
            json.dump(log_entry, f, indent=4)

        print(f"✅ Scan log saved: {filename}")

    def format_for_wwb(self, scan_data):
        """
        Formats scan data into a DataFrame for WWB export.
        - Converts frequency from Hz to MHz (rounded to 3 decimals).
        - Converts power levels to negative dBm.
        """
        frequencies_mhz = np.round(np.array(scan_data["frequencies"]) / 1e6, 3)
        power_levels_dbm = np.array([self.convert_to_dbm(val) for val in scan_data["power_levels"]])

        df = pd.DataFrame({
            "Frequency (MHz)": frequencies_mhz,
            "Signal Strength (dBm)": power_levels_dbm
        })
        return df

    def update_recent_scan(self, scan_data):
        """
        Saves the most recent scan pass as a CSV file.
        Also updates the max scan file.
        """
        if self.config.get("test_mode", False):
            print("🧪 Test Mode: Skipping recent scan save.")
            return
        df = self.format_for_wwb(scan_data)
        recent_csv_path = os.path.join(self.data_directory, "recent_scan.csv")
        df.to_csv(recent_csv_path, index=False, header=False)
        print(f"✅ Recent scan saved to {recent_csv_path}")

        # Update max scan file with new data
        self.update_max_scan(scan_data)

    def update_max_scan(self, scan_data):
        """
        Updates the max scan file by comparing current scan values against stored max values.
        Keeps the highest observed signal strength for each frequency.
        """
        if self.config.get("test_mode", False):
            print("🧪 Test Mode: Skipping max scan update.")
            return
        max_csv_path = os.path.join(self.data_directory, "max_scan.csv")

        # Format current scan data
        df_new = self.format_for_wwb(scan_data)

        # If max_scan.csv exists, compare values
        if os.path.exists(max_csv_path):
            df_old = pd.read_csv(max_csv_path, header=None, names=["Frequency (MHz)", "Signal Strength (dBm)"])

            # Merge old and new data, keeping the maximum power level for each frequency
            df_merged = df_old.merge(df_new, on="Frequency (MHz)", how="outer", suffixes=("_old", "_new"))
            df_merged["Signal Strength (dBm)"] = df_merged[["Signal Strength (dBm)_old", "Signal Strength (dBm)_new"]].max(axis=1)

            # Drop extra columns and sort by frequency
            df_final = df_merged[["Frequency (MHz)", "Signal Strength (dBm)"]].sort_values("Frequency (MHz)")
        else:
            df_final = df_new  # No previous data, use current scan directly

        # Save updated max scan data
        df_final.to_csv(max_csv_path, index=False, header=False)
        print(f"✅ Max scan updated. Saved to {max_csv_path}")

    def load_recent_logs(self, limit=5):
        """Loads up to 'limit' most recent scan logs and ensures valid data."""
        log_dir = self.config.get("test_log_directory") if self.config.get("test_mode", False) else self.log_directory
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")], reverse=True)[:limit]
        scan_passes = []

        print(f"📂 DEBUG: Loading logs from {log_dir}")
        print(f"📂 DEBUG: Found {len(log_files)} log files.")

        for file in log_files:
            file_path = os.path.join(log_dir, file)
            with open(file_path, "r") as f:
                data = json.load(f)
                if "frequencies" in data and "power_levels" in data:
                    scan_passes.append(data)
                    print(f"📂 DEBUG: Loaded {file} with valid data.")
                else:
                    print(f"⚠️ WARNING: {file} missing 'frequencies' or 'power_levels' and will be ignored.")

        return scan_passes
