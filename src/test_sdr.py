#!/usr/bin/env python3
import sys
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import time

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
        daq = DataAcquisition(config)
    except Exception as e:
        print(f"❌ Failed to initialize DataAcquisition: {e}")
        return

    sp = SignalProcessing(config)
    logger = Logger(config)
    vis = Visualization(config, BANDS)

    # Loop over the number of passes.
    for pass_num in range(num_passes):
        print(f"\n=== Running Scan Pass {pass_num + 1} of {num_passes} ===")
        freqs_collected = []
        peak_power_levels = []

        # Sweep through the frequency range.
        for freq, iq_samples in daq.scan_range():
            try:
                # Process IQ samples with FFT.
                spectrum = sp.process(iq_samples)
                # Use the peak value as the signal strength indicator.
                peak_power = np.max(spectrum)
            except Exception as proc_err:
                print(f"❌ Error processing samples at {freq/1e6:.3f} MHz: {proc_err}")
                continue

            freqs_collected.append(freq)
            peak_power_levels.append(peak_power)

            # Update real-time visualization: progress bar and current frequency.
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
            logger.save_log(scan_data)
            logger.update_recent_scan(scan_data)
            print(f"✅ Pass {pass_num + 1}: Data logged and recent CSV updated.")
        except Exception as log_err:
            print(f"❌ Error logging data for pass {pass_num + 1}: {log_err}")

        # Update spectrum visualization with the current sweep.
        try:
            vis.update_spectrum(power_array)
            plt.pause(0.1)  # Short pause to refresh the GUI.
        except Exception as vis_err:
            print(f"❌ Error updating visualization for pass {pass_num + 1}: {vis_err}")

        # Optional: small delay between passes (if needed by your SDR)
        time.sleep(0.5)

    # After completing all passes, update the average scan CSV.
    try:
        logger.update_average_scan()
        print("✅ All passes completed. Average CSV updated in 'data/' directory.")
    except Exception as avg_err:
        print(f"❌ Error updating average scan CSV: {avg_err}")

    print("✅ Final visualization. Close the window to exit.")
    plt.show()  # Block until the window is closed.

    # Clean up SDR resources.
    try:
        daq.close()
        print("🔻 SDR device closed.")
    except Exception as close_err:
        print(f"❌ Error closing SDR device: {close_err}")

if __name__ == "__main__":
    main()
