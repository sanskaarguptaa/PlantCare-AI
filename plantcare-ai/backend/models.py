"""
PlantCare AI - SQLite Database Models and Persistence Layer
Manages local SQLite storage for settings, cached cloud telemetry, and system alerts.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from config import Config

def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema if not already present."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 2. Cached Readings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_readings (
                entry_id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL,
                soil_voltage_v REAL,
                light_voltage_v REAL,
                temperature_c REAL,
                pressure_hpa REAL,
                water_voltage_v REAL,
                is_demo INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_created ON cached_readings(created_at)")
        
        # 3. Alerts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                severity TEXT NOT NULL,
                affected_sensor TEXT NOT NULL,
                triggering_value REAL,
                rule TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)")

        # Populate default settings if table is empty
        default_settings = {
            "plant_name": "Monstera Deliciosa",
            "plant_type": "Indoor Tropical Houseplant",
            "temp_min_c": "18.0",
            "temp_max_c": "28.0",
            "temp_unit": "C",
            "soil_dry_voltage": "2.65",
            "soil_wet_voltage": "1.20",
            "soil_invert": "1",  # 1 = higher voltage means drier soil (standard capacitive/resistive sensor)
            "light_threshold_voltage": "1.50",
            "water_sensor_alert_threshold": "0.80",
            "dashboard_refresh_sec": "30",
            "demo_mode": "1" if Config.DEMO_MODE else "0"
        }
        
        now = datetime.now(timezone.utc).isoformat()
        for k, v in default_settings.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (k, str(v), now)
            )
        conn.commit()

def get_all_settings() -> Dict[str, Any]:
    """Retrieves all application settings as a Python dictionary."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        
        settings = {}
        for row in rows:
            val = row["value"]
            # Convert numeric strings where appropriate
            if val.isdigit():
                val = int(val)
            else:
                try:
                    val = float(val)
                except ValueError:
                    pass
            settings[row["key"]] = val
        return settings

def get_setting(key: str, default: Any = None) -> Any:
    """Retrieves a single setting value by key."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return default
        val = row["value"]
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            return val

def update_setting(key: str, value: Any):
    """Updates or inserts a single setting."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value, updated_at) 
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, str(value), now))
        conn.commit()

def update_settings(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Batch updates multiple settings and returns the updated set."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("""
                INSERT INTO settings (key, value, updated_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (k, str(v), now))
        conn.commit()
    return get_all_settings()

def save_reading(
    entry_id: int,
    created_at: str,
    soil_v: Optional[float],
    light_v: Optional[float],
    temp_c: Optional[float],
    press_hpa: Optional[float],
    water_v: Optional[float],
    is_demo: int = 0
):
    """Caches a sensor reading from ThingSpeak or demo simulator."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cached_readings 
            (entry_id, created_at, soil_voltage_v, light_voltage_v, temperature_c, pressure_hpa, water_voltage_v, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, created_at, soil_v, light_v, temp_c, press_hpa, water_v, is_demo))
        conn.commit()

def save_readings_batch(readings: List[Dict[str, Any]], is_demo: int = 0):
    """Batch saves multiple readings."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for r in readings:
            cursor.execute("""
                INSERT OR REPLACE INTO cached_readings 
                (entry_id, created_at, soil_voltage_v, light_voltage_v, temperature_c, pressure_hpa, water_voltage_v, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("entry_id"),
                r.get("created_at"),
                r.get("soil_voltage_v"),
                r.get("light_voltage_v"),
                r.get("temperature_c"),
                r.get("pressure_hpa"),
                r.get("water_voltage_v"),
                is_demo
            ))
        conn.commit()

def get_latest_cached_reading() -> Optional[Dict[str, Any]]:
    """Retrieves the most recent cached reading."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM cached_readings 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

def get_cached_readings(limit: int = 100, hours: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves cached readings with limit and optional hours filter."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if hours:
            cursor.execute("""
                SELECT * FROM cached_readings 
                WHERE datetime(created_at) >= datetime('now', ?)
                ORDER BY created_at ASC
            """, (f"-{hours} hours",))
        else:
            cursor.execute("""
                SELECT * FROM (
                    SELECT * FROM cached_readings 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ) ORDER BY created_at ASC
            """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def add_alert(
    severity: str,
    affected_sensor: str,
    triggering_value: Optional[float],
    rule: str,
    recommendation: str
) -> int:
    """Records a new alert if a similar unresolved alert does not already exist recently."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Avoid spamming duplicate unresolved alerts for the same sensor within 15 mins
        cursor.execute("""
            SELECT id FROM alerts 
            WHERE affected_sensor = ? AND resolved = 0 AND rule = ?
            AND datetime(created_at) >= datetime('now', '-15 minutes')
            LIMIT 1
        """, (affected_sensor, rule))
        existing = cursor.fetchone()
        if existing:
            return existing["id"]
        
        cursor.execute("""
            INSERT INTO alerts (severity, affected_sensor, triggering_value, rule, recommendation, created_at, resolved)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (severity, affected_sensor, triggering_value, rule, recommendation, now))
        conn.commit()
        return cursor.lastrowid

def get_alerts(limit: int = 50, unresolved_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieves recent alerts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if unresolved_only:
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE resolved = 0 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT * FROM alerts 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def resolve_alert(alert_id: int) -> bool:
    """Marks an alert as resolved."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        return cursor.rowcount > 0
