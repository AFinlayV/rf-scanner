from rtlsdr import RtlSdr
import numpy as np

class DataAcquisition:
    def __init__(self, config):
        self.config = config
        self.sdr = RtlSdr()

        # Apply initial SDR settings
        self.sdr.sample_rate = config["sample_rate"]
        self.sdr.gain = config["gain"]
        self.sdr.freq_correction = config["freq_correction"]

    def scan(self, frequency):
        """Grab IQ samples from RTL-SDR at a specific frequency."""
        self.sdr.center_freq = frequency
        print(f"[DataAcquisition] Scanning {self.sdr.center_freq / 1e6:.3f} MHz...")

        iq_samples = self.sdr.read_samples(self.config["samples_per_scan"])  # Get real samples
        iq_samples = np.array(iq_samples, dtype=np.complex64)  # Ensure NumPy format

        return self.sdr.center_freq, iq_samples

    def scan_range(self):
        """Scan from start_frequency to end_frequency in steps."""
        start_freq = self.config["start_frequency"]
        end_freq = self.config["end_frequency"]
        step = self.config["frequency_step"]

        frequency_list = np.arange(start_freq, end_freq, step)
        for freq in frequency_list:
            yield self.scan(freq)  # Yield each scan result

    def close(self):
        """Clean up SDR resources."""
        self.sdr.close()
