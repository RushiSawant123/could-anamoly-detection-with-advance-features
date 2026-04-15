# 🌌 Retro Cloud Anomaly Detection & Self-Healing Suite

A state-of-the-art, **distributed observability platform** engineered for real-time cloud infrastructure monitoring. This system combines hybrid Machine Learning (Isolation Forests & Autoencoders) with an **Automated Remediation Engine** and **3D Geographical Threat Intelligence**.

Designed with a premium **Synthwave / Retro-Cyber** aesthetic, it provides a high-fidelity command center for modern DevOps and Security teams.

---

## 🏛️ Architectural Overview

The system utilizes a strictly **decoupled client-server architecture**, mimicking distributed production environments:

1.  **FastAPI Inference Brain (Backend)**: The core intelligence. It executes dual-model ML inference on cross-network telemetry, manages a persistent SQLite store, and determines tactical countermeasures.
2.  **Retro Command Center (Dashboard)**: A high-performance Streamlit dashboard for real-time observability, self-healing controls, and 3D threat mapping.
3.  **Telemetry Source (Simulator)**: Continuous background data feed (`live_simulator.py`) or manual edge-injection (`injector_ui.py`). **The dashboard will appear static unless a simulator is running.**

---

## 🚀 Quick Start Guide

To see the platform in action with **live moving data**, launch these in **three separate terminals**:

### 1. The Inference Server (Terminal 1)
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. The Command Center (Terminal 2)
```powershell
streamlit run dashboard/app.py
```

### 3. The Live Data Feed (Terminal 3)
Choose **ONE** of the following depending on your needs:

*   **Option A: Continuous Live Simulation (Recommended for UI testing)**
    ```powershell
    python simulator/live_simulator.py
    ```
*   **Option B: Manual Anomaly Injection (Interactive UI)**
    ```powershell
    streamlit run simulator/injector_ui.py --server.port 8502
    ```

---

## 🌟 Premium Features

### 🛡️ Automated "Self-Healing" Engine
The system doesn't just watch—it acts. When an anomaly is detected, the backend autonomously triggers tactical protocols:
-   **Traffic Rerouting**: Instantly deploys load balancer scaling during DDoS floods.
-   **Thread Isolation**: Gracefully restarts services leaking memory.
-   **Resource Throttling**: Frees up compute for mission-critical tasks.

### 🤖 Generative AI Incident Post-Mortems
Native "AI Analysis" button that parses complex telemetry into human-readable incident reports. These reports provide executive summaries, metric breakdowns, and recommended engineering action items.

### 🌍 3D Geographical Threat Mapping
Powered by **Pydeck**, the dashboard features a glowing 3D globe that tracks the geographical origin of incoming attacks in real-time.

---

## 🛠️ Technology Stack

-   **Backend**: FastAPI, SQLAlchemy (SQLite), Pydantic
-   **Frontend**: Streamlit, Plotly, Pydeck (3D Mapping), Custom CSS (Synthwave)
-   **ML Engine**: Scikit-Learn (Isolation Forest), PyTorch (Log Autoencoder)
-   **Observability**: Python Logging, RESTful API Webhooks

---

## 📂 Project Anatomy

```text
├── backend/                  # FastAPI Core
├── dashboard/                # Synthwave Monitoring UI
├── simulator/                # Edge Client & Live Simulation
├── ml/                       # Hybrid Intelligence (Predict/Retrain)
├── database/                 # SQLAlchemy Models & Schemas
├── logs/                     # Network-wide System Logs
└── cloud.db                  # Centralized Persistence Layer
```

---

## 📜 License
MIT License. Built for advanced cloud observability research.
