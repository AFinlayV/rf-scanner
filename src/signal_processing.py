import numpy as np

class SignalProcessing:
    def __init__(self, config):
        self.config = config

    def process(self, samples):
        """Convert IQ samples to a frequency spectrum using FFT and remove DC spike."""
        print("[SignalProcessing] Processing FFT...")

        # Apply FFT to convert IQ samples to frequency domain
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(samples)))

        # Remove DC spike (center frequency)
        center_bin = len(spectrum) // 2
        spectrum[center_bin - 1:center_bin + 2] = 0  # Zero out the center 3 bins

        return spectrum
