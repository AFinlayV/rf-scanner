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
        
        os.makedirs(self.log_directory, exist_ok=True)
        os.makedirs(self.data_directory, exist_ok=True)

    def save_log(self, scan_data):
        """
        Saves full scan data as a JSON file in the log directory.
        Expects scan_data to include a "timestamp" key.
        """
        timestamp = scan_data["timestamp"]
        filename = os.path.join(self.log_directory, f"scan_{timestamp}.json")
        with open(filename, "w") as f:
            json.dump(scan_data, f, indent=4)

    def format_for_wwb(self, scan_data):
        """
        Formats scan data into a DataFrame for WWB export.
        - Converts frequency from Hz to MHz (rounded to 3 decimals).
        - Rounds dBm values to 2 decimals.
        """
        frequencies_mhz = np.round(np.array(scan_data["frequencies"]) / 1e6, 3)
        power_levels_dbm = np.round(np.array(scan_data["power_levels"]), 2)
        df = pd.DataFrame({
            "Frequency (MHz)": frequencies_mhz,
            "Signal Strength (dBm)": power_levels_dbm
        })
        return df

    def update_recent_scan(self, scan_data):
        """
        Updates the most recent scan CSV file for WWB.
        """
        df = self.format_for_wwb(scan_data)
        recent_csv_path = os.path.join(self.data_directory, "recent_scan.csv")
        df.to_csv(recent_csv_path, index=False, header=False)

    def update_average_scan(self):
        """
        Computes the running average of the last N scans (if num_passes_for_average is set,
        otherwise averages all available scans) and updates the average_scan.csv file.
        """
        # Get list of JSON log files, sorted by filename (assuming timestamp in filename sorts chronologically)
        json_files = sorted([f for f in os.listdir(self.log_directory) if f.endswith(".json")])
        if self.num_passes_for_average and len(json_files) > self.num_passes_for_average:
            json_files = json_files[-self.num_passes_for_average:]

        all_scans = []
        frequencies = None
        for file in json_files:
            file_path = os.path.join(self.log_directory, file)
            with open(file_path, "r") as f:
                scan_data = json.load(f)
                all_scans.append(scan_data["power_levels"])
                # Assuming frequencies are the same for all scans, just grab once.
                if frequencies is None:
                    frequencies = scan_data["frequencies"]

        if not all_scans or frequencies is None:
            return

        # Compute average and format the values
        avg_power_levels = np.round(np.mean(all_scans, axis=0), 2)
        frequencies_mhz = np.round(np.array(frequencies) / 1e6, 3)
        avg_df = pd.DataFrame({
            "Frequency (MHz)": frequencies_mhz,
            "Signal Strength (dBm)": avg_power_levels
        })
        avg_csv_path = os.path.join(self.data_directory, "average_scan.csv")
        avg_df.to_csv(avg_csv_path, index=False, header=False)
