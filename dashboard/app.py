"""
Cloud Infrastructure Anomaly Detection Dashboard
Monitors system metrics and anomalies in real-time with visualization and alerting.
"""

import logging
import time
import os
from datetime import datetime
from typing import Tuple, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import plotly.graph_objects as go
import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.forecast import calculate_time_to_breach

# ================== Configuration ==================
# Environment-based configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_PROTOCOL = os.getenv("API_PROTOCOL", "http")
API_BASE_URL = f"{API_PROTOCOL}://{API_HOST}:{API_PORT}"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "5"))
API_RETRY_ATTEMPTS = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
API_RETRY_DELAY = int(os.getenv("API_RETRY_DELAY", "1"))

REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "5000"))
RECORDS_TO_DISPLAY = int(os.getenv("RECORDS_TO_DISPLAY", "10"))
RETENTION_RECORDS_THRESHOLD = int(os.getenv("RETENTION_RECORDS_THRESHOLD", "50"))

# Model file paths
MODEL_VERSION_FILE = Path(os.getenv("MODEL_VERSION_FILE", "ml/model_version.txt"))
LAST_RETRAIN_FILE = Path(os.getenv("LAST_RETRAIN_FILE", "ml/last_retrain.txt"))

# Anomaly thresholds
ANOMALY_CRITICAL_THRESHOLD = float(os.getenv("ANOMALY_CRITICAL_THRESHOLD", "0.7"))
ANOMALY_WARNING_THRESHOLD = float(os.getenv("ANOMALY_WARNING_THRESHOLD", "0.4"))
ANOMALY_INFO_THRESHOLD = float(os.getenv("ANOMALY_INFO_THRESHOLD", "0.2"))

# Metric ranges
CPU_MEMORY_MAX = 100
METRIC_MIN = 0

# ================== Logging Setup ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== Styling ==================
DASHBOARD_STYLES = """
<style>
/* Sohub.digital Inspired Retro-Wave Synthwave Theme */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: #0d0d0d !important;
}

div[data-testid="stAppViewContainer"] {
    background-color: #0d0d0d;
    background-image: 
        radial-gradient(circle at 50% 0%, rgba(112, 0, 255, 0.15) 0%, transparent 50%),
        linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
    background-size: 100% 100%, 30px 30px, 30px 30px;
}

/* Glassmorphism Bento Cards */
div[data-testid="metric-container"] {
    background: rgba(20, 20, 25, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 242, 254, 0.3);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(0, 242, 254, 0.05);
    transition: all 0.3s ease;
}

div[data-testid="metric-container"]:hover {
    border-color: #ff00cc;
    box-shadow: 0 8px 32px rgba(255, 0, 204, 0.15), inset 0 0 15px rgba(255, 0, 204, 0.1);
    transform: translateY(-4px);
}

/* Typography Enhancements */
div[data-testid="stMetricLabel"] p {
    color: #00f2fe;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
}

div[data-testid="stMetricValue"] p {
    color: #ffffff;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700;
    font-size: 36px !important;
    text-shadow: 0 0 10px rgba(255,255,255,0.3);
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #ffffff !important;
    letter-spacing: 1px;
}

hr {
    border: none;
    border-top: 1px solid rgba(112, 0, 255, 0.3);
    margin: 20px 0;
}

/* Glowing Alert Boxes */
.critical-alert {
    background: rgba(255, 0, 204, 0.1);
    border-left: 4px solid #ff00cc;
    padding: 20px;
    border-radius: 8px;
    color: #ffb3f0;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    box-shadow: 0 0 20px rgba(255, 0, 204, 0.2);
}

/* Neon Pulse Status Dot */
.pulse {
    height: 12px;
    width: 12px;
    background-color: #00f2fe;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 12px #00f2fe;
    margin-right: 10px;
    animation: glow-pulse 2s infinite;
}

@keyframes glow-pulse {
    0% { box-shadow: 0 0 5px #00f2fe; opacity: 1; }
    50% { box-shadow: 0 0 20px #00f2fe; opacity: 0.6; }
    100% { box-shadow: 0 0 5px #00f2fe; opacity: 1; }
}

/* Retro Cyber Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 30px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(0, 242, 254, 0.2);
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif;
    color: #a0a0a0;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 1px;
}

.stTabs [aria-selected="true"] {
    color: #00f2fe !important;
    text-shadow: 0 0 10px rgba(0, 242, 254, 0.4);
}
</style>
"""

# ================== Helper Functions ==================

def load_file_content(file_path: Path) -> Optional[str]:
    """Load content from a file safely."""
    try:
        if file_path.exists():
            return file_path.read_text().strip()
        return None
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return None


def validate_dataframe(df: pd.DataFrame) -> bool:
    """Validate that the dataframe has required columns."""
    required_columns = {"prediction", "cpu_usage", "memory_usage", "disk_io", "network_traffic"}
    return all(col in df.columns for col in required_columns)


