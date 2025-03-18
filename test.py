#!/usr/bin/env python3
import sys
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt

# Add the 'src' directory to the module search path.
sys.path.append(os.path.join(os.getcwd(), "src"))

from config import load_config
from logger import Logger

# Try importing the real scan function; if missing, fall back to dummy.
try:
    from data_acquisition import scan_frequencies
except ImportError:
    print("scan_frequencies not found in data_acquisition; using dummy scan function.")
    def scan_frequencies(start_freq, end_freq, step_size, gain, samples_per_scan, sample_rate, freq_correction):
        frequencies = list(np.arange(start_freq, end_freq, step_size))
        power_levels = list(np.random.uniform(-100, -50, len(frequencies)))
        return {"frequencies": frequencies, "power_levels": power_levels}

# Dummy signal processing function (if needed)
try:
    from signal_processing import process_iq_samples
except ImportError:
    def process_iq_samples(raw_data):
        return {"power_levels": raw_data}

# Dummy visualization if no module is provided.
try:
    import visualization
except ImportError:
    print("Visualization module not found; using dummy visualization.")
    class DummyVisualization:
        def __init__(self):
            self.fig, self.ax = plt.subplots()
            self.line, = self.ax.plot([], [], 'r-', label="Recent Scan")
            self.ax.set_xlabel("Frequency (MHz)")
            self.ax.set_ylabel("Signal Strength (dBm)")
            self.ax.legend()
        def update_plot(self, scan_data):
            freqs = np.array(scan_data["frequencies"]) / 1e6  # Hz -> MHz
            power = scan_data["power_levels"]
            self.line.set_data(freqs, power)
            self.ax.relim()
            self.ax.autoscale_view()
            plt.draw()
        def show(self):
            plt.show()
    visualization = DummyVisualization()

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    # Load the final config from config.py.
    config = load_config()
    
    # Check for start/end frequencies—config.py should add these overrides.
    if "start_frequency" not in config or "end_frequency" not in config:
        print("Error: 'start_frequency' and/or 'end_frequency' missing from final config. Check your config.py overrides.")
        return

    start_freq      = config["start_frequency"]
    end_freq        = config["end_frequency"]
    step_size       = config["frequency_step"]
    gain            = config["gain"]
    samples_per_scan= config.get("samples_per_scan", 1024)
    sample_rate     = config.get("sample_rate", 2048000)
    freq_correction = config.get("freq_correction", 0)
    selected_band   = config.get("selected_band", "Unknown")
    
    # Initialize the Logger with the full config.
    logger = Logger(config)
    
    print(f"📡 Starting RF Scan for Band: {selected_band}")
    print(f"🔍 Scanning from {start_freq/1e6:.3f} MHz to {end_freq/1e6:.3f} MHz")
    print(f"⚙️ Frequency Step: {step_size/1e3:.1f} kHz | Gain: {gain} dB")
    
    # Perform the scan.
    try:
        scan_results = scan_frequencies(start_freq, end_freq, step_size, gain, samples_per_scan, sample_rate, freq_correction)
    except Exception as e:
        print(f"❌ Error during scanning: {e}")
        return
    
    if not scan_results or "frequencies" not in scan_results or "power_levels" not in scan_results:
        print("⚠️ Scan returned empty results.")
        return

    # If raw I/Q samples are provided, process them.
    if "raw_iq" in scan_results:
        processed = process_iq_samples(scan_results["raw_iq"])
        scan_results["power_levels"] = processed.get("power_levels", scan_results["power_levels"])
    
    # Build the scan data dictionary.
    scan_data = {
        "timestamp": get_timestamp(),
        "frequencies": scan_results["frequencies"],
        "power_levels": scan_results["power_levels"]
    }
    
    try:
        # Log the full scan and update WWB export CSVs.
        logger.save_log(scan_data)
        logger.update_recent_scan(scan_data)
        logger.update_average_scan()
        print("✅ Scan Complete! Log saved and WWB files updated in /data/")
    except Exception as e:
        print(f"❌ Error during logging/export: {e}")
    
    # Update visualization if available.
    try:
        if hasattr(visualization, "update_plot"):
            visualization.update_plot(scan_data)
            print("✅ Visualization updated. Close the window to exit.")
            if hasattr(visualization, "show"):
                visualization.show()
    except Exception as e:
        print(f"❌ Error during visualization: {e}")

if __name__ == "__main__":
    main()
