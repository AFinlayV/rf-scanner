from rtlsdr import RtlSdr
import numpy as np
import time
from rtlsdr.rtlsdr import LibUSBError

class DataAcquisition:
    def __init__(self, config):
        self.config = config
        self.test_mode = config.get("test_mode", False)

        if not self.test_mode:
            self.sdr = RtlSdr()

            # Apply initial SDR settings
            self.sdr.sample_rate = config["sample_rate"]
            self.sdr.gain = config["gain"]
            self.sdr.freq_correction = config["freq_correction"]

    def scan(self, frequency):
        """Grab IQ samples from RTL-SDR or return simulated data in test mode."""
        if self.test_mode:
            print(f"🧪 Test Mode: Simulating scan at {frequency / 1e6:.3f} MHz")
            iq_samples = np.random.normal(0, 0.1, self.config["samples_per_scan"]) + \
                         1j * np.random.normal(0, 0.1, self.config["samples_per_scan"])
            return frequency, iq_samples.astype(np.complex64)

        max_retries = 3  # Number of attempts before giving up
        retry_delay = 1  # Seconds to wait before retrying

        for attempt in range(max_retries):
            try:
                self.sdr.center_freq = frequency
                print(f"[DataAcquisition] Scanning {self.sdr.center_freq / 1e6:.3f} MHz...")

                iq_samples = self.sdr.read_samples(self.config["samples_per_scan"])  # Get real samples
                iq_samples = np.array(iq_samples, dtype=np.complex64)  # Ensure NumPy format

                return self.sdr.center_freq, iq_samples

            except LibUSBError as e:
                print(f"⚠️ SDR USB Error: {e}. Attempt {attempt + 1} of {max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    print(f"❌ Failed to set frequency {frequency / 1e6:.3f} MHz after {max_retries} attempts.")
                    return frequency, np.zeros(self.config["samples_per_scan"], dtype=np.complex64)  # Return empty samples on failure

    def scan_range(self):
        """Scan from start_frequency to end_frequency in steps."""
        start_freq = self.config["start_frequency"]
        end_freq = self.config["end_frequency"]
        step = self.config["frequency_step"]

        frequency_list = np.arange(start_freq, end_freq, step)
        for freq in frequency_list:
            yield self.scan(freq)  # Yield each scan result

    def close(self):
        """Clean up SDR resources if not in test mode."""
        if not self.test_mode:
            self.sdr.close()