def check_api_health() -> Tuple[bool, str]:
    """Check API health endpoint before making main requests.
    
    Returns:
        Tuple of (is_healthy: bool, status_message: str)
    """
    health_url = f"{API_BASE_URL}/health"
    
    for attempt in range(1, API_RETRY_ATTEMPTS + 1):
        try:
            logger.info(f"Checking API health at {health_url} (attempt {attempt}/{API_RETRY_ATTEMPTS})")
            response = requests.get(health_url, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            health_data = response.json()
            status = health_data.get("status", "unknown")
            
            if status in ["healthy", "degraded"]:
                logger.info(f"API health check passed: {status}")
                return True, f"API healthy ({status})"
            else:
                logger.warning(f"API health check failed: {status}")
                return False, f"API unhealthy ({status})"
                
        except requests.exceptions.Timeout as e:
            error_msg = f"Health check timeout after {API_TIMEOUT}s: {str(e)} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                logger.info(f"Retrying in {API_RETRY_DELAY}s...")
                import time
                time.sleep(API_RETRY_DELAY)
                continue
            
            logger.error(f"Health check timeout exhausted after {API_RETRY_ATTEMPTS} attempts")
            return False, error_msg
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to API health endpoint: {str(e)} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                logger.info(f"Retrying in {API_RETRY_DELAY}s...")
                import time
                time.sleep(API_RETRY_DELAY)
                continue
            
            logger.error(f"Health check connection exhausted after {API_RETRY_ATTEMPTS} attempts")
            return False, error_msg
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Health check HTTP error {response.status_code}: {response.text} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS and response.status_code >= 500:
                logger.info(f"Retrying in {API_RETRY_DELAY}s...")
                import time
                time.sleep(API_RETRY_DELAY)
                continue
            
            logger.error(f"Health check HTTP error exhausted after {API_RETRY_ATTEMPTS} attempts")
            return False, error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Health check request failed: {str(e)} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                logger.info(f"Retrying in {API_RETRY_DELAY}s...")
                import time
                time.sleep(API_RETRY_DELAY)
                continue
            
            logger.error(f"Health check request exhausted after {API_RETRY_ATTEMPTS} attempts")
            return False, error_msg
            
        except (ValueError, KeyError) as e:
            error_msg = f"Failed to parse health response: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # If all attempts failed
    logger.error(f"All {API_RETRY_ATTEMPTS} attempts to check API health failed")
    return False, f"API health check failed after {API_RETRY_ATTEMPTS} attempts"


def fetch_predictions_data() -> Optional[pd.DataFrame]:
    """Fetch prediction data from API with retry logic and error handling.
    
    Returns:
        DataFrame with prediction data,
        Empty DataFrame if connected but no data,
        None if connection failed
    """
    predictions_url = f"{API_BASE_URL}/predictions"
    
    for attempt in range(1, API_RETRY_ATTEMPTS + 1):
        try:
            logger.info(f"Fetching predictions from {predictions_url} (attempt {attempt}/{API_RETRY_ATTEMPTS})")
            response = requests.get(predictions_url, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle API response structure - may be list or dict with "predictions" key
            if isinstance(data, dict) and "predictions" in data:
                predictions = data["predictions"]
            elif isinstance(data, list):
                predictions = data
            else:
                logger.warning(f"Unexpected API response format: {type(data)}")
                predictions = []
            
            # Check if data is empty
            if not predictions:
                logger.warning("API returned empty predictions list")
                return pd.DataFrame()  # Return empty DataFrame, not None (connected but no data)
            
            # Convert to DataFrame
            df = pd.DataFrame(predictions)
            if not validate_dataframe(df):
                logger.error("DataFrame validation failed - missing required columns")
                logger.error(f"Available columns: {list(df.columns)}")
                logger.error(f"Required columns: {{'prediction', 'cpu_usage', 'memory_usage', 'disk_io', 'network_traffic'}}")
                return pd.DataFrame()
            
            logger.info(f"Successfully fetched {len(df)} records on attempt {attempt}")
            return df
            
        except requests.exceptions.Timeout as e:
            error_msg = f"API request timeout after {API_TIMEOUT}s (attempt {attempt}): {str(e)}"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                time.sleep(API_RETRY_DELAY)
                continue
            logger.error(f"API timeout exhausted after {API_RETRY_ATTEMPTS} attempts")
            return None  # Connection failed
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to API server: {str(e)} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                time.sleep(API_RETRY_DELAY)
                continue
            logger.error(f"API connection exhausted after {API_RETRY_ATTEMPTS} attempts")
            return None  # Connection failed
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code}: {response.text} (attempt {attempt}): {str(e)}"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS and response.status_code >= 500:
                time.sleep(API_RETRY_DELAY)
                continue
            logger.error(f"API HTTP error exhausted after {API_RETRY_ATTEMPTS} attempts")
            return None  # Connection failed
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)} (attempt {attempt})"
            logger.warning(error_msg)
            if attempt < API_RETRY_ATTEMPTS:
                time.sleep(API_RETRY_DELAY)
                continue
            logger.error(f"API request exhausted after {API_RETRY_ATTEMPTS} attempts")
            return None  # Connection failed
            
        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Failed to parse API response: {str(e)}"
            logger.error(error_msg)
            return None  # Invalid response
    
    # If all attempts failed
    logger.error(f"All {API_RETRY_ATTEMPTS} attempts to fetch predictions failed")
    return None


