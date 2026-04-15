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

## 🛡️ Cyber Jail (Zero-Trust Security)

The platform features an advanced **Automated Quarantine System**. When the ML engine detects a high-severity malicious pattern (e.g., a DDoS signature or severe memory leak), it automatically "jails" the originating device.

-   **Autonomous Blocking**: The Backend immediately rejects all subsequent requests from the quarantined `device_id`.
-   **Security Status**: Blocked attempts are logged and flagged in the system logs as `ACCESS DENIED`.
-   **Manual Override**: Use the `unquarantine.py` utility to release devices from custody.

---

## 🌩️ Cross-Network Support (ngrok)

You can run the Backend on one machine and the Simulators on a completely different network (e.g., edge devices).

1.  Expose the backend via ngrok: `ngrok http 8000`.
2.  Configure the [**.env**](file:///c:/Users/Solgaleo/Downloads/cloud-anomaly-detection/cloud-anomaly-detection/.env) file on the client machine with the public ngrok URL.
3.  See [**CROSS_NETWORK_GUIDE.md**](file:///c:/Users/Solgaleo/Downloads/cloud-anomaly-detection/cloud-anomaly-detection/CROSS_NETWORK_GUIDE.md) for full setup details.

---

## 🧪 Testing & Validation

To ensure the platform is operating at peak efficiency, follow these testing protocols:

1.  **Manual Injection**: Use the [Injector UI](http://localhost:8502) to trigger a "Memory Leak" and observe the "Cyber Jail" protocol in action.
2.  **Unit Tests**: Run `pytest tests/` to validate core ML and API logic.
3.  **End-to-End**: Run `python simulator/live_simulator.py` and verify charts move in the Dashboard.
4.  **Security Reset**: Run `python unquarantine.py` to clear the environment after a security test.

Refer to the [**TESTING_GUIDE.md**](file:///c:/Users/Solgaleo/Downloads/cloud-anomaly-detection/cloud-anomaly-detection/TESTING_GUIDE.md) for detailed test cases.

---

## 🌟 Premium Features

### 🛡️ Automated "Self-Healing" Engine
The system doesn't just watch—it acts. When an anomaly is detected, the backend autonomously triggers tactical protocols such as traffic rerouting and thread isolation.

### 🤖 Generative AI Incident Post-Mortems
Native "AI Analysis" button that parses complex telemetry into human-readable incident reports.

### 🌍 3D Geographical Threat Mapping
Powered by **Pydeck**, the dashboard features a glowing 3D globe that tracks threat origins in real-time.

---

## 🛠️ Technology Stack

-   **Backend**: FastAPI, SQLAlchemy, Pydantic, python-dotenv
-   **Frontend**: Streamlit, Plotly, Pydeck, Custom CSS
-   **ML Engine**: Scikit-Learn (Isolation Forest), PyTorch (Log Autoencoder)

---

## 📂 Project Anatomy

```text
├── backend/                  # FastAPI Core
├── dashboard/                # Synthwave Monitoring UI
├── simulator/                # Edge Client & Live Simulation
├── ml/                       # Hybrid Intelligence (Predict/Retrain)
├── database/                 # SQLAlchemy Models & Schemas
├── logs/                     # Network-wide System Logs
├── unquarantine.py           # Security Reset Utility
├── .env.example              # Configuration Template
└── CROSS_NETWORK_GUIDE.md    # ngrok Setup Instructions
```

---

## 📜 License
MIT License. Built for advanced cloud observability research.
