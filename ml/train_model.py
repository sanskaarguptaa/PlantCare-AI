"""
Generates baseline healthy plant environmental training data and trains
an Isolation Forest model for Unsupervised Anomaly Detection.
"""
import os
import pickle
import numpy as np
import math
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent
MODEL_FILE = MODEL_DIR / "anomaly_model.pkl"

def calculate_vpd(temp_c: float, humidity_pct: float) -> float:
    vp_sat = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    vp_act = vp_sat * (humidity_pct / 100.0)
    return max(0.0, vp_sat - vp_act)

def generate_training_data(n_samples: int = 5000) -> np.ndarray:
    """
    Generates synthetic training points representing healthy indoor/greenhouse plant conditions:
    Features: [soil_moisture, temperature, humidity, lux, vpd]
    """
    np.random.seed(42)

    # Normal healthy distributions
    moisture = np.random.uniform(35.0, 75.0, n_samples)
    temperature = np.random.normal(23.0, 3.0, n_samples)
    temperature = np.clip(temperature, 16.0, 30.0)
    
    humidity = np.random.normal(58.0, 10.0, n_samples)
    humidity = np.clip(humidity, 35.0, 85.0)

    # Realistic lux range (dim indoor to bright indirect)
    lux = np.random.exponential(scale=1800, size=n_samples)
    lux = np.clip(lux, 200, 12000)

    # Calculate VPD for each sample
    vpd = np.array([calculate_vpd(t, h) for t, h in zip(temperature, humidity)])

    # Add a small proportion of extreme anomalies (3%) so the model establishes tight boundaries
    n_anomalies = int(n_samples * 0.03)
    anomaly_idx = np.random.choice(n_samples, n_anomalies, replace=False)
    
    # Inject various anomaly archetypes
    for i, idx in enumerate(anomaly_idx):
        if i % 3 == 0:
            temperature[idx] = np.random.uniform(37.0, 45.0) # Heatwave
            humidity[idx] = np.random.uniform(10.0, 25.0)
        elif i % 3 == 1:
            moisture[idx] = np.random.uniform(3.0, 15.0)     # Severe drought / sensor dry
        else:
            moisture[idx] = np.random.uniform(88.0, 99.0)    # Waterlogged
            vpd[idx] = 0.15

    data = np.column_stack([moisture, temperature, humidity, lux, vpd])
    return data

def train_and_save_model():
    """Trains IsolationForest model and writes to disk."""
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        print("scikit-learn is not installed yet. Skipping training until installed.")
        return None

    print("Generating representative plant training data...")
    X = generate_training_data(6000)

    print("Training Isolation Forest Anomaly Detector...")
    # Contamination set to ~4% expected outliers
    model = IsolationForest(
        n_estimators=100,
        contamination=0.04,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

    print(f"Model successfully trained and saved to: {MODEL_FILE}")
    return model

if __name__ == "__main__":
    train_and_save_model()