@st.cache_data(ttl=5)
def calculate_metrics(df_len: int, anomaly_count: int) -> Tuple[float, float]:
    """Calculate stability and confidence scores from pre-computed anomaly count.
    
    Args:
        df_len: Total number of records
        anomaly_count: Number of anomalies detected
        
    Returns:
        Tuple of (stability_score, confidence_score)
    """
    anomaly_ratio = anomaly_count / df_len if df_len > 0 else 0
    stability_score = round((1 - anomaly_ratio) * 100, 2)
    confidence_score = round(100 - (abs(50 - stability_score) * 1.2), 2)
    confidence_score = max(0, confidence_score)  # Ensure non-negative
    
    return stability_score, confidence_score


def get_status_info(anomaly_ratio: float) -> Tuple[str, str, str]:
    """Determine system status based on anomaly ratio."""
    if anomaly_ratio > ANOMALY_CRITICAL_THRESHOLD:
        return "CRITICAL", "red", "🚨 SYSTEM STATUS: CRITICAL — IMMEDIATE ATTENTION REQUIRED"
    elif anomaly_ratio > ANOMALY_WARNING_THRESHOLD:
        return "WARNING", "orange", "⚠ WARNING: Moderate anomaly activity"
    elif anomaly_ratio > ANOMALY_INFO_THRESHOLD:
        return "INFO", "#00ff88", "ℹ Increased anomaly pattern observed"
    else:
        return "HEALTHY", "#00ff88", "✅ System operating normally"


def render_page_header():
    """Render dashboard header with title and timestamp."""
    st.markdown(DASHBOARD_STYLES, unsafe_allow_html=True)
    st.title("Cloud System Monitor")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"<span class='pulse'></span> **Live System Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_model_info():
    """Render model version and retrain information."""
    version = load_file_content(MODEL_VERSION_FILE)
    last_retrain = load_file_content(LAST_RETRAIN_FILE)
    
    if version:
        st.caption(f"Current Model Version: {version}")
    if last_retrain:
        st.caption(f"Last Model Retrained: {last_retrain}")
    
    return version


def render_engine_status(version: Optional[str], api_failed: bool = False):
    """Render AI engine status indicators.
    
    Args:
        version: Model version string
        api_failed: Whether API connection failed (df is None)
    """
    st.markdown("### 🤖 AI Engine Status")
    
    # Status indicator based on actual API response
    if api_failed:
        # API response is None → Connection failed
        st.warning("⚠ AI Engine: Connection Failed")
    else:
        # API returned response (either empty list or with data) → Connection succeeded
        st.markdown("<span class='pulse'></span> <b>LIVE MONITORING ACTIVE</b>", unsafe_allow_html=True)
        st.success("AI Engine: ACTIVE")
    
    if version:
        st.caption(f"Model Version: {version}")


def render_core_metrics(api_failed: bool = False, data_ready: bool = False):
    st.markdown("### 📡 API Connection State")
    col1, col2, col3 = st.columns(3)
    
    if api_failed:
        with col1:
            st.metric("API Status", "❌ Disconnected")
        with col2:
            st.metric("Records Fetched", "0")
        with col3:
            st.metric("Data Age", "—")
    elif data_ready:
        with col1:
            st.metric("API Status", "✅ Connected")
        with col2:
            st.metric("Latest Sync", datetime.now().strftime("%H:%M:%S"))
        with col3:
            st.empty() # Placeholder for layout
    else:
        with col1:
            st.metric("API Status", "✅ Connected")
        with col2:
            st.metric("Records Fetched", "Waiting...")
        with col3:
            st.metric("Data Age", "—")

def render_analysis_metrics(df: pd.DataFrame):
    # Compute metrics once
    total_records = len(df)
    anomaly_mask = df["prediction"] == "Anomaly"
    anomaly_count = anomaly_mask.sum()
    anomaly_ratio = anomaly_count / total_records if total_records > 0 else 0
    
    stability_score, confidence_score = calculate_metrics(total_records, anomaly_count)
    
    st.markdown("### 📡 Traffic Payload Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Telemetry Records", total_records)
    with col2:
        st.metric("Detected Anomalies", anomaly_count)
    with col3:
        st.metric("Anomaly Rate (%)", round(anomaly_ratio * 100, 2))
        
    st.markdown("### 🧠 AI Engine Confidence Core")
    acc_col1, acc_col2 = st.columns(2)
    with acc_col1:
        st.metric("Engine Stability Score", f"{stability_score}%")
    with acc_col2:
        st.metric("Prediction Confidence Level", f"{confidence_score}%")
    
    # Display recent anomalies with their causes (limit to 5 records)
    if anomaly_count > 0:
        st.markdown("---")
        st.markdown("### 🚨 Recent Anomalies Detected")
        
        # Get last 5 anomalies directly using mask
        anomalies_df = df[anomaly_mask].iloc[-5:] if anomaly_count > 0 else pd.DataFrame()
        
        for idx, row in anomalies_df.iterrows():
            cause = row.get("cause", "Unknown reason") if isinstance(row, dict) else getattr(row, "cause", "Unknown reason")
            if pd.isna(cause) or cause is None:
                cause = "Unknown reason"
            
            metric_summary = f"CPU: {row['cpu_usage']:.1f}% | Memory: {row['memory_usage']:.1f}% | Disk: {row['disk_io']:.1f} | Network: {row['network_traffic']:.1f}"
            
            st.warning(f"**Anomaly Detected** — {cause}")
            st.caption(metric_summary)
    
    return total_records, anomaly_count, anomaly_ratio, stability_score, confidence_score


