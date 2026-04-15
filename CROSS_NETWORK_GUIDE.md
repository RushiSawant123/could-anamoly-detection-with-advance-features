# 🌩️ Cross-Network Deployment Guide (ngrok)

This guide explains how to run the **Inference Server** on one network and the **Edge Client (Simulator)** on another.

---

## 1. Expose the Backend via ngrok

Since your local backend runs on `127.0.0.1:8000`, it is invisible to the outside world. To expose it:

1.  **Download ngrok**: [ngrok.com](https://ngrok.com/download)
2.  **Start your Backend**:
    ```powershell
    python -m uvicorn backend.main:app --port 8000
    ```
3.  **Start the Tunnel** (in a new terminal):
    ```powershell
    ngrok http 8000
    ```
4.  **Copy the Forwarding URL**: You will see a URL like `https://a1b2-c3d4.ngrok-free.app`. This is your new "Public API URL".

---

## 2. Configure the Remote Client

On the machine that will run the **Simulator** (the client on a different network):

1.  **Create a `.env` file** in the project root:
    ```bash
    API_URL=https://your-ngrok-url.ngrok-free.app/predict
    ```
2.  **Start the Simulator**:
    ```powershell
    python simulator/live_simulator.py
    ```
    The simulator will now automatically detect the `API_URL` from the `.env` file and send data to your server across the internet!

---

## 3. Configure the Dashboard

If you want to view the dashboard from a different network than the server:

1.  **Update your `.env`**:
    ```bash
    API_HOST=your-ngrok-url.ngrok-free.app
    API_PROTOCOL=https
    API_PORT=443
    ```
2.  **Run the Dashboard**:
    ```powershell
    streamlit run dashboard/app.py
    ```

---

## 🛠️ Performance Tips
- **Keep ngrok running**: If you stop ngrok and restart it, you will get a new URL. You must update your `.env` files accordingly.
- **Latency**: Expect a small delay in chart updates when data travels across the public internet.
