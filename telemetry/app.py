import streamlit as st
import requests
import time
import asyncio
import aiohttp
import os
import plotly.graph_objects as go
import pandas as pd
import psutil
from datetime import datetime
from collections import deque

st.set_page_config(layout="wide", page_title="AskVigil | Core Telemetry Engine", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    /* Force the main container to the very top */
    .stMainBlockContainer {
        padding-top: 0.5rem !important;
    }
    /* Hide the default Streamlit header/menu space if needed */
    header[data-testid="stHeader"] {
        display: none;
    }
    </style>
    <div style="margin-top: 0.5rem; margin-bottom: 0rem;">
        <h2 style="margin: 0; padding: 0;">🛡️ AskVigil Telemetry Engine</h2>
        <p style="margin: 0; padding: 0; color: #888;">Real-Time Performance Profiling & Explainable AI Validation Layer</p>
    </div>
""", unsafe_allow_html=True)

if "http_session" not in st.session_state:
    st.session_state.http_session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=100)
    st.session_state.http_session.mount('http://', adapter)

# BACKEND_URL = st.sidebar.text_input("Backend Target", "http://backend:8000")
BACKEND_URL = "http://backend:8000"
ASSET_DIR = "/app/benchmark_assets"

# -----------------------------------------------------------------------------
# WORKLOAD CAPABILITY FIXTURES
# -----------------------------------------------------------------------------
TEXT_FIXTURES = {
    "Short (~150 chars)": "URGENT: Your account has been flagged for suspicious activity. Click here immediately to verify your identity or your assets will be frozen: http://secure-bank-login.com",
    "Medium (~500 chars)": "Dear Employee,\n\nOur human resources and cybersecurity compliance teams have updated the mandatory corporate policy guidelines for the upcoming quarter. All personnel are strictly required to review the appended documentation and sign the acknowledgement form before the end of the current business day. Please authenticate here to proceed: https://internal-hr-portal.net/login",
    "Long (~950 chars)": "OFFICIAL NOTIFICATION: INTERNAL REVENUE AUDIT RECONCILIATION DISCLOSURE.\n\nThis electronic transmission serves as an official administrative notice that your submitted financial tax declarations for the prior fiscal period have been flagged by our automated data validation engines for immediate reconciliation. Access your file instantly via the encrypted gateway link provided below:\n\nSECURE ACCESS LINK: https://gov-tax-reconciliation-portal.org/secure/auth-login"
}

IMAGE_FIXTURES = {
    "Micro Notification": "ocr-micro-notification.png",
    "Dense Transaction Stream": "ocr-dense-transaction-stream.png",
    "Uniform Stream": "ocr-uniform-stream.png",
    "Fragmented Block": "ocr-fragmented-block.png",
    "Sparse Matrix": "ocr-sparse-matrix.png"
}

# -----------------------------------------------------------------------------
# SYSTEM TOPOLOGY CONSTANTS
# -----------------------------------------------------------------------------
LOGICAL_CORES = psutil.cpu_count(logical=True) or 1
PHYSICAL_CORES = psutil.cpu_count(logical=False) or 1
CPU_FREQ = psutil.cpu_freq().max if psutil.cpu_freq() else 0.0

# -----------------------------------------------------------------------------
# ROLLING HISTORY DEQUES
# -----------------------------------------------------------------------------
WINDOW_SIZE = 30
if "time_history" not in st.session_state:
    st.session_state.time_history = deque([datetime.now().strftime("%H:%M:%S") for _ in range(WINDOW_SIZE)], maxlen=WINDOW_SIZE)
if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)
if "mem_history" not in st.session_state:
    st.session_state.mem_history = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)
if "shm_history" not in st.session_state:
    st.session_state.shm_history = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)
if "io_write_history" not in st.session_state:
    st.session_state.io_write_history = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)
if "io_read_history" not in st.session_state:
    st.session_state.io_read_history = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)

# Seed parameters for accurate delta calculations
if "last_io_bytes" not in st.session_state:
    st.session_state.last_io_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
if "last_net_bytes" not in st.session_state:
    st.session_state.last_net_bytes = psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0
if "last_io_time" not in st.session_state:
    st.session_state.last_io_time = time.perf_counter()

# -----------------------------------------------------------------------------
# PERFORMANCE MONITOR ENGINE
# -----------------------------------------------------------------------------
def get_network_latency(target_url: str) -> float:
    try:
        start = time.perf_counter()
        res = st.session_state.http_session.get(target_url, timeout=0.5)
        if res.status_code == 200:
            return (time.perf_counter() - start) * 1000
    except Exception:
        pass
    return 0.0

def calculate_system_metrics():
    now_time = time.perf_counter()
    time_delta = now_time - st.session_state.last_io_time
    if time_delta <= 0:
        time_delta = 0.1
        
    raw_cpu_total = psutil.cpu_percent(interval=None) * LOGICAL_CORES
    capacity_cpu_pct = raw_cpu_total / LOGICAL_CORES
    ram_util = psutil.virtual_memory().percent
    
    shm_pct = 0.0
    if os.path.exists('/dev/shm'):
        shm_stats = os.statvfs('/dev/shm')
        if shm_stats.f_blocks > 0:
            shm_pct = (1.0 - (shm_stats.f_bavail / shm_stats.f_blocks)) * 100
            
    # Calculate Disk Write Rate
    current_io_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
    bytes_delta = current_io_bytes - st.session_state.last_io_bytes
    if bytes_delta < 0: bytes_delta = 0
    write_mb_per_sec = (bytes_delta / (1024 * 1024)) / time_delta
    
    # Calculate Network Rx Inbound Traffic Throughput
    current_net_bytes = psutil.net_io_counters().bytes_recv if psutil.net_io_counters() else 0
    net_delta = current_net_bytes - st.session_state.last_net_bytes
    if net_delta < 0: net_delta = 0
    net_in_mb_per_sec = (net_delta / (1024 * 1024)) / time_delta
    
    st.session_state.last_io_bytes = current_io_bytes
    st.session_state.last_net_bytes = current_net_bytes
    st.session_state.last_io_time = now_time
    
    return raw_cpu_total, capacity_cpu_pct, ram_util, shm_pct, write_mb_per_sec, net_in_mb_per_sec

# -----------------------------------------------------------------------------
# UNIFIED REAL-TIME HUD LOOP
# -----------------------------------------------------------------------------
@st.fragment(run_every=1.0)
def render_live_telemetry_hub():
    raw_cpu, capacity_cpu, ram, shm, io_write, net_in = calculate_system_metrics()
    network_ping = get_network_latency(f"{BACKEND_URL}/")
    
    st.session_state.time_history.append(datetime.now().strftime("%H:%M:%S"))
    st.session_state.cpu_history.append(capacity_cpu)
    st.session_state.mem_history.append(ram)
    st.session_state.shm_history.append(shm)
    st.session_state.io_write_history.append(io_write)
    st.session_state.io_read_history.append(net_in)
    
    plot_df = pd.DataFrame({
        "Timestamp": list(st.session_state.time_history),
        "CPU (%)": list(st.session_state.cpu_history),
        "RAM (%)": list(st.session_state.mem_history),
        "IPC (%)": list(st.session_state.shm_history),
        "Write (MB/s)": list(st.session_state.io_write_history),
        "Network In (MB/s)": list(st.session_state.io_read_history)
    })
    
    col_graphs, col_cards = st.columns([2, 1])
    
    with col_graphs:
        st.markdown("### 📈 Live Resource Consumption Waveform")
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.line_chart(plot_df, x="Timestamp", y=["CPU (%)", "RAM (%)", "IPC (%)"], height=260)
        with chart_col2:
            # Dual fields automatically activate single-line balanced legend height padding
            st.line_chart(plot_df, x="Timestamp", y=["Write (MB/s)", "Network In (MB/s)"], height=260)
            
    with col_cards:
        st.markdown("### ⚙️ Hardware Introspection & Controls")
        
        metric_r1_c1, metric_r1_c2 = st.columns(2)
        with metric_r1_c1:
            st.metric(
                label="Compute Capacity", 
                value=f"{raw_cpu:.1f}%", 
                delta=f"{LOGICAL_CORES} Cores ({PHYSICAL_CORES}P / {CPU_FREQ/1000:.1f}GHz)" if CPU_FREQ else f"{LOGICAL_CORES} Cores Mapped"
            )
        with metric_r1_c2:
            st.metric(
                label="Network Transit", 
                value=f"{network_ping:.1f} ms", 
                delta="Deterministic Pool" if network_ping < 10 else "Network Jitter"
            )
            
        metric_r2_c1, metric_r2_c2 = st.columns(2)
        with metric_r2_c1:
            st.metric(
                label="Shared Memory Pool", 
                value=f"{shm:.1f}% Use", 
                delta="1.0 GB Cap Enforced"
            )
        with metric_r2_c2:
            st.metric(
                label="Disk Write Rate", 
                value=f"{io_write:.2f} MB/s", 
                delta="10 MB/s Rate Cap",
                delta_color="inverse" if io_write > 9.0 else "normal"
            )

# -----------------------------------------------------------------------------
# MAIN APP BODY INITIALIZATION
# -----------------------------------------------------------------------------
# st.title("🛡️ AskVigil Telemetry Engine")
# st.markdown("##### Real-Time Performance Profiling & Explainable AI Validation Layer")
# st.write("---")

render_live_telemetry_hub()

# st.write("---")
left_pane, right_pane = st.columns([1, 1])

# -----------------------------------------------------------------------------
# ADMINISTRATIVE EXPANDER: ISOLATING VALIDATION FROM OBSERVABILITY
# -----------------------------------------------------------------------------
with st.expander("🛠️ Administrative & Validation Controls", expanded=False):    
    # Global Configuration in a single horizontal row
    col_mode, col_payload, col_backend = st.columns([1, 1, 1])
    
    # Payload Selection
    with col_mode:
        mode = st.radio("Pipeline Mode", ["Text Ingestion (RAC)", "Multimodal Computer Vision (OCR)"])
    
    with col_payload:
        if mode == "Text Ingestion (RAC)":
            selected_key = st.selectbox("Select Text Vector", list(TEXT_FIXTURES.keys()))
            active_payload = TEXT_FIXTURES[selected_key]
        else:
            selected_key = st.selectbox("Select Target Image Asset", list(IMAGE_FIXTURES.keys()))
            active_payload = os.path.join(ASSET_DIR, IMAGE_FIXTURES[selected_key])
            
    # st.write("---")# Horizontal line separator

    left_pane, right_pane = st.columns([1, 1])

    # -----------------------------------------------------------------------------
    # LEFT PANE: SINGLE PIPELINE INFERENCE DEMO
    # -----------------------------------------------------------------------------
    with left_pane:
        st.subheader("Unified Pipeline Ingestion Gateway")
        endpoint = f"{BACKEND_URL}/api/v1/detection/scan"
        trigger_scan = False
        
        if mode == "Text Ingestion (RAC)":
            display_text = st.text_area("Active Text String", value=active_payload, height=150)
            trigger_scan = st.button("⚡ Fire Real-Time RAC Pipeline", use_container_width=True)
        else:
            st.markdown(f"**Target Verification Path:** `{active_payload}`")
            if not os.path.exists(active_payload):
                st.error("❌ Verification target not found. Ensure Docker volumes are correctly mounted.")
            else:
                import base64
                try:
                    with open(active_payload, "rb") as image_file:
                        encoded_img = base64.b64encode(image_file.read()).decode()
                    st.markdown(
                        f"""
                        <div style="height: 200px; overflow-y: scroll; border: 1px solid rgba(255, 255, 255, 0.1); 
                                    border-radius: 4px; background-color: #1e272e; text-align: center; padding: 10px; margin-bottom: 15px;">
                            <img src="data:image/png;base64,{encoded_img}" style="max-width: 100%; height: auto;" />
                        </div>
                        """, unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Failed to read image for preview: {str(e)}")
                    
                trigger_scan = st.button("👁️ Fire Multimodal CV Inference Engine", use_container_width=True)

        if trigger_scan:
            avg_network_lag_ms = get_network_latency(f"{BACKEND_URL}/")
            start_time = time.perf_counter()
            
            try:
                if mode == "Text Ingestion (RAC)":
                    response = st.session_state.http_session.post(endpoint, data={"text": display_text, "input_type": "text"}, timeout=10.0)
                else:
                    with open(active_payload, "rb") as img:
                        files_payload = {"file": (os.path.basename(active_payload), img, "image/png")}
                        response = st.session_state.http_session.post(endpoint, files=files_payload, timeout=20.0)
                
                total_rtt_ms = (time.perf_counter() - start_time) * 1000
                isolated_compute_ms = max(1.0, total_rtt_ms - avg_network_lag_ms)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Inference Successfully Completed in {total_rtt_ms:.2f} ms")
                    st.markdown(
                        f"🔬 **Compute Verification:** Isolated Server Compute = `{isolated_compute_ms:.2f} ms` | "
                        f"Network Transit Overhead = `{avg_network_lag_ms:.2f} ms`"
                    )
                    
                    text_analysis = data.get("unified_text_analysis", {}).get("text_analysis", {})
                    weight_exp = text_analysis.get("weightage_explainability", {})
                    heatmap_list = weight_exp.get("token_heatmap", [])
                    
                    if heatmap_list:
                        html_str = "<div style='background-color:#1e272e; padding:18px; border-radius:8px; line-height:2.8; font-family: monospace;'>"
                        for token_node in heatmap_list:
                            token_text = token_node.get("token_text", "")
                            score = token_node.get("xgb_predictive_delta", 0.0)
                            visual_weight = score * 15.0
                            
                            if score > 0.001:
                                alpha = min(abs(visual_weight) * 1.5, 1.0)
                                bg_color = f"rgba(235, 94, 40, {alpha:.2f})"
                                color = "#ffffff"
                            elif score < -0.001:
                                alpha = min(abs(visual_weight) * 1.5, 1.0)
                                bg_color = f"rgba(46, 213, 115, {alpha:.2f})"
                                color = "#ffffff"
                            else:
                                bg_color = "transparent"
                                color = "#d2dae2"
                            html_str += f"<span style='background-color:{bg_color}; color:{color}; padding: 6px 10px; margin: 4px; border-radius: 4px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1);'>{token_text}</span>"
                        html_str += "</div>"
                        st.markdown(html_str, unsafe_allow_html=True)
                    
                    with st.expander("🔍 View Raw Platform API Contract JSON Stream", expanded=False):
                        st.json(data)
                else:
                    st.error(f"Backend Server Returned Operational Error Status: {response.status_code}")
            except Exception as e:
                st.error(f"Network Pipeline Communication Fault: {str(e)}")

    # -----------------------------------------------------------------------------
    # RIGHT PANE: ASYNC CONCURRENCY HARDENING ENGINE
    # -----------------------------------------------------------------------------
    with right_pane:
        st.subheader("Concurrency Hardening Simulation")
        concurrent_workers = st.slider("Simulated Concurrent Connections", min_value=10, max_value=100, value=25, step=5)
        
        async def fetch_async(session, url, mode_target, payload_data):
            start = time.perf_counter()
            try:
                if mode_target == "Text Ingestion (RAC)":
                    form_fields = {"text": payload_data, "input_type": "text"}
                    async with session.post(url, data=form_fields) as response:
                        await response.read()
                        return (time.perf_counter() - start) * 1000, response.status
                else:
                    data = aiohttp.FormData()
                    with open(payload_data, "rb") as f:
                        file_bytes = f.read()
                    data.add_field("file", file_bytes, filename="ocr_test.png", content_type="image/png")
                    
                    async with session.post(url, data=data) as response:
                        await response.read()
                        return (time.perf_counter() - start) * 1000, response.status
            except Exception:
                return 0, 503

        async def run_stress_test(total_requests, mode_target, payload_data):
            conn = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            async with aiohttp.ClientSession(connector=conn) as session:
                tasks = [fetch_async(session, endpoint, mode_target, payload_data) for _ in range(total_requests)]
                return await asyncio.gather(*tasks)

        if st.button("🔥 Trigger Hardware Saturation Test", use_container_width=True):
            st.info(f"Dispatching {concurrent_workers} concurrent requests down ASGI network interfaces...")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_stress_test(concurrent_workers, mode, active_payload))
            
            latencies = [r[0] for r in results if r[0] > 0]
            status_codes = [r[1] for r in results]
            
            if latencies:
                df_perf = pd.DataFrame({
                    "Request Ingestion Index": list(range(1, len(latencies) + 1)),
                    "Latency (ms)": latencies
                }).set_index("Request Ingestion Index")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_perf.index, y=df_perf["Latency (ms)"], mode='lines+markers', name='Inference Speed', line=dict(color='#e84393', width=2)))
                fig.update_layout(title="ASGI Loop Queue Stability Curve", xaxis_title="Concurrent Connection Request Index", yaxis_title="Latency (ms)", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                success_rate = (status_codes.count(200) / len(status_codes)) * 100
                st.success(f"Metrics Verified: {success_rate:.1f}% Success Rate under maximum operational throttling thresholds.")