def render_stability_gauge(stability_score: float):
    """Render AI stability gauge chart."""
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stability_score,
        number={'font': {'size': 60, 'color': "white"}},
        title={'text': "AI Stability Score", 'font': {'size': 24, 'color': "white"}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': "#00FFFF", 'line': {'color': "#00FFFF", 'width': 4}},
            'bgcolor': "black",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 40], 'color': "#400000"},
                {'range': [40, 70], 'color': "#4d3300"},
                {'range': [70, 100], 'color': "#003300"}
            ],
            'threshold': {
                'line': {'color': "cyan", 'width': 8},
                'thickness': 0.75,
                'value': stability_score
            }
        }
    ))
    
    gauge.update_layout(
        paper_bgcolor="black",
        font={'color': "white"},
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    gauge.update_traces(selector=dict(type='indicator'), gauge_bar_thickness=0.25)
    st.plotly_chart(gauge, use_container_width=True)


def render_system_status_alert(anomaly_ratio: float):
    """Render system status alerts based on anomaly ratio."""
    status, color, message = get_status_info(anomaly_ratio)
    
    st.markdown(f"""
    <div style='text-align:center; padding:20px;'>
        <h1 style='color:{color};'>
            🚦 SYSTEM STATUS: {status}
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    if anomaly_ratio > ANOMALY_CRITICAL_THRESHOLD:
        st.markdown(f"""
        <div class="critical-alert">
            {message}
        </div>
        """, unsafe_allow_html=True)
    elif anomaly_ratio > ANOMALY_WARNING_THRESHOLD:
        st.warning(message)
    elif anomaly_ratio > ANOMALY_INFO_THRESHOLD:
        st.info(message)
    else:
        st.success(message)


def render_countermeasures_status(df: pd.DataFrame):
    """Render the active countersystem measure based on the latest anomaly."""
    # Find the latest anomaly record
    anomalies = df[df['prediction'] == 'Anomaly']
    if anomalies.empty:
        st.markdown(f"""
        <div style='background: rgba(0, 255, 136, 0.05); border: 1px solid rgba(0, 255, 136, 0.2); border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 2rem;'>
            <h3 style='color: #00ff88; margin-top: 0;'>🛡️ Active Countermeasures System</h3>
            <p style='color: #a0a0a0; font-family: "JetBrains Mono", monospace; margin-bottom: 0;'>System: Scanning... No active threats detected.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Get the latest anomaly
    latest_anomaly = anomalies.iloc[-1]
    remediation = latest_anomaly.get("remediation", "None")
    
    st.markdown(f"""
    <div style='background: rgba(255, 20, 147, 0.1); border: 2px solid #ff1493; border-radius: 12px; padding: 20px; box-shadow: 0 0 15px rgba(255, 20, 147, 0.4); text-align: center; margin-bottom: 2rem; animation: pulse 2s infinite;'>
        <h3 style='color: #ff1493; margin-top: 0;'>⚡ COUNTERMEASURE DEPLOYED</h3>
        <p style='color: #ffffff; font-family: "JetBrains Mono", monospace; font-size: 1.1em; margin-bottom: 0;'>{remediation}</p>
    </div>
    """, unsafe_allow_html=True)


def render_fallback_dashboard():
    """Render a fallback dashboard when API is unavailable."""
    st.markdown("---")
    st.markdown("## 🔄 System Status: API Unavailable")
    
    st.warning("The anomaly detection system is currently offline. Here's what you can expect when it's back online:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Real-time Monitoring**\n\n- Live system metrics tracking\n- Anomaly detection alerts\n- Performance analytics")
    
    with col2:
        st.info("🤖 **AI Engine Status**\n\n- Model health monitoring\n- Automatic retraining\n- Prediction accuracy tracking")
    
    with col3:
        st.info("📈 **Analytics Dashboard**\n\n- Historical trend analysis\n- System stability metrics\n- Customizable visualizations")
    
    st.markdown("---")
    st.markdown("### 🔧 Quick Setup Guide")
    
    st.code(f"""
# 1. Start the FastAPI backend
python -m uvicorn backend.main:app --host {API_HOST} --port {API_PORT} --reload

# 2. Start the Streamlit dashboard (in another terminal)
streamlit run dashboard/app.py

# 3. Start the Live Simulator (in a third terminal)
# This is REQUIRED to see live moving charts!
python simulator/live_simulator.py

# 4. Access the dashboard at http://localhost:8501
""")
    
    st.markdown("### ⚙️ Configuration")
    st.json({
        "API_HOST": API_HOST,
        "API_PORT": API_PORT,
        "API_BASE_URL": API_BASE_URL,
        "API_TIMEOUT": f"{API_TIMEOUT}s",
        "REFRESH_INTERVAL": f"{REFRESH_INTERVAL}ms"
    })
    
    st.markdown("---")
    st.info("💡 **Tip:** The dashboard will automatically reconnect once the API is available. Refresh the page to retry connection.")


def render_analysis_charts(df: pd.DataFrame, max_chart_records: int = 100):
    """Render analysis charts with limited records for better performance.
    
    Args:
        df: Full dataframe from API
        max_chart_records: Maximum records to display in charts
    """
    # Limit data for charts to improve rendering performance
    df_chart = df.tail(max_chart_records) if len(df) > max_chart_records else df
    
    st.subheader("Anomaly Ratio")
    ratio_data = df["prediction"].value_counts()  # Use full data for ratio accuracy
    st.bar_chart(ratio_data)
    
    st.subheader("CPU Usage Trend")
    st.line_chart(df_chart["cpu_usage"])
    
    st.subheader("Memory Usage Trend")
    st.line_chart(df_chart["memory_usage"])
    
    st.subheader("Anomaly Occurrence Over Time")
    df_anomaly = df_chart.copy()
    df_anomaly["is_anomaly"] = (df_anomaly["prediction"] == "Anomaly").astype(int)
    st.line_chart(df_anomaly["is_anomaly"])


def _prepare_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and format dataframe for display (reusable).
    
    Args:
        df: Source dataframe
        
    Returns:
        Formatted dataframe with columns reordered and renamed
    """
    # Ensure cause column exists and handle missing values
    if 'cause' not in df.columns:
        df['cause'] = "—"
    else:
        df['cause'] = df['cause'].fillna("—")
        
    if 'remediation' not in df.columns:
        df['remediation'] = "None"
    else:
        df['remediation'] = df['remediation'].fillna("None")
    
    # Reorder columns for better visibility
    column_order = ['id', 'device_id', 'prediction', 'cause', 'remediation', 'cpu_usage', 'memory_usage', 'disk_io', 'network_traffic']
    available_cols = [col for col in column_order if col in df.columns]
    
    # Add timestamp if available
    if 'timestamp' in df.columns:
        available_cols.append('timestamp')
    
    df = df[available_cols]
    
    # Rename columns for display
    rename_mapping = {
        'id': 'ID',
        'device_id': 'Device/Laptop ID',
        'prediction': 'Status',
        'cause': 'Reason/Cause',
        'remediation': 'Remediation Action',
        'cpu_usage': 'CPU %',
        'memory_usage': 'Memory %',
        'disk_io': 'Disk I/O',
        'network_traffic': 'Network',
        'timestamp': 'Time'
    }
    df = df.rename(columns={k: v for k, v in rename_mapping.items() if k in df.columns})
    
    return df


def _style_anomalies(row):
    """Style function for anomaly row highlighting (reusable)."""
    if row['Status'] == 'Anomaly':
        return ['background-color: rgba(255, 0, 0, 0.2); font-weight: bold;'] * len(row)
    else:
        return ['background-color: rgba(0, 255, 136, 0.1);'] * len(row)


def generate_mock_llm_post_mortem(row: pd.Series) -> str:
    """Generates a structured mock GenAI incident report based on telemetry."""
    cause = row.get("cause", "Unknown Anomaly")
    
    # Handle both Series and dict access patterns
    get_val = lambda key, default: row.get(key, default) if hasattr(row, 'get') else getattr(row, key, default)
    
    cpu = get_val("cpu_usage", 0)
    ram = get_val("memory_usage", 0)
    disk = get_val("disk_io", 0)
    net = get_val("network_traffic", 0)
    remediation = get_val("remediation", "None")
    device_id = get_val("device_id", "Unknown Device")
    timestamp = get_val("timestamp", "Unknown Time")
    
    cpu_status = "(Critical Starvation Detected)" if cpu > 85 else "(Nominal)"
    ram_status = "(Heap Overflow / Memory Leak Trajectory)" if ram > 85 else "(Nominal)"
    net_status = "(DDoS Packet Flood Detected)" if net > 800 else "(Nominal)"
    disk_status = "(Hardware Degradation Warning)" if disk > 400 else "(Nominal)"
    
    report = f"""
**Executive Summary:**
At `{timestamp}`, the Anomaly Detection ML engine successfully intercepted a major infrastructural irregularity originating from `{device_id}`. Based on my analysis of the systemic payload, this signature heavily correlates with a **[{cause}]** vector. 

**Telemetry Analysis:**
- **CPU Load:** `{cpu}%` {cpu_status}
- **Memory Saturation:** `{ram}%` {ram_status}
- **Network Ingress:** `{net} Mbps` {net_status}
- **Disk I/O Thrashing:** `{disk} MB/s` {disk_status}

**Automated Remediation Log:**
The Active Countermeasures System was engaged immediately with the following tactical response:
> `{remediation}`

**Recommended Engineering Steps:**
1. **Investigate Origin:** Check access logs for `{device_id}` immediately prior to the incident timestamp.
2. **Review Codebase:** Escalate to DevOps to search for unclosed database connections or missing auto-scaling policies that contributed to this bottleneck.
3. **Enhance Rules:** Consider adjusting the Isolation Forest ML bounds if this is deemed a false positive.

*Report dynamically generated by local GenAI Engine.*
"""
    return report


def render_recent_records(df: Optional[pd.DataFrame] = None):
    """Render recent records table with anomaly highlighting and cause explanations.
    
    Args:
        df: DataFrame with prediction records, or None for loading state
    """
    st.subheader("Recent Records")
    
    if df is None or df.empty:
        st.info("⏳ Waiting for data from API...")
        return
    
    # Limit records for table display (most recent N records)
    display_df = df.tail(RECORDS_TO_DISPLAY).copy()
    
    # Prepare display dataframe (reuse formatting function)
    display_df = _prepare_display_dataframe(display_df)
    
    # Apply styling and display
    styled_df = display_df.style.apply(_style_anomalies, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # Display detailed anomaly explanations below table (limit to 3 recent anomalies)
    anomaly_mask = df["prediction"] == "Anomaly"
    anomaly_count = anomaly_mask.sum()
    
    if anomaly_count > 0:
        st.markdown("---")
        st.markdown("### 📋 Anomaly Details")
        
        # Get last 3 anomalies efficiently
        anomalies = df[anomaly_mask].iloc[-3:]
        
        for idx, row in anomalies.iterrows():
            cause = row.get("cause", "Unknown reason") if isinstance(row, dict) else getattr(row, "cause", "Unknown reason")
            if pd.isna(cause) or cause is None or cause == "":
                cause = "Anomaly detected based on learned patterns"
            
            with st.expander(f"🔴 Anomaly #{row['id']} - {cause}"):
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("CPU", f"{row['cpu_usage']:.1f}%")
                with col_b:
                    st.metric("Memory", f"{row['memory_usage']:.1f}%")
                with col_c:
                    st.metric("Disk I/O", f"{row['disk_io']:.1f}")
                with col_d:
                    st.metric("Network", f"{row['network_traffic']:.1f}")
                
                st.markdown(f"**Reason:** {cause}")
                if 'timestamp' in row and not pd.isna(row['timestamp']):
                    st.caption(f"Detected at: {row['timestamp']}")
                    
                if st.button("🤖 Generate AI Post-Mortem", key=f"btn_ai_{row['id']}"):
                    with st.spinner("AI Analysis Engine parsing telemetry..."):
                        import time
                        time.sleep(1.2) # Simulate LLM generation time
                        report = generate_mock_llm_post_mortem(row)
                        st.info(report, icon="🤖")


def render_geographical_threat_map(df: pd.DataFrame):
    """Render a 3D glowing threat map using Pydeck."""
    st.markdown("## 🌍 Global Threat Intelligence")
    st.markdown("Real-time geographical tracking of incoming anomalies and attack vectors.")
    
    # Filter for anomalies with geo data
    anomalies = df[(df['prediction'] == 'Anomaly') & (df['latitude'] != 0) & (df['longitude'] != 0)].copy()
    
    if anomalies.empty:
        st.info("Searching for geographical threat signatures... No active external breaches detected.")
        # Show an empty globe anyway for aesthetic
        view_state = pdk.ViewState(latitude=20, longitude=0, zoom=0.5, pitch=45)
        st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/dark-v10', initial_view_state=view_state))
        return

    # Prepare data for pydeck (Scatterplot for threats)
    # Most recent anomalies should be brighter/larger
    anomalies['radius'] = 100000 # 100km radius markers
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        anomalies,
        get_position=["longitude", "latitude"],
        get_color="[255, 20, 147, 160]", # Cyber Pink
        get_radius="radius",
        pickable=True,
    )

    # Add a glowing pulse effect or arcs if we had a destination (but we only have source)
    # Let's just use a high-contrast dark globe
    view_state = pdk.ViewState(
        latitude=anomalies['latitude'].iloc[-1],
        longitude=anomalies['longitude'].iloc[-1],
        zoom=1,
        pitch=45
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/dark-v10',
        tooltip={"text": "Anomaly Triggered\nRegion: {cause}\nID: #{id}"}
    )

    st.pydeck_chart(r)
    
    st.markdown("---")
    st.markdown("### 📡 Active Breach Locations")
    st.dataframe(anomalies[['id', 'latitude', 'longitude', 'cause']].rename(columns={'id': 'Alert ID', 'cause': 'Threat Vector'}), use_container_width=True)


def render_ai_prognosis_panel(df: pd.DataFrame):
    """Render a predictive AI panel that forecasts system failure."""
    st.markdown("---")
    st.markdown("### 🔮 AI Health Prognosis (Time-to-Failure)")
    
    col1, col2 = st.columns(2)
    
    # Calculate CPU trend
    cpu_vals = df['cpu_usage'].tail(10).tolist()
    cpu_time = calculate_time_to_breach(cpu_vals)
    
    # Calculate RAM trend
    ram_vals = df['memory_usage'].tail(10).tolist()
    ram_time = calculate_time_to_breach(ram_vals)
    
    with col1:
        if cpu_time is not None:
            if cpu_time == 0:
                st.error("🔥 **CPU LIMIT BREACHED**")
            else:
                st.warning(f"⚠️ **CPU CRITICAL**: Estimated breach in ~{cpu_time:.0f}s")
        else:
            st.success("✅ **CPU RELIABILITY**: Stable trajectory")
            
    with col2:
        if ram_time is not None:
            if ram_time == 0:
                st.error("🔥 **MEMORY SATURATION REACHED**")
            else:
                st.warning(f"⚠️ **MEMORY ALERT**: Estimated exhaustion in ~{ram_time:.0f}s")
        else:
            st.success("✅ **MEMORY RELIABILITY**: Stable trajectory")


def render_cyber_jail():
    """Render the management interface for quarantined devices."""
    st.markdown("## 🚨 CYBER JAIL REPOSITORY")
    st.markdown("Manage devices that have been automatically isolated due to critical threat signatures.")
    
    try:
        response = requests.get(f"{API_BASE_URL}/quarantine")
        if response.status_code == 200:
            jailed = response.json()
            if not jailed:
                st.success("The Cyber Jail is empty. No active internal threats detected.")
                return
            
            for device in jailed:
                with st.expander(f"🔴 JAIL RECORD: {device['device_id']}"):
                    col_x, col_y = st.columns([3, 1])
                    with col_x:
                        st.write(f"**Reason for Isolation:** {device['reason']}")
                        st.caption(f"Quarantined at: {device['timestamp']}")
                    with col_y:
                        if st.button("PARDON DEVICE", key=f"release_{device['device_id']}"):
                            rel_resp = requests.post(f"{API_BASE_URL}/quarantine/release/{device['device_id']}")
                            if rel_resp.status_code == 200:
                                st.toast(f"Device {device['device_id']} has been pardoned and network access restored.", icon="🔓")
                                st.rerun()
                            else:
                                st.error("Failed to release device.")
        else:
            st.error("Could not reach quarantine API.")
    except Exception as e:
        st.error(f"Error loading cyber jail: {e}")


def render_system_logs():
    st.markdown("## 📜 System Logs Viewer")
    st.markdown("Monitor and explore internal application logs here.")
    
    log_file_path = Path("logs/system.log")
    if not log_file_path.exists():
        st.info("System log file not found. Logs will appear here once the system generates them.")
        return
        
    try:
        with open(log_file_path, "r") as f:
            logs = f.readlines()
            
        if not logs:
            st.info("System log file is empty.")
            return
            
        # Parse logs into a simple structured format (very basic parsing)
        parsed_logs = []
        for line in reversed(logs[-2000:]):  # Get last 2000 lines, reversed for newest first
            parts = line.strip().split(' - ', 3)
            if len(parts) == 4:
                parsed_logs.append({
                    "Timestamp": parts[0],
                    "Component": parts[1],
                    "Severity": parts[2],
                    "Message": parts[3]
                })
            else:
                # Fallback for unparseable lines
                parsed_logs.append({
                    "Timestamp": "",
                    "Component": "",
                    "Severity": "UNKNOWN",
                    "Message": line.strip()
                })
                
        df_logs = pd.DataFrame(parsed_logs)
        
        # Filtering controls
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 Search Logs", "")
        with col2:
            severity_filter = st.multiselect(
                "Filter by Severity", 
                ["INFO", "WARNING", "ERROR", "CRITICAL"],
                default=["INFO", "WARNING", "ERROR", "CRITICAL"]
            )
            
        # Apply filters
        if search_term:
            df_logs = df_logs[df_logs["Message"].str.contains(search_term, case=False, na=False)]
            
        if severity_filter:
            df_logs = df_logs[df_logs["Severity"].isin(severity_filter)]
            
        # Style function
        def style_logs(row):
            sev = row["Severity"]
            if sev == "ERROR" or sev == "CRITICAL":
                return ['background-color: rgba(255, 0, 0, 0.2); font-weight: bold; color: #ffcccc;'] * len(row)
            elif sev == "WARNING":
                return ['background-color: rgba(255, 165, 0, 0.2); color: #ffe6cc;'] * len(row)
            return [''] * len(row)
            
        st.dataframe(
            df_logs.style.apply(style_logs, axis=1),
            use_container_width=True,
            height=600
        )
        
    except Exception as e:
        st.error(f"Failed to read logs: {e}")

def render_alert_history(df: pd.DataFrame):
    st.markdown("## 🚨 Anomaly Alert History")
    st.markdown("Historical record of all anomaly events detected by the system.")
    
    if df is None or df.empty:
        st.info("No prediction data available.")
        return
        
    anomalies = df[df['prediction'] == 'Anomaly'].copy()
    
    if anomalies.empty:
        st.success("No anomalies have been detected! The system is perfectly healthy.")
        return
        
    # Re-use the display preparation function for columns
    display_df = _prepare_display_dataframe(anomalies)
    
    # Sort by ID descending so newest alerts are on top
    if 'ID' in display_df.columns:
        display_df = display_df.sort_values(by='ID', ascending=False)
        
    def style_alerts(row):
        return ['background-color: rgba(255, 0, 0, 0.15);'] * len(row)
        
    st.dataframe(display_df.style.apply(style_alerts, axis=1), use_container_width=True, height=600)



# ================== Main Application ==================

def main():
    """Main application entry point."""
    st.set_page_config(layout="wide")
    
    # Auto refresh
    st_autorefresh(interval=REFRESH_INTERVAL, key="refresh")
    
    # Render header
    render_page_header()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Monitoring", "🌍 Threat Map", "🚨 Cyber Jail", "📜 Logs", "🚨 Alerts"])
    
    with tab1:
        # Load and display model info
        version = render_model_info()
        st.markdown("---")
        
        # Check API health first with timeout
        api_healthy, health_message = check_api_health()
        
        if not api_healthy:
            # Show error state immediately - API is not responding
            render_engine_status(version, api_failed=True)
            st.markdown("---")
            render_core_metrics(api_failed=True, data_ready=False)
            st.markdown("---")
            
            st.error("⚠ API Connection Failed")
            st.error(f"Details: {health_message}")
            st.error(f"API Base URL: {API_BASE_URL}")
            st.info("Troubleshooting steps:")
            st.info("1. Ensure the FastAPI server is running")
            st.info("2. Verify the API host and port configuration")
            st.info("3. Check that CORS is properly configured")
            st.info("4. Review API server logs for errors")
            return
        
        # Show loading state with timeout to prevent infinite wait
        with st.spinner("🔄 Connecting to anomaly detection API..."):
            st.markdown("---")
            
            # Show loading metrics
            render_core_metrics(api_failed=False, data_ready=False)
            
            # Fetch and process data with explicit timeout handling
            df = fetch_predictions_data()
        
        # Handle three cases:
        if df is None:
            # Connection failed to /predictions endpoint - API response is None
            logger.warning("Failed to fetch predictions data - connection error")
            render_engine_status(version, api_failed=True)
            st.markdown("---")
            
            # Show "❌ Failed" status
            render_core_metrics(api_failed=True, data_ready=False)
            st.markdown("---")
            
            st.warning("⚠ Could not fetch predictions from API")
            st.info("The API health check passed, but the /predictions endpoint is not responding.")
            st.info("This may indicate the API server is starting up. Please refresh the page.")
            render_fallback_dashboard()
            
        elif df.empty:
            # Connected but no data yet - API returned empty list
            logger.info("Connected to API but no predictions available yet")
            render_engine_status(version, api_failed=False)
            st.markdown("---")
            
            # Show "✅ Connected" status even though list is empty
            render_core_metrics(api_failed=False, data_ready=False)
            st.markdown("---")
            
            st.info("🟢 Connected to API - Waiting for prediction data")
            st.info("The system is ready and monitoring. Predictions will appear once log/metric data is received.")
            
        else:
            # Connected with data - API returned non-empty list
            try:
                logger.info(f"Processing {len(df)} records from API")
                
                # Update engine status - API returned data
                render_engine_status(version, api_failed=False)
                st.markdown("---")
                
                # Check for new anomalies and trigger alerts
                if 'last_seen_id' not in st.session_state:
                    st.session_state.last_seen_id = df['id'].max() if not df.empty else 0
                else:
                    new_records = df[df['id'] > st.session_state.last_seen_id]
                    if not new_records.empty:
                        st.session_state.last_seen_id = df['id'].max()
                        new_anomalies = new_records[new_records['prediction'] == 'Anomaly']
                        for _, row in new_anomalies.iterrows():
                            device = row.get('device_id', 'Unknown')
                            cause = row.get('cause', 'Unknown')
                            st.toast(f"🚨 **NEW ANOMALY DETECTED**\n\nDevice: {device}\nCause: {cause}", icon="🚨")

                
                # Render analysis metrics and get computed scores (computed once)
                st.markdown("---")
                total_records, anomaly_count, anomaly_ratio, stability_score, confidence_score = render_analysis_metrics(df)
                
                # Render core metrics with updated connection status
                render_core_metrics(api_failed=False, data_ready=True)
                st.markdown("---")
                
                # Render stability gauge
                render_stability_gauge(stability_score)
                
                # Render system status alert
                render_system_status_alert(anomaly_ratio)
                
                # Render Countermeasures
                render_countermeasures_status(df)
                
                # AI Prognosis
                render_ai_prognosis_panel(df)
                
                # Render charts (with optimized record limit)
                st.markdown("---")
                st.markdown("## 📈 Analytics and Trends")
                render_analysis_charts(df, max_chart_records=100)
                
                # Render recent records
                st.markdown("---")
                render_recent_records(df)
                
                logger.info("Dashboard rendered successfully")
                
            except Exception as e:
                logger.error(f"Dashboard rendering error: {e}", exc_info=True)
                st.error(f"⚠ Error rendering dashboard: {str(e)}")
                st.error("Please refresh the page or contact support.")

    with tab2:
        if 'df' in locals():
            render_geographical_threat_map(df)
        else:
            st.info("Waiting for data connection to load threat map...")

    with tab3:
        render_cyber_jail()

    with tab4:
        render_system_logs()

    with tab5:
        if 'df' in locals():
            render_alert_history(df)
        else:
            st.info("Waiting for data connection to load alert history...")



if __name__ == "__main__":
    main()