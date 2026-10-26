"""
PlantCare AI - Machine Learning Model Evaluation Tool
Inspects the trained Isolation Forest model, tests sample telemetry vectors,
and displays explainable feature deviations.
"""

import json
import joblib
import numpy as np
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
MODEL_PATH = ML_DIR / "anomaly_model.pkl"
METADATA_PATH = ML_DIR / "model_metadata.json"

def evaluate_test_cases():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        print("Model or metadata not found. Please run 'python train_anomaly_model.py' first.")
        return

    model = joblib.load(MODEL_PATH)
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print("=" * 65)
    print("PlantCare AI - Model Evaluation & Diagnostic Explanations")
    print(f"Model Type: {meta['model_type']} (v{meta['version']})")
    print(f"Trained At: {meta['trained_at']}")
    print(f"Training Samples: {meta['training_samples']}")
    print("=" * 65)

    # Test cases:
    # 1. Normal diurnal reading
    # 2. Extreme heat wave spike (42C)
    # 3. Disconnected sensor (0V on all ADC channels)
    test_cases = [
        {
            "name": "Typical Normal Afternoon",
            "features": [1.95, 2.10, 24.5, 1013.2, 0.05]
        },
        {
            "name": "Extreme Temperature Spike (42.0 °C)",
            "features": [1.95, 2.10, 42.0, 1013.2, 0.05]
        },
        {
            "name": "Sensor Disconnection / Floating ADC (0.01 V)",
            "features": [0.01, 0.01, 24.5, 1013.2, 0.00]
        }
    ]

    features_list = meta["features"]
    stats = meta["feature_stats"]

    for tc in test_cases:
        X = np.array([tc["features"]], dtype=float)
        pred = model.predict(X)[0]  # 1: Normal, -1: Anomaly
        score = float(model.decision_function(X)[0])
        status = "NORMAL" if pred == 1 else "ANOMALY DETECTED"

        print(f"\nTest Case: {tc['name']}")
        print(f"  Values: {dict(zip(features_list, tc['features']))}")
        print(f"  Classification: [{status}] (Score: {score:.4f})")

        # Explain deviations from baseline mean
        deviations = []
        for feat, val in zip(features_list, tc["features"]):
            mean = stats[feat]["mean"]
            std = max(stats[feat]["std"], 0.001)
            z_score = abs(val - mean) / std
            if z_score > 2.5:
                deviations.append(f"{feat} deviates significantly (value={val}, baseline={mean}±{std})")

        if deviations:
            print("  Top Explanations:")
            for d in deviations:
                print(f"   • {d}")
        else:
            print("  Readings align with historical baseline distributions.")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    evaluate_test_cases()
