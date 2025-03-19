#!/usr/bin/env python3
import sys
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import json

# Ensure the 'src' directory is in the module search path.
sys.path.append(os.path.join(os.getcwd(), "src"))

# Import configuration and modules.
from config import CONFIG, BANDS
from logger import Logger
from data_acquisition import DataAcquisition
from signal_processing import SignalProcessing
from visualization import Visualization

def get_timestamp():
    """Return the current timestamp in YYYYMMDD_HHMMSS format."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    """Perform multiple scan passes, log each, update visualization, and compute running average."""
    config = CONFIG
    test_mode = config.get("test_mode", False)
    flask_mode = config.get("flask_mode", False)

    # Validate required configuration parameters.
    start_freq = config.get("start_frequency")
    end_freq = config.get("end_frequency")
    freq_step = config.get("frequency_step")
    num_passes = config.get("num_passes_for_average", 1)

    if start_freq is None or end_freq is None or freq_step is None:
        print("❌ Error: Missing required frequency configuration in config.json.")
        return

    print(f"📡 Starting scan from {start_freq/1e6:.3f} MHz to {end_freq/1e6:.3f} MHz")
    print(f"🔄 Will perform {num_passes} pass(es) to average.")

    # Initialize modules.
    try:
        daq = DataAcquisition(config) if not test_mode else None
    except Exception as e:
        print(f"❌ Failed to initialize DataAcquisition: {e}")
        return

    sp = SignalProcessing(config)
    logger = Logger(config)
    vis = Visualization(config, BANDS)

    # If in test mode, load scan logs from test_log_directory
    scan_logs = []
    if test_mode:
        log_dir = config.get("test_log_directory", "src/test_data")
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")])
        for log_file in log_files:
            with open(os.path.join(log_dir, log_file), "r") as f:
                scan_logs.append(json.load(f))
        print(f"🧪 Test Mode Enabled: Loaded {len(scan_logs)} past scans from {log_dir}")

    # Loop over the number of passes.
    for pass_num in range(num_passes):
        print(f"\n=== Running Scan Pass {pass_num + 1} of {num_passes} ===")
        freqs_collected = []
        peak_power_levels = []

        # Simulate scanning
        if test_mode:
            scan_data = scan_logs[pass_num % len(scan_logs)]  # Loop through logs
            freqs_collected = scan_data["frequencies"]
            peak_power_levels = scan_data["power_levels"]
            for i, freq in enumerate(freqs_collected):
                progress_percent = (i / len(freqs_collected)) * 100
                vis.update_status(freq, progress_percent)
                #time.sleep(0.1)  # Simulate scan delay
        else:
            for freq, iq_samples in daq.scan_range():
                try:
                    spectrum = sp.process(iq_samples)
                    peak_power = np.max(spectrum)
                except Exception as proc_err:
                    print(f"❌ Error processing samples at {freq/1e6:.3f} MHz: {proc_err}")
                    continue

                freqs_collected.append(freq)
                peak_power_levels.append(peak_power)
                progress_percent = (freq - start_freq) / (end_freq - start_freq) * 100
                vis.update_status(freq, progress_percent)

        # Convert collected data to numpy arrays.
        freqs_array = np.array(freqs_collected)
        power_array = np.array(peak_power_levels)

        # Create scan data dictionary for this pass.
        scan_data = {
            "timestamp": get_timestamp(),
            "frequencies": freqs_array.tolist(),
            "power_levels": power_array.tolist()
        }

        # Log the scan data and update the recent scan CSV.
        try:
            if test_mode:
                test_filename = f"scan_{get_timestamp()}_test.json"
                test_log_path = os.path.join(config.get("log_directory", "logs"), test_filename)
                with open(test_log_path, "w") as f:
                    json.dump(scan_data, f, indent=4)
                print(f"🧪 Test Mode: Log saved as {test_filename}")

                # Save test data CSVs
                recent_csv_path = os.path.join(config.get("data_directory", "data"), "recent_scan_test.csv")
                max_csv_path = os.path.join(config.get("data_directory", "data"), "max_scan_test.csv")
                
                df = logger.format_for_wwb(scan_data)
                df.to_csv(recent_csv_path, index=False, header=False)
                df.to_csv(max_csv_path, index=False, header=False)
                print(f"🧪 Test Mode: Recent and Max scan data saved with '_test' filenames.")
            
            else:
                logger.save_log(scan_data)
                logger.update_recent_scan(scan_data)
                print(f"✅ Pass {pass_num + 1}: Data logged and recent CSV updated.")
        except Exception as log_err:
            print(f"❌ Error logging data for pass {pass_num + 1}: {log_err}")

        # Update spectrum visualization.
        try:
            vis.update_spectrum(power_array)
            plt.pause(0.1)
        except Exception as vis_err:
            print(f"❌ Error updating visualization for pass {pass_num + 1}: {vis_err}")

        time.sleep(0.5)  # Delay between passes

    # After completing all passes, update the average scan CSV.
    try:
        if not test_mode:
            logger.update_average_scan()
        print("✅ All passes completed. Average CSV updated.")
    except Exception as avg_err:
        print(f"❌ Error updating average scan CSV: {avg_err}")

    print("✅ Final visualization. Close the window to exit.")
    plt.show()

    # Clean up SDR resources.
    if not test_mode:
        try:
            daq.close()
            print("🔻 SDR device closed.")
        except Exception as close_err:
            print(f"❌ Error closing SDR device: {close_err}")

if __name__ == "__main__":
    main()
