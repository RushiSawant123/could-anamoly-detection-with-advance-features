"""
Cloud Anomaly Detection - Client Anomaly Injector UI

A standalone Streamlit application that acts as an edge client.
Allows targeting a remote central server and injecting simulated
real-world anomalies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import os
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import streamlit as st
import simulator.anomaly_injector as injector

st.set_page_config(page_title="Client Anomaly Injector", layout="centered")

st.markdown("## 🧪 Edge Client Anomaly Injector")
st.markdown("Simulate real-world conditions from this client device and send them to the central monitoring server.")

st.markdown("### Client Configuration")
col_a, col_b = st.columns(2)
with col_a:
    device_id = st.text_input("Local Device/Laptop ID", "Client-Laptop-1")
with col_b:
    default_url = os.getenv("API_URL", "http://127.0.0.1:8000/predict")
    target_url = st.text_input("Central Server API URL", default_url)

st.markdown("### Geographical Origin (Simulated)")
region = st.selectbox("Select Threat Origin Region", ["North America (San Francisco)", "Europe (Frankfurt)", "Asia (Tokyo)", "South America (São Paulo)", "Australia (Sydney)", "Eastern Europe (Moscow)"])

# Approximate coordinates for the globe
REGIONS = {
    "North America (San Francisco)": (37.7749, -122.4194),
    "Europe (Frankfurt)": (50.1109, 8.6821),
    "Asia (Tokyo)": (35.6762, 139.6503),
    "South America (São Paulo)": (-23.5505, -46.6333),
    "Australia (Sydney)": (-33.8688, 151.2093),
    "Eastern Europe (Moscow)": (55.7558, 37.6173)
}
lat, lon = REGIONS[region]

st.markdown("---")
st.markdown("### Select Anomaly Payload to Inject")

col1, col2 = st.columns(2)

with col1:
    st.info("🧠 **Memory Leak**\n\nSimulates a slow memory exhaustion without high CPU use.")
    if st.button("Inject Memory Leak", use_container_width=True):
        payload = injector.generate_memory_leak(device_id, latitude=lat, longitude=lon)
        if injector.request_anomaly(payload, url=target_url):
            st.success("Successfully injected Memory Leak payload to Server!")
        else:
            st.error(f"Injection failed. Is the API listening at {target_url}?")
            
    st.info("⚡ **Crypto-Mining / CPU Spike**\n\nSimulates an unauthorized heavy processor workload with networking attached.")
    if st.button("Inject CPU Spike", use_container_width=True):
        payload = injector.generate_crypto_mining(device_id, latitude=lat, longitude=lon)
        if injector.request_anomaly(payload, url=target_url):
            st.success("Successfully injected Crypto-Mining payload to Server!")
        else:
            st.error(f"Injection failed. Is the API listening at {target_url}?")

with col2:
    st.info("🌐 **DDoS / Network Flood**\n\nSimulates a massive influx of unauthorized network requests.")
    if st.button("Inject DDoS Attack", use_container_width=True):
        payload = injector.generate_ddos_attack(device_id, latitude=lat, longitude=lon)
        if injector.request_anomaly(payload, url=target_url):
            st.success("Successfully injected DDoS Attack payload to Server!")
        else:
            st.error(f"Injection failed. Is the API listening at {target_url}?")
            
    st.info("💾 **Disk Failure**\n\nSimulates an I/O hang where disk read/writes suddenly drop to 0.")
    if st.button("Inject Disk Failure", use_container_width=True):
        payload = injector.generate_disk_failure(device_id, latitude=lat, longitude=lon)
        if injector.request_anomaly(payload, url=target_url):
            st.success("Successfully injected Disk Failure payload to Server!")
        else:
            st.error(f"Injection failed. Is the API listening at {target_url}?")
