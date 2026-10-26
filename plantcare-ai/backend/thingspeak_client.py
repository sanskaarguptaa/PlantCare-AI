"""
PlantCare AI - ThingSpeak Cloud REST API Client
Retrieves live sensor telemetry and historical feeds from ThingSpeak Cloud with caching,
robust parsing, rate-limit awareness, and explicit data-source tracking.
"""

import time
import math
import random
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from config import Config
import models

class ThingSpeakClient:
    """Client for retrieving channel feeds from ThingSpeak Cloud."""

    BASE_URL = "https://api.thingspeak.com"

    def __init__(self):
        self._last_fetch_time: float = 0.0
        self._cached_latest: Optional[Dict[str, Any]] = None
        self._last_error: Optional[str] = None
        self._last_status_code: Optional[int] = None
        self._consecutive_failures: int = 0

    def _safe_float(self, val: Any) -> Optional[float]:
        """Safely parses a value to float; returns None if empty, invalid, or null."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("null", "none", "nan", ""):
            return None
        try:
            return round(float(val_str), 3)
        except ValueError:
            return None

    def _parse_entry(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """Maps ThingSpeak fields to domain sensor names."""
        return {
            "entry_id": feed.get("entry_id"),
            "created_at": feed.get("created_at"),
            "soil_voltage_v": self._safe_float(feed.get("field1")),
            "light_voltage_v": self._safe_float(feed.get("field2")),
            "temperature_c": self._safe_float(feed.get("field3")),
            "pressure_hpa": self._safe_float(feed.get("field4")),
            "water_voltage_v": self._safe_float(feed.get("field5")),
        }

    def _calculate_freshness(self, created_at_iso: Optional[str]) -> Tuple[Optional[float], bool]:
        """
        Calculates elapsed seconds since reading timestamp and determines staleness.
        Telemetry is considered stale if older than 120 seconds.
        """
        if not created_at_iso:
            return None, True
        try:
            # Handle ISO timestamp formats like 2026-10-26T01:30:00Z
            clean_ts = created_at_iso.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            now_utc = datetime.now(timezone.utc)
            seconds_ago = max(0.0, (now_utc - dt).total_seconds())
            is_stale = seconds_ago > 120.0
            return round(seconds_ago, 1), is_stale
        except Exception:
            return None, True

    def get_latest(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves the latest telemetry entry.
        Checks in-memory cache to respect ThingSpeak API limits.
        """
        now = time.time()
        
        # Check if Demo Mode is explicitly enabled in settings or config
        demo_setting = models.get_setting("demo_mode")
        is_demo_mode = (demo_setting == 1 or demo_setting == "1" or Config.DEMO_MODE)
        
        # If Demo mode is explicitly active, produce simulated telemetry
        if is_demo_mode:
            return self._generate_demo_latest()

        # If cloud credentials are not configured, return clear unconfigured state
        if not Config.is_cloud_configured():
            return {
                "status": "unconfigured",
                "message": "ThingSpeak Channel ID is not configured. Add your credentials to .env or enable Demo Mode in Settings.",
                "data_source": "none",
                "data": None,
                "freshness": {"seconds_ago": None, "is_stale": True},
                "cached": False
            }

        # Check Cache TTL
        if not force_refresh and self._cached_latest and (now - self._last_fetch_time < Config.CACHE_TTL_SECONDS):
            cached_data = dict(self._cached_latest)
            seconds_ago, is_stale = self._calculate_freshness(cached_data.get("created_at"))
            return {
                "status": "success",
                "data_source": "cached",
                "data": cached_data,
                "freshness": {"seconds_ago": seconds_ago, "is_stale": is_stale},
                "cached": True,
                "cache_age_seconds": round(now - self._last_fetch_time, 1)
            }

        # Fetch from ThingSpeak REST API
        url = f"{self.BASE_URL}/channels/{Config.THINGSPEAK_CHANNEL_ID}/feeds/last.json"
        params = {}
        if Config.THINGSPEAK_READ_API_KEY and Config.THINGSPEAK_READ_API_KEY != "YOUR_READ_API_KEY_HERE":
            params["api_key"] = Config.THINGSPEAK_READ_API_KEY

        try:
            resp = requests.get(url, params=params, timeout=Config.REQUEST_TIMEOUT_SECONDS)
            self._last_status_code = resp.status_code

            if resp.status_code == 200:
                feed = resp.json()
                if not feed or feed == -1 or not feed.get("created_at"):
                    # Empty channel or rate limit response
                    self._last_error = "ThingSpeak returned empty or rate-limited response"
                    return self._fallback_to_last_cached("Channel has no entries yet or is rate-limited.")

                parsed = self._parse_entry(feed)
                self._cached_latest = parsed
                self._last_fetch_time = now
                self._last_error = None
                self._consecutive_failures = 0

                # Cache in local SQLite database for persistence & offline analysis
                models.save_reading(
                    entry_id=parsed["entry_id"] or int(now),
                    created_at=parsed["created_at"],
                    soil_v=parsed["soil_voltage_v"],
                    light_v=parsed["light_voltage_v"],
                    temp_c=parsed["temperature_c"],
                    press_hpa=parsed["pressure_hpa"],
                    water_v=parsed["water_voltage_v"],
                    is_demo=0
                )

                seconds_ago, is_stale = self._calculate_freshness(parsed["created_at"])
                return {
                    "status": "success",
                    "data_source": "cloud",
                    "data": parsed,
                    "freshness": {"seconds_ago": seconds_ago, "is_stale": is_stale},
                    "cached": False
                }

            elif resp.status_code == 404:
                self._last_error = f"Channel ID '{Config.THINGSPEAK_CHANNEL_ID}' not found on ThingSpeak."
            elif resp.status_code == 400 or resp.status_code == 403:
                self._last_error = "Access denied by ThingSpeak. Please verify your Read API Key in .env."
            else:
                self._last_error = f"ThingSpeak returned HTTP {resp.status_code}."

        except requests.exceptions.Timeout:
            self._last_error = "Connection to ThingSpeak timed out (network latency or cloud delay)."
        except requests.exceptions.ConnectionError:
            self._last_error = "Network error: Unable to reach api.thingspeak.com. Check internet connectivity."
        except Exception as e:
            self._last_error = f"Unexpected cloud error: {str(e)}"

        self._consecutive_failures += 1
        return self._fallback_to_last_cached(self._last_error)

    def _fallback_to_last_cached(self, error_message: str) -> Dict[str, Any]:
        """Provides last persisted reading from SQLite if cloud request fails, without hiding error."""
        last_db = models.get_latest_cached_reading()
        if last_db:
            seconds_ago, is_stale = self._calculate_freshness(last_db.get("created_at"))
            return {
                "status": "warning",
                "message": error_message,
                "data_source": "cached",
                "data": last_db,
                "freshness": {"seconds_ago": seconds_ago, "is_stale": True},
                "cached": True,
                "cloud_error": error_message
            }

        return {
            "status": "error",
            "message": error_message,
            "data_source": "none",
            "data": None,
            "freshness": {"seconds_ago": None, "is_stale": True},
            "cached": False,
            "cloud_error": error_message
        }

    def get_history(self, hours: Optional[int] = 24, limit: int = 100) -> Dict[str, Any]:
        """
        Retrieves historical telemetry.
        First tries ThingSpeak channel feeds API; if offline or empty, retrieves from local SQLite cache.
        """
        demo_setting = models.get_setting("demo_mode")
        is_demo_mode = (demo_setting == 1 or demo_setting == "1" or Config.DEMO_MODE)
        
        if is_demo_mode:
            return self._generate_demo_history(hours=hours or 24, count=limit)

        if not Config.is_cloud_configured():
            # Return cached or empty
            cached = models.get_cached_readings(limit=limit, hours=hours)
            return {
                "status": "unconfigured" if not cached else "success",
                "data_source": "cached" if cached else "none",
                "count": len(cached),
                "readings": cached
            }

        url = f"{self.BASE_URL}/channels/{Config.THINGSPEAK_CHANNEL_ID}/feeds.json"
        params = {"results": min(limit, 800)}
        if hours:
            params["minutes"] = hours * 60
        if Config.THINGSPEAK_READ_API_KEY and Config.THINGSPEAK_READ_API_KEY != "YOUR_READ_API_KEY_HERE":
            params["api_key"] = Config.THINGSPEAK_READ_API_KEY

        try:
            resp = requests.get(url, params=params, timeout=Config.REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                data = resp.json()
                raw_feeds = data.get("feeds", [])
                parsed_readings = [self._parse_entry(f) for f in raw_feeds]

                # Cache in SQLite
                if parsed_readings:
                    models.save_readings_batch(parsed_readings, is_demo=0)

                return {
                    "status": "success",
                    "data_source": "cloud",
                    "channel_name": data.get("channel", {}).get("name", "PlantCare"),
                    "count": len(parsed_readings),
                    "readings": parsed_readings
                }
        except Exception as e:
            # Fall back to local SQLite cache
            pass

        cached = models.get_cached_readings(limit=limit, hours=hours)
        return {
            "status": "warning" if cached else "error",
            "message": "Serving cached historical data due to cloud access issue.",
            "data_source": "cached" if cached else "none",
            "count": len(cached),
            "readings": cached
        }

    def _generate_demo_latest(self) -> Dict[str, Any]:
        """Generates realistic demo telemetry for offline preview and testing."""
        now = datetime.now(timezone.utc)
        hour = now.hour + now.minute / 60.0
        sun_factor = max(0.0, math.sin((hour - 6) / 18.0 * math.pi))
        
        soil_v = round(1.85 + 0.15 * math.sin(now.minute / 10.0) + random.uniform(-0.02, 0.02), 3)
        light_v = round(0.15 + 2.4 * sun_factor + random.uniform(-0.03, 0.03), 3)
        light_v = max(0.05, min(3.2, light_v))
        temp_c = round(22.0 + 4.5 * sun_factor + random.uniform(-0.2, 0.2), 2)
        press_hpa = round(1012.8 + 1.2 * math.cos(now.minute / 20.0), 2)
        water_v = round(0.05 + random.uniform(0.0, 0.02), 3)

        reading = {
            "entry_id": int(now.timestamp()),
            "created_at": now.isoformat(),
            "soil_voltage_v": soil_v,
            "light_voltage_v": light_v,
            "temperature_c": temp_c,
            "pressure_hpa": press_hpa,
            "water_voltage_v": water_v,
        }
        
        # Save to DB tagged as demo
        models.save_reading(
            entry_id=reading["entry_id"],
            created_at=reading["created_at"],
            soil_v=soil_v,
            light_v=light_v,
            temp_c=temp_c,
            press_hpa=press_hpa,
            water_v=water_v,
            is_demo=1
        )

        return {
            "status": "success",
            "data_source": "demo",
            "data": reading,
            "freshness": {"seconds_ago": 1.0, "is_stale": False},
            "cached": False,
            "demo_notice": "DEMO / SIMULATION MODE: Values are synthesized for interface testing."
        }

    def _generate_demo_history(self, hours: int = 24, count: int = 60) -> Dict[str, Any]:
        """Generates smooth historical sequence for demo preview."""
        now = datetime.now(timezone.utc)
        readings = []
        step_minutes = max(1, int((hours * 60) / max(count, 1)))

        for i in range(count):
            t = now - timedelta(minutes=(count - 1 - i) * step_minutes)
            hour = t.hour + t.minute / 60.0
            sun_factor = max(0.0, math.sin((hour - 6) / 18.0 * math.pi))
            
            soil_v = round(1.50 + (i / float(count)) * 0.70 + random.uniform(-0.02, 0.02), 3)
            light_v = round(0.12 + 2.5 * sun_factor + random.uniform(-0.04, 0.04), 3)
            light_v = max(0.05, min(3.2, light_v))
            temp_c = round(21.0 + 5.0 * sun_factor + random.uniform(-0.3, 0.3), 2)
            press_hpa = round(1013.2 + 2.0 * math.sin(i / 10.0), 2)
            water_v = round(0.04 + random.uniform(0.0, 0.02), 3)

            readings.append({
                "entry_id": int(t.timestamp()),
                "created_at": t.isoformat(),
                "soil_voltage_v": soil_v,
                "light_voltage_v": light_v,
                "temperature_c": temp_c,
                "pressure_hpa": press_hpa,
                "water_voltage_v": water_v,
            })

        return {
            "status": "success",
            "data_source": "demo",
            "channel_name": "PlantCare Demo Channel",
            "count": len(readings),
            "readings": readings,
            "demo_notice": "DEMO / SIMULATION MODE: Historical trends are synthesized."
        }

    def get_connection_status(self) -> Dict[str, Any]:
        """Returns non-sensitive cloud connection health summary."""
        demo_setting = models.get_setting("demo_mode")
        is_demo_mode = (demo_setting == 1 or demo_setting == "1" or Config.DEMO_MODE)
        
        return {
            "configured": Config.is_cloud_configured(),
            "channel_id": Config.THINGSPEAK_CHANNEL_ID if Config.is_cloud_configured() else None,
            "has_read_key": bool(Config.THINGSPEAK_READ_API_KEY and Config.THINGSPEAK_READ_API_KEY != "YOUR_READ_API_KEY_HERE"),
            "demo_mode": is_demo_mode,
            "last_status_code": self._last_status_code,
            "last_error": self._last_error,
            "last_fetch_timestamp": datetime.fromtimestamp(self._last_fetch_time, timezone.utc).isoformat() if self._last_fetch_time > 0 else None,
            "consecutive_failures": self._consecutive_failures,
            "cache_ttl_seconds": Config.CACHE_TTL_SECONDS
        }

# Global singleton client instance
thingspeak_client = ThingSpeakClient()
