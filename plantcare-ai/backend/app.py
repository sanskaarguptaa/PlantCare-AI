"""
PlantCare AI - Flask Application and REST API
Provides secure, validated endpoints for sensor telemetry, historical analytics,
agronomic recommendations, machine learning anomaly detection, and settings management.
"""

import io
import csv
from datetime import datetime, timezone
from flask import Flask, jsonify, request, send_file, make_response, send_from_directory
from flask_cors import CORS
from config import Config
import models
from thingspeak_client import thingspeak_client
from analytics import plant_analytics

app = Flask(__name__)

# Configure Cross-Origin Resource Sharing (CORS)
# Allows requests from Vite development server or configured origin
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Initialize SQLite database tables
with app.app_context():
    models.init_db()


# ------------------------------------------------------------------------------
# 1. System Health & Diagnostics
# ------------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns backend system status without exposing sensitive credentials."""
    safe_info = Config.get_safe_info()
    return jsonify({
        "status": "healthy",
        "service": "PlantCare AI Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cloud_configured": safe_info["channel_id_configured"],
        "demo_mode": safe_info["demo_mode"],
        "database_connected": safe_info["database_exists"],
        "ml_model_loaded": safe_info["ml_model_exists"]
    }), 200


@app.route("/api/status/cloud", methods=["GET"])
def cloud_status():
    """Returns detailed non-sensitive cloud connection diagnostics."""
    status = thingspeak_client.get_connection_status()
    return jsonify(status), 200


# ------------------------------------------------------------------------------
# 2. Sensor Telemetry Endpoints
# ------------------------------------------------------------------------------

@app.route("/api/sensors/latest", methods=["GET"])
def get_latest_sensor_data():
    """
    Retrieves the latest available sensor reading.
    Returns parsed sensor values, data freshness, and data source ('cloud', 'cached', or 'demo').
    """
    force = request.args.get("force", "false").lower() in ("true", "1")
    result = thingspeak_client.get_latest(force_refresh=force)
    
    # Calculate calibrated relative moisture if reading is present
    if result.get("data"):
        data = result["data"]
        settings = models.get_all_settings()
        dry_v = float(settings.get("soil_dry_voltage", 2.65))
        wet_v = float(settings.get("soil_wet_voltage", 1.20))
        invert = bool(int(settings.get("soil_invert", 1)))
        
        rel_moisture = plant_analytics.calculate_relative_moisture(
            data.get("soil_voltage_v"), dry_v, wet_v, invert
        )
        data["relative_soil_moisture_pct"] = rel_moisture
        data["soil_calibrated"] = (rel_moisture is not None)

    return jsonify(result), 200


@app.route("/api/sensors/history", methods=["GET"])
def get_sensor_history():
    """
    Retrieves historical readings.
    Query parameters:
      - range: '1h', '24h', '7d', 'all' (default: '24h')
      - limit: integer between 1 and 800 (default: 100)
    """
    range_param = request.args.get("range", "24h").lower()
    limit = min(max(request.args.get("limit", 100, type=int), 1), 800)

    hours_map = {
        "1h": 1,
        "24h": 24,
        "7d": 168,
        "all": None
    }
    hours = hours_map.get(range_param, 24)

    history = thingspeak_client.get_history(hours=hours, limit=limit)
    return jsonify(history), 200


# ------------------------------------------------------------------------------
# 3. Agronomic Analytics & Insights
# ------------------------------------------------------------------------------

@app.route("/api/analytics/summary", methods=["GET"])
def get_analytics_summary():
    """Returns summary statistics (min, max, avg, trend) for available historical readings."""
    history = thingspeak_client.get_history(hours=24, limit=120)
    readings = history.get("readings", [])
    summary = plant_analytics.compute_summary_and_trends(readings)
    summary["data_source"] = history.get("data_source", "none")
    return jsonify(summary), 200


@app.route("/api/analytics/plant-status", methods=["GET"])
def get_plant_status():
    """
    Evaluates latest telemetry using agronomic rules.
    Returns status (Normal, Needs Attention, Critical), explainable diagnosis, and recommendations.
    """
    latest = thingspeak_client.get_latest()
    telemetry = latest.get("data")
    assessment = plant_analytics.assess_plant(telemetry)
    assessment["data_source"] = latest.get("data_source", "none")
    assessment["freshness"] = latest.get("freshness", {})
    return jsonify(assessment), 200


@app.route("/api/analytics/anomalies", methods=["GET"])
def get_anomaly_evaluation():
    """Runs ML anomaly evaluation (Isolation Forest) on current sensor reading."""
    latest = thingspeak_client.get_latest()
    telemetry = latest.get("data")
    anomalies = plant_analytics.evaluate_anomalies(telemetry)
    return jsonify(anomalies), 200


