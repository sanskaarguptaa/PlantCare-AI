"""
PlantCare AI - Backend Test Suite
Tests API endpoints, ThingSpeak field parsing, agronomic rule assessment,
settings persistence, and alert management.
"""

import sys
import os
import unittest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import app
from config import Config
import models
from thingspeak_client import thingspeak_client
from analytics import plant_analytics

class PlantCareBackendTestCase(unittest.TestCase):
    """Unit and integration test cases for PlantCare AI backend."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        # Initialize database for testing
        with self.app.app_context():
            models.init_db()

    # 1. ThingSpeak Parser Unit Tests
    def test_safe_float_parsing(self):
        """Tests that safe_float converts numbers, handles nulls, and ignores garbage."""
        self.assertEqual(thingspeak_client._safe_float("1.234"), 1.234)
        self.assertEqual(thingspeak_client._safe_float(2.5), 2.5)
        self.assertIsNone(thingspeak_client._safe_float(None))
        self.assertIsNone(thingspeak_client._safe_float(""))
        self.assertIsNone(thingspeak_client._safe_float("nan"))
        self.assertIsNone(thingspeak_client._safe_float("invalid_string"))

    def test_parse_entry_mapping(self):
        """Tests mapping ThingSpeak field1..field5 to domain sensor names."""
        raw_feed = {
            "entry_id": 42,
            "created_at": "2026-10-26T01:30:00Z",
            "field1": "2.105",  # Soil Voltage
            "field2": "1.450",  # Light Voltage
            "field3": "24.5",   # Temperature
            "field4": "1012.3", # Pressure
            "field5": "0.080"   # Water Sensor Voltage
        }
        parsed = thingspeak_client._parse_entry(raw_feed)
        self.assertEqual(parsed["entry_id"], 42)
        self.assertEqual(parsed["soil_voltage_v"], 2.105)
        self.assertEqual(parsed["light_voltage_v"], 1.450)
        self.assertEqual(parsed["temperature_c"], 24.5)
        self.assertEqual(parsed["pressure_hpa"], 1012.3)
        self.assertEqual(parsed["water_voltage_v"], 0.08)

    # 2. Agronomic Calibration & Rule Tests
    def test_relative_moisture_calculation(self):
        """Tests relative moisture calculation for standard inverted capacitive sensor."""
        # Higher voltage = drier soil (e.g., dry = 2.65V, wet = 1.20V)
        dry_v = 2.65
        wet_v = 1.20
        # If voltage is exactly wet_v, moisture should be 100%
        wet_calc = plant_analytics.calculate_relative_moisture(wet_v, dry_v, wet_v, invert=True)
        self.assertAlmostEqual(wet_calc, 100.0, places=1)

        # If voltage is exactly dry_v, moisture should be 0%
        dry_calc = plant_analytics.calculate_relative_moisture(dry_v, dry_v, wet_v, invert=True)
        self.assertAlmostEqual(dry_calc, 0.0, places=1)

        # Midpoint (~1.925V) should be ~50%
        mid_calc = plant_analytics.calculate_relative_moisture(1.925, dry_v, wet_v, invert=True)
        self.assertAlmostEqual(mid_calc, 50.0, places=1)

    def test_plant_status_normal_assessment(self):
        """Tests that optimal readings evaluate to Normal status."""
        telemetry = {
            "soil_voltage_v": 1.90,  # Mid moist
            "light_voltage_v": 1.80, # Bright indirect
            "temperature_c": 22.5,   # Ideal temp
            "pressure_hpa": 1013.25,
            "water_voltage_v": 0.05
        }
        assessment = plant_analytics.assess_plant(telemetry)
        self.assertEqual(assessment["overall_status"], "Normal")
        self.assertEqual(assessment["status_code"], "normal")
        self.assertIn("Maintain", assessment["recommendation"])

    def test_plant_status_cold_stress_assessment(self):
        """Tests that cold temperature generates a warning or critical alert."""
        telemetry = {
            "soil_voltage_v": 1.90,
            "light_voltage_v": 1.80,
            "temperature_c": 11.0,   # Way below default 18C
            "pressure_hpa": 1013.25,
            "water_voltage_v": 0.05
        }
        assessment = plant_analytics.assess_plant(telemetry)
        self.assertIn(assessment["overall_status"], ["Needs Attention", "Critical"])
        self.assertIn("temperature", assessment["diagnostics"])
        self.assertIn("Cold", assessment["diagnostics"]["temperature"]["status"])

    # 3. Settings & Alerts Database Tests
    def test_settings_persistence(self):
        """Tests reading and updating settings in SQLite."""
        orig_name = models.get_setting("plant_name")
        models.update_setting("plant_name", "Test Bonsai")
        updated = models.get_setting("plant_name")
        self.assertEqual(updated, "Test Bonsai")
        # Restore
        models.update_setting("plant_name", orig_name)

    def test_alerts_lifecycle(self):
        """Tests adding an alert and resolving it."""
        alert_id = models.add_alert(
            severity="warning",
            affected_sensor="Test Sensor",
            triggering_value=99.9,
            rule="Test Rule Triggered",
            recommendation="Perform test check"
        )
        self.assertIsNotNone(alert_id)
        
        alerts = models.get_alerts(unresolved_only=True)
        found = any(a["id"] == alert_id for a in alerts)
        self.assertTrue(found)

        # Resolve alert
        resolved = models.resolve_alert(alert_id)
        self.assertTrue(resolved)

    # 4. REST API Endpoint Tests
    def test_api_health(self):
        """Tests GET /api/health returns 200 and required fields."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data["status"], "healthy")
        self.assertIn("cloud_configured", json_data)

    def test_api_sensors_latest(self):
        """Tests GET /api/sensors/latest returns 200 and schema."""
        response = self.client.get("/api/sensors/latest")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("status", json_data)
        self.assertIn("data_source", json_data)

    def test_api_settings_get_and_put(self):
        """Tests GET and PUT on /api/settings."""
        # GET
        get_res = self.client.get("/api/settings")
        self.assertEqual(get_res.status_code, 200)
        
        # PUT
        put_res = self.client.put("/api/settings", json={
            "temp_min_c": 19.5,
            "temp_max_c": 27.5
        })
        self.assertEqual(put_res.status_code, 200)
        data = put_res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["settings"]["temp_min_c"], 19.5)

    def test_api_anomalies(self):
        """Tests GET /api/analytics/anomalies endpoint."""
        response = self.client.get("/api/analytics/anomalies")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("available", data)

    def test_api_export_csv(self):
        """Tests GET /api/export/csv returns a valid CSV attachment."""
        response = self.client.get("/api/export/csv?range=1h")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers.get("Content-Type", ""))
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
        csv_text = response.data.decode("utf-8")
        self.assertIn("entry_id,timestamp_utc", csv_text)

if __name__ == "__main__":
    unittest.main()


