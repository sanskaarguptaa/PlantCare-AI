"""
PlantCare AI - Central Configuration
Loads environment variables and provides validated settings for the backend.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root directory (one level up from backend)
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env file from project root first, then backend dir if present
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv(BACKEND_DIR / ".env")


class Config:
    """Backend application configuration."""

    BACKEND_DIR = BACKEND_DIR
    PROJECT_ROOT = PROJECT_ROOT

    # Server settings
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t", "yes")

    # ThingSpeak Cloud Settings
    THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "").strip()
    THINGSPEAK_READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY", "").strip()
    THINGSPEAK_WRITE_API_KEY = os.getenv("THINGSPEAK_WRITE_API_KEY", "").strip()

    # Rate limiting & caching
    # ThingSpeak free tier requires >=15s between channel updates. Backend caches queries for at least 20s.
    CACHE_TTL_SECONDS = int(os.getenv("THINGSPEAK_CACHE_TTL_SECONDS", 20))
    REQUEST_TIMEOUT_SECONDS = 8

    # Demo / Simulation Mode
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "t", "yes")

    # Paths
    DATABASE_PATH = BACKEND_DIR / "plantcare.db"
    MODEL_PATH = PROJECT_ROOT / "ml" / "anomaly_model.pkl"
    MODEL_METADATA_PATH = PROJECT_ROOT / "ml" / "model_metadata.json"
    SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "plant_data_sample.csv"

    # CORS configuration
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

    @classmethod
    def is_cloud_configured(cls) -> bool:
        """Checks whether valid-looking ThingSpeak Channel ID is configured."""
        return bool(
            cls.THINGSPEAK_CHANNEL_ID
            and cls.THINGSPEAK_CHANNEL_ID != "YOUR_CHANNEL_ID_HERE"
        )

    @classmethod
    def get_safe_info(cls) -> dict:
        """Returns non-sensitive configuration summary for status endpoints."""
        channel_id = cls.THINGSPEAK_CHANNEL_ID
        has_read_key = bool(
            cls.THINGSPEAK_READ_API_KEY
            and cls.THINGSPEAK_READ_API_KEY != "YOUR_READ_API_KEY_HERE"
        )
        return {
            "channel_id_configured": bool(channel_id and channel_id != "YOUR_CHANNEL_ID_HERE"),
            "channel_id": channel_id if channel_id != "YOUR_CHANNEL_ID_HERE" else None,
            "has_read_key": has_read_key,
            "cache_ttl_seconds": cls.CACHE_TTL_SECONDS,
            "demo_mode": cls.DEMO_MODE,
            "database_exists": cls.DATABASE_PATH.exists(),
            "ml_model_exists": cls.MODEL_PATH.exists(),
        }