# ------------------------------------------------------------------------------
# 4. Alerts Management
# ------------------------------------------------------------------------------

@app.route("/api/alerts", methods=["GET"])
def list_alerts():
    """Retrieves recorded alerts."""
    unresolved_only = request.args.get("unresolved", "false").lower() in ("true", "1")
    limit = min(request.args.get("limit", 50, type=int), 200)
    alerts = models.get_alerts(limit=limit, unresolved_only=unresolved_only)
    return jsonify({"count": len(alerts), "alerts": alerts}), 200


@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert_endpoint(alert_id: int):
    """Marks an alert as resolved."""
    success = models.resolve_alert(alert_id)
    if success:
        return jsonify({"status": "success", "message": f"Alert {alert_id} resolved."}), 200
    return jsonify({"status": "error", "message": "Alert not found or already resolved."}), 404


# ------------------------------------------------------------------------------
# 5. Settings & Calibration
# ------------------------------------------------------------------------------

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Returns non-secret user settings and calibration parameters."""
    settings = models.get_all_settings()
    return jsonify(settings), 200


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    """Validates and updates user settings."""
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    # Whitelist of allowed settings keys with type validators
    allowed_keys = {
        "plant_name": str,
        "plant_type": str,
        "temp_min_c": float,
        "temp_max_c": float,
        "temp_unit": str,
        "soil_dry_voltage": float,
        "soil_wet_voltage": float,
        "soil_invert": int,
        "light_threshold_voltage": float,
        "water_sensor_alert_threshold": float,
        "dashboard_refresh_sec": int,
        "demo_mode": int
    }

    clean_settings = {}
    for k, v in payload.items():
        if k in allowed_keys:
            try:
                converter = allowed_keys[k]
                clean_settings[k] = converter(v)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": f"Invalid type for setting '{k}'"}), 400

    updated = models.update_settings(clean_settings)
    return jsonify({"status": "success", "settings": updated}), 200


@app.route("/api/demo/toggle", methods=["POST"])
def toggle_demo():
    """Toggles demo mode on or off."""
    payload = request.get_json(silent=True) or {}
    current = models.get_setting("demo_mode", 0)
    new_val = 1 if (current == 0 or current == "0") else 0
    if "enabled" in payload:
        new_val = 1 if payload["enabled"] else 0

    models.update_setting("demo_mode", new_val)
    return jsonify({
        "status": "success",
        "demo_mode": bool(new_val),
        "message": f"Demo Mode set to {bool(new_val)}"
    }), 200


# ------------------------------------------------------------------------------
# 6. CSV Data Export
# ------------------------------------------------------------------------------

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Exports historical sensor readings as a downloadable CSV file."""
    range_param = request.args.get("range", "24h").lower()
    hours_map = {"1h": 1, "24h": 24, "7d": 168, "all": None}
    hours = hours_map.get(range_param, 24)

    history = thingspeak_client.get_history(hours=hours, limit=800)
    readings = history.get("readings", [])

    si = io.StringIO()
    writer = csv.writer(si)
    
    # Standard header matching domain fields
    writer.writerow([
        "entry_id", "timestamp_utc", "soil_voltage_v", "light_voltage_v",
        "temperature_c", "pressure_hpa", "water_voltage_v"
    ])

    for r in readings:
        writer.writerow([
            r.get("entry_id", ""),
            r.get("created_at", ""),
            r.get("soil_voltage_v", ""),
            r.get("light_voltage_v", ""),
            r.get("temperature_c", ""),
            r.get("pressure_hpa", ""),
            r.get("water_voltage_v", "")
        ])

    output = make_response(si.getvalue())
    filename = f"plantcare_readings_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output


# ------------------------------------------------------------------------------
# Frontend Static Asset Serving (Production Build)
# ------------------------------------------------------------------------------

FRONTEND_DIST = Config.PROJECT_ROOT / "frontend" / "dist"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # Don't intercept API routes
    if path.startswith("api/"):
        return jsonify({"status": "error", "code": 404, "message": "API endpoint not found"}), 404

    # If static file exists in dist, serve it
    if path != "" and (FRONTEND_DIST / path).exists():
        return send_from_directory(FRONTEND_DIST, path)

    # Otherwise serve index.html (SPA fallback)
    if (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return jsonify({
        "service": "PlantCare AI API Server",
        "notice": "Frontend build not detected. Run 'npm run build' in frontend/ or access Vite dev server at http://localhost:5173"
    })


# ------------------------------------------------------------------------------
# Error Handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "code": 404, "message": "Endpoint not found"}), 404
    if (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"status": "error", "code": 404, "message": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "code": 500, "message": "An internal server error occurred"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

