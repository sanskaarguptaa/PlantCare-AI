"""
SQLite Database manager for telemetry, watering events, and AI alerts.
"""
import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Sensor Readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                soil_moisture REAL NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                pressure REAL NOT NULL,
                lux REAL NOT NULL,
                vpd REAL,
                health_index REAL,
                is_anomaly INTEGER DEFAULT 0,
                anomaly_score REAL DEFAULT 0.0
            )
        """)
        
        # Watering History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watering_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration_seconds REAL NOT NULL,
                trigger_type TEXT NOT NULL, -- 'auto' or 'manual'
                moisture_before REAL,
                moisture_after REAL
            )
        """)
        
        # AI Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                severity TEXT NOT NULL, -- 'info', 'warning', 'critical'
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0
            )
        """)
        
        # Key-Value Settings table (for persistent user thresholds & preset)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        conn.commit()

def log_reading(
    soil_moisture: float,
    temperature: float,
    humidity: float,
    pressure: float,
    lux: float,
    vpd: float,
    health_index: float,
    is_anomaly: int = 0,
    anomaly_score: float = 0.0
) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_readings (
                soil_moisture, temperature, humidity, pressure, lux, vpd, health_index, is_anomaly, anomaly_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            round(soil_moisture, 2),
            round(temperature, 2),
            round(humidity, 2),
            round(pressure, 2),
            round(lux, 2),
            round(vpd, 3),
            round(health_index, 1),
            is_anomaly,
            round(anomaly_score, 3)
        ))
        conn.commit()
        return cursor.lastrowid

def log_watering(duration_seconds: float, trigger_type: str, moisture_before: float, moisture_after: Optional[float] = None) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO watering_logs (duration_seconds, trigger_type, moisture_before, moisture_after)
            VALUES (?, ?, ?, ?)
        """, (duration_seconds, trigger_type, moisture_before, moisture_after))
        conn.commit()
        return cursor.lastrowid

def log_alert(severity: str, title: str, message: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_alerts (severity, title, message)
            VALUES (?, ?, ?)
        """, (severity, title, message))
        conn.commit()
        return cursor.lastrowid

def get_recent_readings(limit: int = 60, hours: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if hours:
            cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT * FROM sensor_readings 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            """, (cutoff,))
        else:
            cursor.execute("""
                SELECT * FROM (
                    SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

def get_recent_watering_events(limit: int = 10) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watering_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_recent_alerts(limit: int = 10) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_alerts ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()

# Initialize tables when imported
init_db()
