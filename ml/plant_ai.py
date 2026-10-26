"""
Plant AI Engine:
1. Calculates Vapor Pressure Deficit (VPD)
2. Evaluates Plant Health Index (0-100%)
3. Runs Unsupervised Anomaly Detection (Isolation Forest)
4. Generates natural language plant diagnostics & smart watering recommendations
"""
import math
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np

from config import MODEL_PATH, PLANT_PROFILES, DEFAULT_PROFILE

logger = logging.getLogger("PlantAI")

class PlantAI:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("Loaded trained Isolation Forest model from disk.")
                return
            except Exception as e:
                logger.warning(f"Error loading model from {MODEL_PATH}: {e}")

        # Train a new model if possible
        try:
            from ml.train_model import train_and_save_model
            self.model = train_and_save_model()
        except Exception as e:
            logger.warning(f"Could not initialize ML model: {e}. Falling back to heuristic anomaly detection.")

    @staticmethod
    def calculate_vpd(temp_c: float, humidity_pct: float) -> float:
        """
        Vapor Pressure Deficit (VPD) in kPa:
        VPD = VP_sat - VP_act
        VP_sat = 0.61078 * exp((17.27 * T) / (T + 237.3))
        VP_act = VP_sat * (RH / 100)
        """
        if temp_c is None or humidity_pct is None:
            return 0.8
        try:
            vp_sat = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
            vp_act = vp_sat * (max(0.0, min(100.0, humidity_pct)) / 100.0)
            return max(0.0, round(vp_sat - vp_act, 3))
        except Exception:
            return 0.8

    def calculate_health_index(self, readings: Dict[str, Any], profile_key: str = DEFAULT_PROFILE) -> float:
        """
        Computes an overall Plant Health Score from 0 to 100%.
        Weights:
        - Soil Moisture adequacy: 40%
        - VPD / Transpiration rate: 25%
        - Temperature comfort: 20%
        - Light adequacy: 15%
        """
        profile = PLANT_PROFILES.get(profile_key, PLANT_PROFILES[DEFAULT_PROFILE])
        
        moisture = readings.get("soil_moisture", 50.0)
        temp = readings.get("temperature", 22.0)
        vpd = readings.get("vpd", 0.8)
        lux = readings.get("lux", 1500.0)

        # 1. Soil Moisture Score (0 to 40 pts)
        if profile["min_moisture"] <= moisture <= profile["max_moisture"]:
            moisture_score = 40.0
        elif moisture < profile["min_moisture"]:
            deficiency = profile["min_moisture"] - moisture
            moisture_score = max(5.0, 40.0 - (deficiency * 1.5))
        else: # Overwatered
            excess = moisture - profile["max_moisture"]
            moisture_score = max(10.0, 40.0 - (excess * 1.2))

        # 2. VPD Score (0 to 25 pts)
        if profile["optimal_vpd_min"] <= vpd <= profile["optimal_vpd_max"]:
            vpd_score = 25.0
        elif vpd < profile["optimal_vpd_min"]:
            vpd_score = max(5.0, 25.0 - (profile["optimal_vpd_min"] - vpd) * 30)
        else:
            vpd_score = max(5.0, 25.0 - (vpd - profile["optimal_vpd_max"]) * 20)

        # 3. Temperature Score (0 to 20 pts)
        if profile["min_temp"] <= temp <= profile["max_temp"]:
            temp_score = 20.0
        else:
            diff = min(abs(temp - profile["min_temp"]), abs(temp - profile["max_temp"]))
            temp_score = max(2.0, 20.0 - (diff * 2.5))

        # 4. Light Score (0 to 15 pts)
        if profile["min_lux"] <= lux <= profile["max_lux"]:
            light_score = 15.0
        elif lux < profile["min_lux"]:
            light_score = max(3.0, 15.0 * (lux / max(1.0, profile["min_lux"])))
        else: # Excess light / direct scorching
            light_score = 10.0

        total_health = moisture_score + vpd_score + temp_score + light_score
        return round(max(0.0, min(100.0, total_health)), 1)

    def detect_anomaly(self, readings: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Uses Isolation Forest model to detect unusual conditions.
        Returns:
            (is_anomaly: bool, anomaly_score: float)
            Negative score indicates anomalous pattern.
        """
        moisture = readings.get("soil_moisture", 50.0)
        temp = readings.get("temperature", 22.0)
        hum = readings.get("humidity", 55.0)
        lux = readings.get("lux", 1200.0)
        vpd = readings.get("vpd", 0.8)

        if self.model is not None:
            try:
                features = np.array([[moisture, temp, hum, lux, vpd]])
                pred = self.model.predict(features)[0] # 1 = normal, -1 = anomaly
                score = self.model.decision_function(features)[0] # Lower = more anomalous
                is_anomaly = bool(pred == -1)
                return is_anomaly, round(float(score), 3)
            except Exception as e:
                logger.debug(f"Model inference failed ({e}), falling back to heuristic.")

        # Heuristic fallback if model not loaded
        is_anomaly = (
            moisture < 12.0 or moisture > 95.0 or
            temp > 38.0 or temp < 5.0 or
            hum < 18.0 or
            vpd > 2.2
        )
        score = -0.5 if is_anomaly else 0.5
        return is_anomaly, score

    def generate_diagnostics(self, readings: Dict[str, Any], profile_key: str = DEFAULT_PROFILE) -> Dict[str, Any]:
        """
        Generates comprehensive diagnostic feedback, alerts, and watering guidance.
        """
        profile = PLANT_PROFILES.get(profile_key, PLANT_PROFILES[DEFAULT_PROFILE])
        moisture = readings.get("soil_moisture", 50.0)
        temp = readings.get("temperature", 22.0)
        hum = readings.get("humidity", 55.0)
        lux = readings.get("lux", 1200.0)
        vpd = readings.get("vpd", 0.8)

        is_anomaly, anomaly_score = self.detect_anomaly(readings)
        health_index = self.calculate_health_index(readings, profile_key)

        insights = []
        action_required = False
        urgency = "normal"

        # Moisture diagnosis
        if moisture < profile["min_moisture"]:
            insights.append(f"Soil is dry ({moisture}%). Plant needs watering soon.")
            action_required = True
            urgency = "high" if moisture < (profile["min_moisture"] - 15) else "medium"
        elif moisture > profile["max_moisture"]:
            insights.append(f"Soil is very damp ({moisture}%). Hold off on watering to avoid root rot.")
        else:
            insights.append(f"Soil moisture is optimal ({moisture}%). Roots have sufficient hydration.")

        # VPD / Transpiration diagnosis
        if vpd > profile["optimal_vpd_max"]:
            insights.append(f"Air drying stress is high (VPD: {vpd} kPa). Foliage is losing water rapidly.")
            if urgency == "normal": urgency = "medium"
        elif vpd < profile["optimal_vpd_min"]:
            insights.append(f"Air is stagnant/humid (VPD: {vpd} kPa). Transpiration is reduced; monitor for mold.")

        # Temperature diagnosis
        if temp > profile["max_temp"]:
            insights.append(f"Warm ambient temperature ({temp}°C). Evaporation rate is accelerated.")
        elif temp < profile["min_temp"]:
            insights.append(f"Chilly environment ({temp}°C). Growth rate will slow.")

        # Light diagnosis
        if lux < profile["min_lux"]:
            insights.append(f"Light is low ({lux} Lux). Plant might stretch or experience weak photosynthesis.")
        elif lux > profile["max_lux"]:
            insights.append(f"Very intense light ({lux} Lux). Check for scorched leaves.")

        # Anomaly insight
        if is_anomaly:
            insights.insert(0, f"⚠️ AI Anomaly Detected (Score: {anomaly_score:.2f})! Unusual environmental condition detected.")
            if urgency == "normal":
                urgency = "medium"

        return {
            "health_index": health_index,
            "vpd": vpd,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "urgency": urgency,
            "action_required": action_required,
            "status_title": "Thriving" if health_index >= 80 else ("Needs Attention" if health_index >= 50 else "Critical Stress"),
            "insights": insights,
            "active_profile": profile["name"]
        }
