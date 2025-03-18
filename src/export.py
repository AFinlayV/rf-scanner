import os
import json
import csv
import numpy as np
import math
from datetime import datetime
from src.config import CONFIG
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Directories for logs and exported data
LOGS_DIR = "logs"
DATA_DIR = "data"

# Use calibration_offset from config; default to -100 if not set.
CALIBRATION_OFFSET = CONFIG.get("calibration_offset", -100)

def convert_to_dbm(value):
    """
    Convert a raw FFT magnitude to dBm using:
        dBm = 10 * log10(value) + CALIBRATION_OFFSET
    Returns a whole number.
    """
    if value <= 0:
        return CALIBRATION_OFFSET
    return round(10 * math.log10(value) + CALIBRATION_OFFSET)

def export_csv(file_path, freqs, spectrum_dbm):
    """
    Export frequency and spectrum data to a CSV file in a format compatible with Shure Wireless Workbench.
    Each row contains:
      - Frequency in MHz (rounded to 3 decimal places)
      - Signal strength in dBm (whole number)
    No header row is included.
    """
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        for freq, level in zip(freqs, spectrum_dbm):
            freq_mhz = round(freq / 1e6, 3)
            writer.writerow([f"{freq_mhz:.3f}", level])

def get_today_session():
    """Return today's session identifier in YYYYMMDD format."""
    return datetime.now().strftime("%Y%m%d")

def load_logs_for_session(session_id):
    """
    Load and return a sorted list of log file paths from LOGS_DIR
    that contain today's session identifier in the filename.
    Assumes log filenames include the session (e.g., 'scan_20230321_...json').
    """
    logs = []
    for fname in os.listdir(LOGS_DIR):
        if fname.startswith("scan_") and fname.endswith(".json") and session_id in fname:
            logs.append(os.path.join(LOGS_DIR, fname))
    logs.sort()  # Sort in chronological order based on filename timestamp
    return logs

def main():
    session_id = get_today_session()
    logs = load_logs_for_session(session_id)
    if not logs:
        print("No logs found for today's session.")
        return

    # Load configuration frequencies from CONFIG in case log files lack a frequency array
    start_freq = CONFIG["start_frequency"]
    end_freq = CONFIG["end_frequency"]
    freq_step = CONFIG["frequency_step"]
    freqs_generated = np.arange(start_freq, end_freq, freq_step)

    # Load the most recent log file
    recent_log_file = logs[-1]
    with open(recent_log_file, "r") as f:
        recent_log = json.load(f)

    # Check if the log file contains a "freqs" field; if not, generate frequencies from CONFIG.
    raw_freqs = recent_log.get("freqs")
    if raw_freqs is None or np.ndim(raw_freqs) == 0:
        freqs = freqs_generated
    else:
        freqs = np.array(raw_freqs)

    # Load the raw spectrum data from the recent log
    recent_spectrum_raw = recent_log.get("spectrum")
    if recent_spectrum_raw is None or np.ndim(recent_spectrum_raw) == 0:
        print("No spectrum data found in recent log.")
        return
    recent_spectrum_raw = np.array(recent_spectrum_raw)
    recent_spectrum_dbm = np.array([convert_to_dbm(val) for val in recent_spectrum_raw])

    os.makedirs(DATA_DIR, exist_ok=True)
    recent_csv_file = os.path.join(DATA_DIR, "recent_scan.csv")
    export_csv(recent_csv_file, freqs, recent_spectrum_dbm)
    print(f"Exported recent scan to {recent_csv_file}")

    # For the average scan, load the last 10 logs (or fewer, if not available)
    logs_to_average = logs[-10:] if len(logs) >= 10 else logs
    spectra = []
    for log_file in logs_to_average:
        with open(log_file, "r") as f:
            log_data = json.load(f)
            spectrum = log_data.get("spectrum")
            if spectrum is not None and np.ndim(spectrum) > 0:
                spectra.append(np.array(spectrum))
    if not spectra:
        print("No valid spectra found for averaging.")
        return
    avg_spectrum_raw = np.mean(np.array(spectra), axis=0)
    avg_spectrum_dbm = np.array([convert_to_dbm(val) for val in avg_spectrum_raw])

    average_csv_file = os.path.join(DATA_DIR, "average_scan.csv")
    export_csv(average_csv_file, freqs, avg_spectrum_dbm)
    print(f"Exported average scan to {average_csv_file}")

if __name__ == "__main__":
    main()
