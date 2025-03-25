RF Scanner with RTL-SDR and Shure Wireless Workbench Integration

Version: 1.0
Author: Alex Finlay V
Status: Functional Prototype

Overview

This project is a custom RF scanning tool designed for wireless in-ear monitor (IEM) frequency coordination in live touring environments. The system leverages a low-cost RTL-SDR receiver to scan across the frequency bands used by the Shure PSM 1000 series. It processes RF data using FFT, visualizes the spectrum in real time, logs scan data, and exports CSV files formatted for Shure Wireless Workbench (WWB) for further frequency coordination.

Key Features
	•	Continuous RF Spectrum Scanning: Scans across a user-selected frequency band, based on Shure PSM 1000 specifications.
	•	FFT Signal Processing: Converts raw I/Q samples into frequency-domain data with signal strength values expressed in dBm.
	•	Real-Time Visualization: Uses Matplotlib to display:
	•	The current spectrum with a black background.
	•	Previous sweeps (displayed in grey).
	•	A running average of the last X scans (displayed in blue).
	•	The most recent scan (displayed in red).
	•	A progress bar at the top showing the scan progress.
	•	An information box at the bottom showing the current frequency (in large, bold cyan text) and detailed band information (in smaller white text).
	•	Data Logging: Saves the most recent scan and the running average of the scans as CSV files in a format compatible with Shure Wireless Workbench. Additionally, a JSON backup of the average spectrum is maintained.
	•	Configurable via JSON: The system reads settings from a configuration file (config.json), including parameters such as sample rate, frequency step, gain, and the selected band. Band data is loaded from a separate file (psm1000_bands.json), which includes frequency ranges, allowed regions, RF output power options, and regulatory information.

System Architecture and File Structure

File Structure
```
rf_scanner/
│
├── data/
│   ├── recent_scan.csv         # CSV file containing the most recent scan
│   ├── average_scan.csv        # CSV file containing the running average scan
│   └── average_spectrum.json   # JSON file with backup of the averaged spectrum data
│
├── logs/                       # Directory for raw scan logs (timestamped JSON files)
│
├── src/
│   ├── config.py               # Loads configuration and band data; applies band selection overrides
│   ├── data_acquisition.py     # Interfaces with the RTL-SDR to perform frequency scans
│   ├── signal_processing.py    # Applies FFT to the captured RF data and computes signal levels
│   ├── visualization.py        # Handles the graphical user interface using Matplotlib
│   ├── logger.py               # Logs scan data and exports CSV files in WWB-compatible format
│   └── test_sdr.py             # Main application script that integrates all modules and runs the scanner
│
├── src/data/
│   └── psm1000_bands.json      # Contains detailed band definitions and regulatory information for the PSM 1000
│
├── config.json                 # User configuration file (defines scan parameters and selected band)
├── requirements.txt            # List of required Python libraries
└── README.md                   # Project documentation
```
Module Descriptions
	1.	config.py:
	•	Loads settings from config.json (e.g., sample rate, frequency step, gain, and selected band).
	•	Loads band definitions from psm1000_bands.json located in src/data/.
	•	Applies a band override so that the start and end frequencies in the configuration are set based on the selected band.
	2.	data_acquisition.py:
	•	Uses the pyrtlsdr library to interface with an RTL-SDR receiver.
	•	Performs a frequency sweep over the configured range.
	•	Captures raw I/Q samples for each frequency step.
	3.	signal_processing.py:
	•	Applies Fast Fourier Transform (FFT) to the captured I/Q samples.
	•	Converts FFT results into signal strength values (in dBm).
	•	Extracts peak values for each frequency step to simplify logging and visualization.
	4.	visualization.py:
	•	Utilizes Matplotlib to display the RF spectrum.
	•	Features include:
	•	A progress bar at the top indicating scan progress.
	•	A main spectrum graph that shows previous sweeps (grey), a running average (blue), and the most recent scan (red).
	•	An info box at the bottom with a large, bold blue display of the current frequency and smaller white text detailing band information.
	•	Automatically adjusts the y-axis scale based on incoming data and ensures that frequency labels remain visible.
	5.	logger.py:
	•	Logs each full sweep to a timestamped file in the logs/ directory.
	•	Updates a running average of the last X sweeps and saves this average as a CSV file.
	•	Exports two CSV files (recent_scan.csv and average_scan.csv) in a format compatible with Shure Wireless Workbench (frequency in Hz, signal strength in dBm, no headers).
	6.	test_sdr.py:
	•	Integrates all the modules.
	•	Controls the scanning loop:
	•	Iterates through the frequency range.
	•	Updates the progress bar and current frequency in the UI.
	•	Processes and visualizes the spectrum.
	•	Logs each sweep and updates the running average.
	•	Runs continuously, allowing for live scanning and real-time updates.

Usage
	1.	Configuration:
	•	Edit config.json to set scan parameters and select the desired band (e.g., "selected_band": "H22").
	•	Ensure that the band definitions in src/data/psm1000_bands.json meet your requirements.
	2.	Running the Scanner:
	•	In the project root directory, run:

python3 src/test_sdr.py


	•	The GUI will open, showing the progress bar at the top, the current scanning frequency and band details in the info box at the bottom, and the RF spectrum in the main window.

	3.	Data Logging:
	•	After each complete sweep, the scanner updates two CSV files in the data/ folder:
	•	recent_scan.csv: Contains the most recent sweep.
	•	average_scan.csv: Contains the average of the last X sweeps.
	•	These files are formatted for direct import into Shure Wireless Workbench.
	4.	Importing into WWB:
	•	Open Wireless Workbench.
	•	Navigate to the frequency coordination section.
	•	Import recent_scan.csv or average_scan.csv as needed.

Conclusion

This RF scanning tool provides a cost-effective solution for real-time frequency analysis and logging for IEM coordination. It combines:
	•	Hardware integration with an RTL-SDR,
	•	Signal processing with FFT,
	•	Dynamic visualization with a professional GUI,
	•	Robust logging in formats compatible with Shure Wireless Workbench.

The system is designed to be modular, making it straightforward to extend or modify as requirements evolve. It serves as a working prototype for practical field use and can be further enhanced with additional features such as real-time alerts, remote monitoring, or historical data analysis.

This report should provide sufficient detail for another developer or language model to understand the design and functionality of the system. If further clarification or additional documentation is needed, please let me know.
