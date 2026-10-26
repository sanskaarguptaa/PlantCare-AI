"""
PlantCare AI - Machine Learning Anomaly Detection Model Trainer
Trains an Isolation Forest model to detect unusual multi-sensor drifts,
extreme weather excursions, or potential sensor hardware faults.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest

# Paths
ML_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ML_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_PATH = ML_DIR / "anomaly_model.pkl"
METADATA_PATH = ML_DIR / "model_metadata.json"

FEATURES = [
    "soil_voltage_v",
    "light_voltage_v",
    "temperature_c",
    "pressure_hpa",
    "water_voltage_v"
]

def load_training_data() -> pd.DataFrame:
    """
    Searches for available sensor data sources:
    1. Pi collector export: data/plant_data_all.csv
    2. Seed sample data: data/plant_data_sample.csv
    3. SQLite cached readings: backend/plantcare.db
    """
    # 1. Check for real collector CSV
    real_csv = DATA_DIR / "plant_data_all.csv"
    if real_csv.exists():
        print(f"Loading real telemetry from: {real_csv}")
        df = pd.read_csv(real_csv)
        if all(col in df.columns for col in FEATURES):
            return df

    # 2. Check for sample CSV
    sample_csv = DATA_DIR / "plant_data_sample.csv"
    if sample_csv.exists():
        print(f"Loading telemetry from sample dataset: {sample_csv}")
        df = pd.read_csv(sample_csv)
        if all(col in df.columns for col in FEATURES):
            return df

    # 3. Check SQLite database
    db_path = PROJECT_ROOT / "backend" / "plantcare.db"
    if db_path.exists():
        import sqlite3
        print(f"Loading telemetry from SQLite database: {db_path}")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(
                "SELECT soil_voltage_v, light_voltage_v, temperature_c, pressure_hpa, water_voltage_v FROM cached_readings",
                conn
            )
            if not df.empty:
                return df

    raise FileNotFoundError(
        "No training data found. Please place 'plant_data_all.csv' in the data/ directory, "
        "or run the collector to populate cached readings."
    )

def train_model():
    """Trains and serializes the Isolation Forest anomaly detector."""
    print("=" * 65)
    print("PlantCare AI - Anomaly Detection Model Training")
    print("=" * 65)

    df = load_training_data()

    # Preprocessing & cleaning
    clean_df = df[FEATURES].dropna()
    print(f"Loaded {len(df)} total rows. {len(clean_df)} complete feature rows after cleaning.")

    if len(clean_df) < 20:
        print("ERROR: Insufficient data samples to train model. Minimum 20 complete rows required.")
        sys.exit(1)

    X = clean_df.values

    # Train Isolation Forest
    contamination_rate = 0.05  # Expect ~5% of training samples may represent anomalies/spikes
    print(f"Training Isolation Forest (contamination={contamination_rate}, n_estimators=100)...")
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination_rate,
        random_state=42,
        max_samples="auto"
    )
    model.fit(X)

    # In-sample evaluation
    preds = model.predict(X)
    scores = model.decision_function(X)
    n_anomalies = int(np.sum(preds == -1))
    n_normal = int(np.sum(preds == 1))

    print(f"In-sample results: {n_normal} normal readings, {n_anomalies} anomalies flagged ({n_anomalies / len(X):.1%}).")
    print(f"Decision score range: Min={scores.min():.4f}, Max={scores.max():.4f}, Mean={scores.mean():.4f}")

    # Compute baseline statistics for feature deviation diagnostics
    feature_stats = {}
    for feat in FEATURES:
        series = clean_df[feat]
        feature_stats[feat] = {
            "mean": round(float(series.mean()), 3),
            "std": round(float(series.std()), 3),
            "min": round(float(series.min()), 3),
            "max": round(float(series.max()), 3)
        }

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")

    # Save metadata
    metadata = {
        "model_type": "IsolationForest",
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(clean_df),
        "contamination_rate": contamination_rate,
        "features": FEATURES,
        "feature_stats": feature_stats,
        "decision_threshold": 0.0,
        "notes": "Trained for sensor anomaly detection. Flagged readings represent unusual sensor shifts."
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {METADATA_PATH}")
    print("=" * 65)
    print("Training completed successfully!")
    print("=" * 65)

if __name__ == "__main__":
    train_model()
