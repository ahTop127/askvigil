import time
import os
import requests

# 1. Configuration
BASE_URL = "https://askvigil.duckdns.org"

SCAN_URL = f"{BASE_URL}/api/v1/detection/scan"
CALIBRATION_URL = f"{BASE_URL}/"  # Root endpoint to safely absorb the dummy upload

# 2. DYNAMICALLY DETECT SCRIPT LOCATION
# This gets the absolute directory of the script file itself, no matter where your terminal is.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define just the filenames here
IMAGE_FILENAMES = {
    # "Easy Fast-Path (Simple Asset)": "dense-easy.png",
    "Optimized Fast-Path (Dense Asset)": "dense-light.jpeg",
    "Complex Edge-Path (Dense Asset)": "dense-complex.jpeg",
}

# Combine the script directory with the filename dynamically using os.path.join
IMAGE_FILES = {
    category: os.path.join(SCRIPT_DIR, filename)
    for category, filename in IMAGE_FILENAMES.items()
}


def run_ocr_benchmark():
    print(f"Connecting to live instance: {BASE_URL}\n")
    # Initialize a unified session for the entire script lifecycle
    session = requests.Session()
    report_metrics = {}

    for category, file_name in IMAGE_FILES.items():
        if not os.path.exists(file_name):
            print(
                f"❌ Error: File '{file_name}' not found in directory. Skipping {category}."
            )
            continue

        file_size_kb = os.path.getsize(file_name) / 1024
        print(f"====== Evaluating Category: {category} ({file_size_kb:.2f} KB) ======")

        # --- PHASE 1: NET OVERHEAD CALIBRATION ---
        # Generate dummy data matching the EXACT byte size of the image
        with open(file_name, "rb") as f:
            real_bytes = f.read()
        byte_length = len(real_bytes)
        
        # 🚀 NETWORK WARMUP LAP: Absorb the cold socket/SSL handshake overhead for this loop
        print(f"-> Priming network connection for {byte_length} byte payload...")
        try:
            dummy_file = {"file": ("dummy.bin", b"X" * byte_length, "application/octet-stream")}
            session.post(CALIBRATION_URL, files=dummy_file, timeout=15)
        except requests.exceptions.RequestException:
            pass

        print(f"-> Calibrating upload speed for an exact {byte_length} byte payload...")
        network_latencies = []

        # Run 10 calibration loops to find network flight overhead for this file size
        for _ in range(10):
            # Create an in-memory dummy file block with identical size to simulate upload transit
            dummy_file = {
                "file": ("dummy.bin", b"X" * byte_length, "application/octet-stream")
            }
            start = time.perf_counter()
            try:
                session.post(CALIBRATION_URL, files=dummy_file, timeout=15)
                network_latencies.append(time.perf_counter() - start)
            except requests.exceptions.RequestException:
                pass

        if not network_latencies:
            print(f"❌ Failed to calculate network overhead for {category}. Skipping.")
            continue

        avg_network_overhead = sum(network_latencies) / len(network_latencies)
        print(f"-> Calculated Upload Overhead: {avg_network_overhead:.4f}s")

        # --- PHASE 2: REAL RAC PIPELINE EXECUTION ---
        # 🚀 BACKEND WARMUP LAP: Prime the computer vision model files and memory arrays
        print("-> Triggering OCR warmup lap to cache model files into RAM...")
        try:
            with open(file_name, "rb") as img:
                warmup_payload = {
                    "file": (
                        file_name,
                        img,
                        "image/jpeg" if file_name.endswith(".jpg") else "image/png",
                    )
                }
                session.post(SCAN_URL, files=warmup_payload, timeout=20)
        except requests.exceptions.RequestException:
            pass

        print("-> System warmed up. Executing 20x Live OCR Processing Loops...")
        adjusted_latencies = []
        
        for i in range(20):
            # Re-open file each loop to refresh the file pointer stream safely
            with open(file_name, "rb") as img:
                # 'input_type' is omitted or set to standard processing values
                files_payload = {
                    "file": (
                        file_name,
                        img,
                        "image/jpeg" if file_name.endswith(".jpeg") else "image/png",
                    )
                }

                start_time = time.perf_counter()
                try:
                    response = session.post(SCAN_URL, files=files_payload, timeout=20)
                    total_time = time.perf_counter() - start_time

                    if response.status_code == 200:
                        # Subtract the size-calibrated network overhead from the total time
                        pure_ocr_compute = max(0.01, total_time - avg_network_overhead)
                        adjusted_latencies.append(pure_ocr_compute)
                        print(
                            f"   Req {i + 1}: Total={total_time:.3f}s | Isolated OCR Compute={pure_ocr_compute:.3f}s"
                        )
                    else:
                        print(
                            f"   Req {i + 1}: Failed with Status {response.status_code}"
                        )
                except requests.exceptions.RequestException as e:
                    print(f"   Req {i + 1}: Network Error: {e}")

        # Summary compilation
        valid_computes = [t for t in adjusted_latencies if t > 0.02]
        if not valid_computes and adjusted_latencies:
            valid_computes = adjusted_latencies

        if valid_computes:
            report_metrics[category] = {
                "size": f"{file_size_kb:.1f} KB",
                "avg": sum(valid_computes) / len(valid_computes),
                "min": min(valid_computes),
                "max": max(valid_computes),
            }

    # --- PHASE 3: SUMMARY DISPLAY ---
    print("\n\n" + "=" * 65)
    print("🚀 FINAL OCR REPORT PERFORMANCE BENCHMARK MATRIX")
    print("=" * 65)
    print(
        "| Asset Category | File Size | Avg Compute Time | Min (Best) | Max (Worst) |"
    )
    print("| :--- | :--- | :--- | :--- | :--- |")
    for cat, stats in report_metrics.items():
        print(
            f"| {cat} | {stats['size']} | {stats['avg']:.4f}s | {stats['min']:.4f}s | {stats['max']:.4f}s |"
        )
    print("=" * 65)


if __name__ == "__main__":
    run_ocr_benchmark()
