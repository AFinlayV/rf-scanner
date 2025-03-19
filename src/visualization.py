import matplotlib.pyplot as plt
import numpy as np

class Visualization:
    def __init__(self, config, bands):
        self.config = config
        self.start_freq = config["start_frequency"]
        self.end_freq = config["end_frequency"]
        self.freq_step = config["frequency_step"]

        self.bands = bands  # All available bands
        self.selected_band = self.get_band_info(config.get("selected_band", ""))

        # Create a frequency axis based on number of steps
        num_steps = (self.end_freq - self.start_freq) // self.freq_step
        self.freqs = np.linspace(self.start_freq, self.end_freq, num=num_steps)
        
        self.spectrum_history = []

        # Set up the main figure and adjust layout
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.patch.set_facecolor("black")
        self.ax.set_facecolor("black")
        self.ax.set_xlabel("Frequency (MHz)", color="white")
        self.ax.set_ylabel("Signal Strength (dB)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, color="gray", linestyle="--", linewidth=0.5)

        # Adjust layout to ensure x-axis labels are visible
        self.fig.subplots_adjust(bottom=0.25, top=0.85)

        # Progress Bar (Top)
        self.progress_ax = self.fig.add_axes([0.1, 0.87, 0.8, 0.03])
        self.progress_ax.set_xlim(0, 100)
        self.progress_ax.set_ylim(0, 1)
        self.progress_ax.set_xticks([])
        self.progress_ax.set_yticks([])
        self.progress_ax.set_facecolor("black")
        self.progress_bar, = self.progress_ax.plot([0, 0], [0.5, 0.5], color="cyan", linewidth=8)

        # Info Box (Bottom)
        self.info_ax = self.fig.add_axes([0.1, 0.05, 0.8, 0.15])
        self.info_ax.set_facecolor("black")
        self.info_ax.set_xticks([])
        self.info_ax.set_yticks([])

        self.current_freq_text = self.info_ax.text(
            0.5, 0.65, "", transform=self.info_ax.transAxes,
            fontsize=20, fontweight="bold", color="cyan", ha="center", va="center"
        )
        self.details_text = self.info_ax.text(
            0.5, 0.25, self.get_band_text(), transform=self.info_ax.transAxes,
            fontsize=10, color="white", ha="center", va="center"
        )

    def get_band_info(self, selected_band_name):
        """Retrieve band info based on selected band name."""
        return next((b for b in self.bands if b["band"] == selected_band_name), None)

    def get_band_text(self):
        """Generate display text for the selected band."""
        if not self.selected_band:
            return "No Band Selected"
        band = self.selected_band
        # Format: Band: H22 | Freq: 518.000-584.000 MHz | Regions: US, Canada, Latin America | RF Power: 10mW, 50mW, 100mW
        return (f"Band: {band['band']} | "
                f"Freq: {band['frequency_range_hz']['start']/1e6:.3f}-{band['frequency_range_hz']['end']/1e6:.3f} MHz | "
                f"Regions: {', '.join(band['regions_allowed'])} | "
                f"RF Power: {', '.join(band['rf_output_power_options'])}")

    def update_status(self, current_freq, progress):
        """Update the current frequency display and progress bar."""
        self.ax.set_title(f"Scanning: {current_freq / 1e6:.3f} MHz", color="white")
        self.progress_bar.set_data([0, progress], [0.5, 0.5])
        self.current_freq_text.set_text(f"{current_freq / 1e6:.3f} MHz")
        self.details_text.set_text(self.get_band_text())
        plt.pause(0.01)

    def update_spectrum(self, spectrum):
        """Update the main spectrum plot with a new full sweep."""
        self.ax.clear()
        self.ax.set_facecolor("black")
        self.ax.set_xlabel("Frequency (MHz)", color="white")
        self.ax.set_ylabel("Signal Strength (dB)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, color="gray", linestyle="--", linewidth=0.5)

        # Ensure frequency axis length matches spectrum length
        if len(self.freqs) != len(spectrum):
            print(f"⚠️ Dimension Mismatch: freqs={len(self.freqs)}, spectrum={len(spectrum)}. Adjusting...")
            self.freqs = np.linspace(self.start_freq, self.end_freq, num=len(spectrum))
        
        # Set x-ticks to show frequency labels at the bottom
        xticks = np.linspace(self.start_freq / 1e6, self.end_freq / 1e6, num=10)
        self.ax.set_xticks(xticks)
        self.ax.set_xticklabels([f"{x:.1f}" for x in xticks], color="white")

        # Store the new sweep in history (keep last 10 sweeps)
        self.spectrum_history.append(spectrum)
        if len(self.spectrum_history) > 10:
            self.spectrum_history.pop(0)

        # Auto-scale y-axis based on all sweep values
        all_vals = np.concatenate(self.spectrum_history)
        self.ax.set_ylim(np.min(all_vals) * 0.9, np.max(all_vals) * 1.1)

        # Plot previous sweeps in grey
        for sweep in self.spectrum_history[:-1]:
            self.ax.plot(self.freqs / 1e6, sweep, color="gray", linewidth=0.5, alpha=0.5)

        # Plot max sweep in blue if available
        if len(self.spectrum_history) > 1:
            max_spectrum = np.max(self.spectrum_history, axis=0)
            self.ax.plot(self.freqs / 1e6, max_spectrum, color="blue", linewidth=1.0, label="Max Observed Sweep")

        # Plot most recent sweep in red with a thinner line
        self.ax.plot(self.freqs / 1e6, self.spectrum_history[-1], color="red", linewidth=0.8, label="Most Recent Sweep")

        self.ax.legend()
        plt.pause(0.05)
