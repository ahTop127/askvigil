import time
import requests

# 1. Your live Oracle server domain or IP
BASE_URL = "https://askvigil.duckdns.org"

SCAN_URL = f"{BASE_URL}/api/v1/detection/scan"
NETWORK_PING_URL = f"{BASE_URL}/"  # Hits your root health_check()


def run_comprehensive_benchmark():
    # Initialize a unified session for the entire script lifecycle
    session = requests.Session() 
    print(f"Connecting to: {BASE_URL}")
    print("Step 1: Calculating network flight time overhead via root health check...")

    # 🚀 NETWORK WARMUP LAP: Absorb the brutal cold TCP/SSL handshake cost here
    print("-> Priming network socket and TLS handshake...")
    try:
        session.get(NETWORK_PING_URL, timeout=5)
    except requests.exceptions.RequestException:
        pass

    # Now, run your actual baseline collection on an already-warmed connection pool
    print("-> Collecting stabilized network latency metrics...")
    network_latencies = []
    for _ in range(25):
        start = time.perf_counter()
        try:
            response = session.get(NETWORK_PING_URL, timeout=5)
            if response.status_code == 200:
                network_latencies.append(time.perf_counter() - start)
        except requests.exceptions.RequestException:
            pass

    if not network_latencies:
        print("Error: Could not establish network baseline. Check your BASE_URL.")
        return

    avg_network_lag = sum(network_latencies) / len(network_latencies)
    print(f"-> Average Network/SSL Overhead: {avg_network_lag:.4f}s\n")

    # 2. Define the three test scenarios
    payloads = {
        "Short (~150 chars)": {
            "text": "URGENT: Your account has been flagged for suspicious activity. Click here immediately to verify your identity or your assets will be frozen: http://secure-bank-login.com"
        },
        "Medium (~500 chars)": {
            "text": "Dear Employee,\n\nOur human resources and cybersecurity compliance teams have updated the mandatory corporate policy guidelines for the upcoming quarter. All personnel are strictly required to review the appended documentation and sign the acknowledgement form before the end of the current business day. Failure to complete this verification will result in temporary suspension of active directory and network gateway access credentials. Please authenticate here to proceed: https://internal-hr-portal.net/login"
        },
        "Long (~950 chars)": {
            "text": "OFFICIAL NOTIFICATION: INTERNAL REVENUE AUDIT RECONCILIATION DISCLOSURE.\n\nThis electronic transmission serves as an official administrative notice that your submitted financial tax declarations for the prior fiscal period have been flagged by our automated data validation engines for immediate reconciliation. Discrepancies were identified within the cross-referenced asset schedules and reported income thresholds. To prevent the escalation of this file to formal legal enforcement proceedings, asset liens, or compounding regulatory penalties, you are instructed to access our secure document repository to audit the discrepancies and upload the mandatory supplementary verification forms. Ensure your local computing environment is secure before authenticating into the federal portal. Do not reply directly to this automated server alias. Access your file instantly via the encrypted gateway link provided below:\n\nSECURE ACCESS LINK: https://gov-tax-reconciliation-portal.org/secure/auth-login"
        },
    }

    report_metrics = {}

    print(
        "Step 2: Executing Multi-Category RAC Pipeline Scans (25 iterations per category)..."
    )

    for category, form_payload in payloads.items():
        print(f"\n--- Testing Category: {category} ---")
        
        # 🚀 WARMUP LAP: Execute once to prime OS page cache, Python heap, and DB buffers
        print(f"[{category}] Triggering warmup lap to stabilize system state...")
        try:
            session.post(SCAN_URL, data=form_payload, timeout=15)
        except requests.exceptions.RequestException:
            pass # Absorb any cold timeout anomalies quietly
        
        print(f"[{category}] System warmed up. Collecting clean metrics...")
        adjusted_latencies = []

        for i in range(25):
            start_time = time.perf_counter()
            try:
                response = session.post(SCAN_URL, data=form_payload, timeout=15)
                total_time = time.perf_counter() - start_time

                if response.status_code == 200:
                    # Filter out network session resumption anomalies
                    pure_server_time = max(0.001, total_time - avg_network_lag)
                    adjusted_latencies.append(pure_server_time)
                    print(
                        f"[{category}] Req {i + 1}: Total={total_time:.3f}s | Isolated Compute={pure_server_time:.3f}s"
                    )
                else:
                    print(
                        f"[{category}] Req {i + 1}: Failed with Status {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                print(f"[{category}] Req {i + 1}: Error: {e}")

        # Calculate summary statistics for this category, skipping clamped 0.001s anomalies for cleaner averages
        valid_computes = [t for t in adjusted_latencies if t > 0.002]
        if not valid_computes and adjusted_latencies:
            valid_computes = adjusted_latencies  # Fallback if everything hit the floor

        if valid_computes:
            report_metrics[category] = {
                "avg": sum(valid_computes) / len(valid_computes),
                "min": min(valid_computes),
                "max": max(valid_computes),
            }
        else:
            report_metrics[category] = {"avg": 0.0, "min": 0.0, "max": 0.0}

    # 3. Print out the final stylized Report Table
    print("\n\n" + "=" * 50)
    print("🚀 FINAL REPORT PERFORMANCE BENCHMARK MATRIX")
    print("=" * 50)
    print(f"Calculated Ingress Network Overhead Baseline: {avg_network_lag:.4f}s\n")

    print(
        "| Payload Category | Avg Compute Time | Min (Best Case) | Max (Worst Case) |"
    )
    print("| :--- | :--- | :--- | :--- |")
    for cat, stats in report_metrics.items():
        print(
            f"| {cat} | {stats['avg']:.4f}s | {stats['min']:.4f}s | {stats['max']:.4f}s |"
        )

    print("\n" + "=" * 50)


if __name__ == "__main__":
    run_comprehensive_benchmark()
