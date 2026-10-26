"""
PlantCare AI - Agronomic Analytics, Rule-Based Assessment, and ML Anomaly Integration
Provides transparent plant-health analysis, explainable watering recommendations,
sensor trend calculations, and Isolation Forest anomaly scoring.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from config import Config
import models

class PlantAnalytics:
    """Core analytics engine for PlantCare AI."""

    def __init__(self):
        self._ml_model = None
        self._ml_metadata = None
        self._load_ml_model()

    def _load_ml_model(self):
        """Loads trained Isolation Forest model and metadata if available."""
        if Config.MODEL_PATH.exists():
            try:
                self._ml_model = joblib.load(Config.MODEL_PATH)
                if Config.MODEL_METADATA_PATH.exists():
                    with open(Config.MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                        self._ml_metadata = json.load(f)
            except Exception as e:
                self._ml_model = None
                self._ml_metadata = None

    def calculate_relative_moisture(
        self,
        soil_voltage: Optional[float],
        dry_v: float,
        wet_v: float,
        invert: bool = True
    ) -> Optional[float]:
        """
        Calculates relative soil moisture percentage (0-100%) from raw voltage.
        Returns None if voltage is missing or calibration is degenerate.
        """
        if soil_voltage is None:
            return None
        if abs(dry_v - wet_v) < 0.1:
            return None  # Uncalibrated or dry/wet values are too close

        if invert:
            # Higher voltage = Drier soil (standard capacitive/resistive sensor behavior)
            moisture = ((dry_v - soil_voltage) / (dry_v - wet_v)) * 100.0
        else:
            # Higher voltage = Wetter soil
            moisture = ((soil_voltage - dry_v) / (wet_v - dry_v)) * 100.0

        return round(max(0.0, min(100.0, moisture)), 1)

    def assess_plant(self, telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs comprehensive agronomic assessment on latest telemetry.
        Returns plant status, transparent explanations, recommendations, and triggering alerts.
        """
        if not telemetry:
            return {
                "overall_status": "Unknown",
                "status_code": "unknown",
                "explanation": "No sensor readings are currently available from ThingSpeak Cloud.",
                "recommendation": "Check Raspberry Pi collector script and cloud connectivity.",
                "confidence": 0.0,
                "diagnostics": {},
                "triggering_factors": []
            }

        settings = models.get_all_settings()
        soil_v = telemetry.get("soil_voltage_v")
        light_v = telemetry.get("light_voltage_v")
        temp_c = telemetry.get("temperature_c")
        press_hpa = telemetry.get("pressure_hpa")
        water_v = telemetry.get("water_voltage_v")

        dry_v = float(settings.get("soil_dry_voltage", 2.65))
        wet_v = float(settings.get("soil_wet_voltage", 1.20))
        invert = bool(int(settings.get("soil_invert", 1)))
        temp_min = float(settings.get("temp_min_c", 18.0))
        temp_max = float(settings.get("temp_max_c", 28.0))
        water_threshold = float(settings.get("water_sensor_alert_threshold", 0.80))

        # Relative moisture calculation
        rel_moisture = self.calculate_relative_moisture(soil_v, dry_v, wet_v, invert)
        is_calibrated = (rel_moisture is not None)

        diagnostics = {}
        triggering_factors = []
        status_points = 0  # 0 = Normal, 1 = Warning, 2 = Critical

        # 1. Soil Moisture Assessment
        if soil_v is None:
            diagnostics["soil"] = {
                "status": "Missing",
                "severity": "warning",
                "reading": None,
                "relative_moisture_pct": None,
                "detail": "Soil moisture sensor reading is missing or null."
            }
            triggering_factors.append("Soil reading missing")
            status_points = max(status_points, 1)
        elif not is_calibrated:
            diagnostics["soil"] = {
                "status": "Uncalibrated",
                "severity": "info",
                "reading": f"{soil_v:.3f} V",
                "relative_moisture_pct": None,
                "detail": f"Raw sensor voltage is {soil_v:.3f} V. Complete the calibration in Settings to view relative moisture percentage."
            }
        else:
            if rel_moisture < 25.0:
                diagnostics["soil"] = {
                    "status": "Dry / Water Depleted",
                    "severity": "critical" if rel_moisture < 15.0 else "warning",
                    "reading": f"{soil_v:.3f} V",
                    "relative_moisture_pct": rel_moisture,
                    "detail": f"Moisture is low ({rel_moisture}%). Root zone is drying out."
                }
                triggering_factors.append(f"Low soil moisture ({rel_moisture}%)")
                status_points = max(status_points, 2 if rel_moisture < 15.0 else 1)
                models.add_alert(
                    severity="critical" if rel_moisture < 15.0 else "warning",
                    affected_sensor="Soil Moisture",
                    triggering_value=soil_v,
                    rule=f"Relative moisture < 25% (Current: {rel_moisture}%)",
                    recommendation="Inspect root zone and apply water manually. (Pump is NOT connected)."
                )
            elif rel_moisture > 85.0:
                diagnostics["soil"] = {
                    "status": "Saturated",
                    "severity": "warning",
                    "reading": f"{soil_v:.3f} V",
                    "relative_moisture_pct": rel_moisture,
                    "detail": f"Soil is near water saturation ({rel_moisture}%). Ensure pot drainage is clear."
                }
                triggering_factors.append(f"Soil saturated ({rel_moisture}%)")
                status_points = max(status_points, 1)
            else:
                diagnostics["soil"] = {
                    "status": "Optimal",
                    "severity": "normal",
                    "reading": f"{soil_v:.3f} V",
                    "relative_moisture_pct": rel_moisture,
                    "detail": f"Soil moisture is in the favorable zone ({rel_moisture}%)."
                }

        # 2. Temperature Assessment (BMP280)
        if temp_c is None:
            diagnostics["temperature"] = {
                "status": "Missing",
                "severity": "warning",
                "reading": None,
                "detail": "BMP280 temperature reading is missing."
            }
            triggering_factors.append("Temperature reading missing")
            status_points = max(status_points, 1)
        elif temp_c < (temp_min - 4.0):
            diagnostics["temperature"] = {
                "status": "Severe Cold Stress",
                "severity": "critical",
                "reading": f"{temp_c:.1f} °C",
                "detail": f"Temperature ({temp_c:.1f} °C) is significantly below the minimum threshold ({temp_min} °C)."
            }
            triggering_factors.append(f"Severe cold stress ({temp_c:.1f} °C)")
            status_points = max(status_points, 2)
            models.add_alert("critical", "Temperature", temp_c, f"Temp < {temp_min - 4.0}°C", "Move plant away from cold drafts or heating vents.")
        elif temp_c < temp_min:
            diagnostics["temperature"] = {
                "status": "Chilly",
                "severity": "warning",
                "reading": f"{temp_c:.1f} °C",
                "detail": f"Temperature ({temp_c:.1f} °C) is slightly below the configured minimum ({temp_min} °C)."
            }
            triggering_factors.append(f"Cool temperature ({temp_c:.1f} °C)")
            status_points = max(status_points, 1)
        elif temp_c > (temp_max + 4.0):
            diagnostics["temperature"] = {
                "status": "Severe Heat Stress",
                "severity": "critical",
                "reading": f"{temp_c:.1f} °C",
                "detail": f"Temperature ({temp_c:.1f} °C) is significantly above the maximum threshold ({temp_max} °C)."
            }
            triggering_factors.append(f"Severe heat stress ({temp_c:.1f} °C)")
            status_points = max(status_points, 2)
            models.add_alert("critical", "Temperature", temp_c, f"Temp > {temp_max + 4.0}°C", "Shield plant from harsh direct sunlight or heat sources.")
        elif temp_c > temp_max:
            diagnostics["temperature"] = {
                "status": "Warm",
                "severity": "warning",
                "reading": f"{temp_c:.1f} °C",
                "detail": f"Temperature ({temp_c:.1f} °C) is above the preferred maximum ({temp_max} °C)."
            }
            triggering_factors.append(f"Warm temperature ({temp_c:.1f} °C)")
            status_points = max(status_points, 1)
        else:
            diagnostics["temperature"] = {
                "status": "Optimal",
                "severity": "normal",
                "reading": f"{temp_c:.1f} °C",
                "detail": f"Ambient temperature is within the ideal range ({temp_min} - {temp_max} °C)."
            }

        # Explicit note about BMP280 not measuring humidity
        diagnostics["temperature"]["humidity_note"] = (
            "BMP280 measures temperature and barometric pressure only. "
            "It does NOT measure relative humidity. Humidity is not estimated or fabricated."
        )

        # 3. Light Sensor Assessment
        if light_v is None:
            diagnostics["light"] = {
                "status": "Missing",
                "severity": "warning",
                "reading": None,
                "detail": "Light sensor reading is missing."
            }
        elif light_v < 0.35:
            diagnostics["light"] = {
                "status": "Dim / Night",
                "severity": "normal",
                "reading": f"{light_v:.3f} V",
                "detail": f"Sensor voltage {light_v:.3f} V indicates dark/night or very low indirect lighting."
            }
        elif light_v < 1.6:
            diagnostics["light"] = {
                "status": "Moderate Indirect Light",
                "severity": "normal",
                "reading": f"{light_v:.3f} V",
                "detail": f"Sensor voltage {light_v:.3f} V indicates healthy diffuse ambient light."
            }
        elif light_v < 2.7:
            diagnostics["light"] = {
                "status": "Bright Light",
                "severity": "normal",
                "reading": f"{light_v:.3f} V",
                "detail": f"Sensor voltage {light_v:.3f} V indicates bright ambient sunlight."
            }
        else:
            diagnostics["light"] = {
                "status": "High Intensity / Direct",
                "severity": "warning",
                "reading": f"{light_v:.3f} V",
                "detail": f"Sensor voltage {light_v:.3f} V suggests intense or direct illumination. Ensure sensitive leaves are not burning."
            }

        # 4. Barometric Pressure Assessment (BMP280)
        if press_hpa is not None:
            diagnostics["pressure"] = {
                "status": "Environmental Weather Metric",
                "severity": "normal",
                "reading": f"{press_hpa:.1f} hPa",
                "detail": f"Atmospheric pressure is {press_hpa:.1f} hPa. Reflects ambient weather trends rather than direct plant physiological stress."
            }
        else:
            diagnostics["pressure"] = {
                "status": "Missing",
                "severity": "warning",
                "reading": None,
                "detail": "BMP280 pressure reading is missing."
            }

        # 5. Water Sensor Assessment (A0 raw water sensor)
        if water_v is not None:
            is_wet = water_v >= water_threshold
            diagnostics["water_sensor"] = {
                "status": "Moisture Detected" if is_wet else "Dry Traces",
                "severity": "info",
                "reading": f"{water_v:.3f} V",
                "detail": (
                    f"Water sensor signal is {water_v:.3f} V. "
                    "Note: This is a raw analog sensor signal, not a calibrated water tank or reservoir measurement."
                )
            }
        else:
            diagnostics["water_sensor"] = {
                "status": "Missing",
                "severity": "info",
                "reading": None,
                "detail": "Water sensor reading is missing."
            }

        # Overall Status Synthesis
        if status_points >= 2:
            overall_status = "Critical"
            status_code = "critical"
            explanation = "One or more environmental parameters have exceeded safe physiological thresholds."
        elif status_points == 1:
            overall_status = "Needs Attention"
            status_code = "needs_attention"
            explanation = "Plant conditions are drifting away from optimal targets."
        else:
            overall_status = "Normal"
            status_code = "normal"
            explanation = "All core environmental parameters are within comfortable growth ranges."

        # Actionable Recommendation Synthesis
        # Crucial requirement: Water pump is NOT connected yet. Show recommendations only!
        if rel_moisture is not None and rel_moisture < 25.0:
            recommendation = (
                f"Watering Recommended: Soil moisture is low ({rel_moisture}%). "
                "The water pump is NOT connected — please manually inspect the soil and add approximately 150–250 ml of water."
            )
            confidence = 0.90
        elif temp_c is not None and temp_c > temp_max:
            recommendation = (
                f"Thermal Cooling: Ambient temperature ({temp_c:.1f} °C) is high. "
                "Increase gentle room ventilation or pull thin sheer curtains to soften direct sunlight."
            )
            confidence = 0.85
        elif temp_c is not None and temp_c < temp_min:
            recommendation = (
                f"Thermal Protection: Ambient temperature ({temp_c:.1f} °C) is cool. "
                "Keep plant away from cold window drafts."
            )
            confidence = 0.85
        else:
            recommendation = "Maintain current routine. Environmental parameters are stable."
            confidence = 0.95

        return {
            "overall_status": overall_status,
            "status_code": status_code,
            "explanation": explanation,
            "recommendation": recommendation,
            "confidence": confidence,
            "diagnostics": diagnostics,
            "triggering_factors": triggering_factors,
            "plant_profile": {
                "name": settings.get("plant_name", "My Plant"),
                "type": settings.get("plant_type", "Houseplant")
            }
        }

    def compute_summary_and_trends(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates min, max, avg, count, and trend arrows for all sensor metrics."""
        if not readings:
            return {"count": 0, "metrics": {}}

        df = pd.DataFrame(readings)
        keys = ["soil_voltage_v", "light_voltage_v", "temperature_c", "pressure_hpa", "water_voltage_v"]
        metrics = {}

        for k in keys:
            if k in df.columns and not df[k].dropna().empty:
                series = pd.to_numeric(df[k], errors="coerce").dropna()
                if len(series) > 0:
                    val_min = round(float(series.min()), 3)
                    val_max = round(float(series.max()), 3)
                    val_avg = round(float(series.mean()), 3)
                    val_latest = round(float(series.iloc[-1]), 3)

                    # Trend direction over last 5 readings if available
                    trend = "stable"
                    if len(series) >= 3:
                        delta = series.iloc[-1] - series.iloc[-3]
                        threshold = 0.03 if "voltage" in k else (0.4 if "temperature" in k else 1.0)
                        if delta > threshold:
                            trend = "rising"
                        elif delta < -threshold:
                            trend = "falling"

                    metrics[k] = {
                        "min": val_min,
                        "max": val_max,
                        "avg": val_avg,
                        "latest": val_latest,
                        "trend": trend,
                        "count": len(series)
                    }

        return {
            "count": len(readings),
            "metrics": metrics
        }

    def evaluate_anomalies(self, telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs ML anomaly evaluation if trained model is present.
        Returns anomaly status, score, model metadata, and transparent explanations.
        """
        # Reload model if it was trained recently
        if self._ml_model is None:
            self._load_ml_model()

        if self._ml_model is None:
            return {
                "available": False,
                "status": "not_trained",
                "message": (
                    "ML Anomaly Model is not yet trained. Run 'python ml/train_anomaly_model.py' "
                    "once at least 50 sensor entries have been collected."
                ),
                "is_anomaly": False,
                "anomaly_score": None
            }

        if not telemetry:
            return {
                "available": True,
                "status": "no_data",
                "message": "No live telemetry available to evaluate.",
                "is_anomaly": False,
                "anomaly_score": None
            }

        # Prepare feature vector: [soil_voltage_v, light_voltage_v, temperature_c, pressure_hpa, water_voltage_v]
        features = [
            telemetry.get("soil_voltage_v"),
            telemetry.get("light_voltage_v"),
            telemetry.get("temperature_c"),
            telemetry.get("pressure_hpa"),
            telemetry.get("water_voltage_v")
        ]

        if any(f is None for f in features):
            return {
                "available": True,
                "status": "incomplete_features",
                "message": "One or more sensor features are null in the current reading.",
                "is_anomaly": False,
                "anomaly_score": None
            }

        try:
            X = np.array([features], dtype=float)
            pred = self._ml_model.predict(X)[0]  # 1 for normal, -1 for anomaly
            # decision_function: lower means more anomalous (negative = anomaly)
            score = float(self._ml_model.decision_function(X)[0])
            is_anomaly = bool(pred == -1)

            explanation = (
                "Unusual sensor pattern flagged by Isolation Forest. "
                "Check for sensor dislodgement, sudden thermal swings, or wiring issues."
                if is_anomaly else
                "Current readings conform to normal operating boundaries learned by the model."
            )

            return {
                "available": True,
                "status": "evaluated",
                "is_anomaly": is_anomaly,
                "anomaly_score": round(score, 4),
                "prediction": "Anomaly" if is_anomaly else "Normal",
                "explanation": explanation,
                "model_info": self._ml_metadata or {"model": "Isolation Forest"}
            }
        except Exception as e:
            return {
                "available": True,
                "status": "error",
                "message": f"ML evaluation failed: {str(e)}",
                "is_anomaly": False,
                "anomaly_score": None
            }

# Global singleton analytics instance
plant_analytics = PlantAnalytics()
