"""
FloraAI Quick Launch Script.
Pre-trains ML model if missing and starts the FastAPI server with live dashboard.
"""
import sys
import uvicorn
from ml.train_model import train_and_save_model
from config import MODEL_PATH, SERVER_HOST, SERVER_PORT

def main():
    print("=" * 65)
    print("  FloraAI: Smart Plant Monitoring & Automatic Watering System")
    print("=" * 65)

    if not MODEL_PATH.exists():
        print("[AI] Anomaly detection model not found. Training baseline model...")
        train_and_save_model()
    else:
        print("[AI] Trained Machine Learning model ready.")

    print(f"\n[SERVER] Starting web server and telemetry engine...")
    print(f"[SERVER] Dashboard URL: http://localhost:{SERVER_PORT}")
    print(f"[SERVER] (On local network: http://<your-pi-ip>:{SERVER_PORT})")
    print("=" * 65)

    uvicorn.run(
        "server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()
