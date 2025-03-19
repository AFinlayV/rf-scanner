from flask import Flask, jsonify, render_template, request
import json
import os
import subprocess
import threading

# Load configuration from the project root
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Load available bands correctly from psm1000_bands.json
BANDS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "data", "psm1000_bands.json"))
try:
    with open(BANDS_PATH, "r") as f:
        bands_data = json.load(f)
        available_bands = [band["band"] for band in bands_data if "band" in band]  # Extract band names
except Exception as e:
    print(f"⚠️ Error loading bands from psm1000_bands.json: {e}")
    available_bands = []

app = Flask(__name__, template_folder="templates", static_folder="static")

scan_process = None  # Track the scan process

def run_scan():
    """Run test_sdr.py and stream its output to Flask logs."""
    global scan_process
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        city = config.get("city", "Unknown")
        venue = config.get("venue", "Unknown")
        zip_code = config.get("zip_code", "Unknown")

        # Start scan process with output capture
        scan_process = subprocess.Popen(
            ["python3", "src/test_sdr.py", city, venue, zip_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Stream output to Flask console
        for line in iter(scan_process.stdout.readline, ''):
            print(f"📡 Scan Output: {line.strip()}")

        scan_process.wait()
        print("✅ Scan process completed.")

    except Exception as e:
        print(f"❌ Error running scan: {e}")

# Modify the status endpoint to include available bands
@app.route("/status", methods=["GET"])
def get_status():
    """Return the current system status, including available bands."""
    return jsonify({
        "flask_mode": config.get("flask_mode", False),
        "test_mode": config.get("test_mode", False),
        "selected_band": config.get("selected_band"),
        "available_bands": available_bands,  # Added this
        "log_directory": config.get("log_directory"),
        "test_log_directory": config.get("test_log_directory"),
        "city": config.get("city", "Unknown"),
        "venue": config.get("venue", "Unknown"),
        "zip_code": config.get("zip_code", "Unknown")
    })

# Endpoint: Get latest scan data
@app.route("/scan/latest", methods=["GET"])
def get_latest_scan():
    """Return the most recent scan data."""
    log_dir = config.get("test_log_directory") if config.get("test_mode", False) else config.get("log_directory")
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")], reverse=True)

    if not log_files:
        return jsonify({"error": "No scan data available"}), 404

    latest_file = os.path.join(log_dir, log_files[0])
    with open(latest_file, "r") as f:
        scan_data = json.load(f)

    return jsonify(scan_data)

# Endpoint: Get last 5 scans
@app.route("/scan/logs", methods=["GET"])
def get_scan_logs():
    """Return the last 5 scan logs."""
    log_dir = config.get("test_log_directory") if config.get("test_mode", False) else config.get("log_directory")
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".json")], reverse=True)[:5]

    scan_logs = []
    for log_file in log_files:
        with open(os.path.join(log_dir, log_file), "r") as f:
            scan_logs.append(json.load(f))

    return jsonify(scan_logs)

# NEW: Stop an active scan
@app.route("/scan/stop", methods=["POST"])
def stop_scan():
    """Stop the currently running scan process."""
    global scan_process
    if scan_process and scan_process.poll() is None:
        scan_process.terminate()
        try:
            scan_process.wait(timeout=3)  # Give it time to exit
        except subprocess.TimeoutExpired:
            scan_process.kill()  # Force kill if not stopping
        scan_process = None
        print("✅ Scan process forcefully stopped.")
        return jsonify({"status": "Scan stopped successfully."})
    return jsonify({"error": "No active scan to stop."}), 400

# NEW: Serve Web UI
@app.route("/")
def index():
    """Serve the main web UI."""
    return render_template("index.html")

# NEW: Update configuration to include location details
@app.route("/update-location", methods=["POST"])
def update_location():
    """Update location details (City, Venue, ZIP Code) and save to config.json."""
    try:
        new_location = request.json

        # Load current config
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Update location details
        config["city"] = new_location.get("city", config.get("city", "Unknown"))
        config["venue"] = new_location.get("venue", config.get("venue", "Unknown"))
        config["zip_code"] = new_location.get("zip_code", config.get("zip_code", "Unknown"))

        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)

        return jsonify({"status": "Location updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Modify /scan/start to run scan in a separate thread and capture logs
@app.route("/scan/start", methods=["POST"])
def start_scan():
    """Trigger a scan and capture its output in Flask logs."""
    global scan_process
    if scan_process and scan_process.poll() is None:
        return jsonify({"error": "Scan is already running."})

    scan_thread = threading.Thread(target=run_scan)
    scan_thread.start()

    return jsonify({"status": "Scan started, check logs for output."})

# NEW: Update configuration from UI
@app.route("/update-config", methods=["POST"])
def update_config():
    """Update configuration settings and save to config.json."""
    try:
        new_config = request.json

        # Load current config
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        # Update relevant settings
        config["selected_band"] = new_config.get("selected_band", config["selected_band"])
        config["test_mode"] = new_config.get("test_mode", config["test_mode"])
        config["flask_mode"] = new_config.get("flask_mode", config["flask_mode"])
        config["city"] = new_config.get("city", config.get("city", "Unknown"))
        config["venue"] = new_config.get("venue", config.get("venue", "Unknown"))
        config["zip_code"] = new_config.get("zip_code", config.get("zip_code", "Unknown"))

        # Save updated config
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)

        return jsonify({"status": "Configuration updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if config.get("flask_mode", False):
        app.run(host="0.0.0.0", port=5001, debug=True)
    else:
        print("❌ Flask mode is disabled. Enable it in config.json to run the API.")
