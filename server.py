"""
FastAPI Server & Real-Time WebSocket Hub for AI Smart Plant Monitoring System.
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Set, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import (
    READING_INTERVAL_SECONDS,
    DB_LOG_INTERVAL_SECONDS,
    DEFAULT_MOISTURE_THRESHOLD,
    DEFAULT_PROFILE,
    PLANT_PROFILES,
    BASE_DIR
)
from sensors import SensorManager
from actuators import PumpController
from ml import PlantAI
from database.db import (
    log_reading,
    get_recent_readings,
    get_recent_watering_events,
    get_recent_alerts,
    get_setting,
    set_setting,
    log_alert
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PlantServer")

# Global instances
sensor_manager = SensorManager()
pump_controller = PumpController(sensor_manager=sensor_manager)
plant_ai = PlantAI()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

# State cache
latest_telemetry: Dict[str, Any] = {}
telemetry_lock = asyncio.Lock()

# Persistent configuration cache
auto_watering_enabled = get_setting("auto_watering_enabled", "true").lower() == "true"
moisture_threshold = float(get_setting("moisture_threshold", str(DEFAULT_MOISTURE_THRESHOLD)))
active_profile_key = get_setting("plant_profile", DEFAULT_PROFILE)

# Request Models
class WaterRequest(BaseModel):
    duration: Optional[float] = 3.5

class SettingsRequest(BaseModel):
    auto_watering_enabled: Optional[bool] = None
    moisture_threshold: Optional[float] = None
    plant_profile: Optional[str] = None

class AnomalySimRequest(BaseModel):
    anomaly_type: Optional[str] = None # 'heatwave', 'drought', 'darkness', 'sensor_failure', or None

async def broadcast_telemetry(payload: dict):
    """Sends latest telemetry to all connected WebSocket clients."""
    disconnected = set()
    msg_text = json.dumps(payload)
    for ws in active_connections:
        try:
            await ws.send_text(msg_text)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        active_connections.discard(ws)

async def background_monitoring_loop():
    """Continuous sensor polling, ML evaluation, auto-watering decision, and DB persistence."""
    global latest_telemetry
    last_db_log_time = 0.0

    logger.info("Background telemetry & AI loop started.")
    while True:
        try:
            # 1. Read all sensors
            raw_data = sensor_manager.read_all()
            
            # 2. AI & Agronomic Evaluation
            vpd = plant_ai.calculate_vpd(raw_data["temperature"], raw_data["humidity"])
            raw_data["vpd"] = vpd

            diagnostics = plant_ai.generate_diagnostics(raw_data, active_profile_key)

            # 3. Assemble complete live telemetry payload
            now_iso = asyncio.get_event_loop().time()
            payload = {
                "timestamp": now_iso,
                "soil_moisture": raw_data["soil_moisture"],
                "temperature": raw_data["temperature"],
                "humidity": raw_data["humidity"],
                "pressure": raw_data["pressure"],
                "lux": raw_data["lux"],
                "vpd": vpd,
                "health_index": diagnostics["health_index"],
                "status_title": diagnostics["status_title"],
                "urgency": diagnostics["urgency"],
                "is_anomaly": diagnostics["is_anomaly"],
                "anomaly_score": diagnostics["anomaly_score"],
                "insights": diagnostics["insights"],
                "pump_active": pump_controller.is_pumping,
                "is_simulated": raw_data["is_simulated"],
                "auto_watering_enabled": auto_watering_enabled,
                "moisture_threshold": moisture_threshold,
                "plant_profile": active_profile_key,
                "plant_profile_name": PLANT_PROFILES.get(active_profile_key, {}).get("name", "Standard")
            }

            async with telemetry_lock:
                latest_telemetry = payload

            # 4. Auto-Watering Decision Engine
            if auto_watering_enabled and not pump_controller.is_pumping:
                if raw_data["soil_moisture"] < moisture_threshold:
                    allowed, reason = pump_controller.can_water(is_manual=False)
                    if allowed:
                        logger.info(f"Auto-watering triggered: Soil moisture {raw_data['soil_moisture']}% < {moisture_threshold}%")
                        pump_controller.trigger_watering(
                            duration=3.5,
                            trigger_type="auto",
                            current_moisture=raw_data["soil_moisture"]
                        )
                    else:
                        logger.debug(f"Auto-watering withheld: {reason}")

            # 5. Database Logging
            import time
            current_time = time.time()
            if current_time - last_db_log_time >= DB_LOG_INTERVAL_SECONDS or diagnostics["is_anomaly"]:
                log_reading(
                    soil_moisture=raw_data["soil_moisture"],
                    temperature=raw_data["temperature"],
                    humidity=raw_data["humidity"],
                    pressure=raw_data["pressure"],
                    lux=raw_data["lux"],
                    vpd=vpd,
                    health_index=diagnostics["health_index"],
                    is_anomaly=1 if diagnostics["is_anomaly"] else 0,
                    anomaly_score=diagnostics["anomaly_score"]
                )
                last_db_log_time = current_time

            # 6. WebSocket Live Broadcast
            await broadcast_telemetry(payload)

        except Exception as e:
            logger.error(f"Error in background telemetry loop: {e}")
            err_payload = {
                "hardware_error": str(e),
                "is_simulated": False,
                "status_title": "Hardware Disconnected",
                "urgency": "critical",
                "insights": [f"⚠️ Real Hardware Error: {e}", "Check jumper wires, power, and I2C connection."]
            }
            async with telemetry_lock:
                latest_telemetry.update(err_payload)
            await broadcast_telemetry(err_payload)

        await asyncio.sleep(READING_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(background_monitoring_loop())
    yield
    monitor_task.cancel()
    pump_controller.cleanup()

app = FastAPI(
    title="Smart Plant AI Monitoring API",
    description="IoT and Machine Learning backend for Raspberry Pi Smart Plant System",
    version="1.0.0",
    lifespan=lifespan
)

# API Endpoints
@app.get("/api/status")
async def get_status():
    async with telemetry_lock:
        if not latest_telemetry:
            # Fallback if first read hasn't completed
            return {"status": "initializing"}
        return latest_telemetry

@app.get("/api/history")
async def get_history(limit: int = 50, hours: Optional[int] = None):
    readings = get_recent_readings(limit=limit, hours=hours)
    return {"readings": readings}

@app.get("/api/watering-history")
async def get_watering_history(limit: int = 15):
    events = get_recent_watering_events(limit=limit)
    return {"events": events}

@app.get("/api/alerts")
async def get_alerts(limit: int = 15):
    alerts = get_recent_alerts(limit=limit)
    return {"alerts": alerts}

@app.get("/api/profiles")
async def get_profiles():
    return {"profiles": PLANT_PROFILES, "active": active_profile_key}

@app.post("/api/water")
async def manual_water(req: WaterRequest):
    current_moisture = latest_telemetry.get("soil_moisture", 40.0)
    success, message = pump_controller.trigger_watering(
        duration=req.duration or 3.5,
        trigger_type="manual",
        current_moisture=current_moisture
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    global auto_watering_enabled, moisture_threshold, active_profile_key

    if req.auto_watering_enabled is not None:
        auto_watering_enabled = req.auto_watering_enabled
        set_setting("auto_watering_enabled", str(auto_watering_enabled).lower())

    if req.moisture_threshold is not None:
        moisture_threshold = max(10.0, min(90.0, req.moisture_threshold))
        set_setting("moisture_threshold", str(moisture_threshold))

    if req.plant_profile is not None and req.plant_profile in PLANT_PROFILES:
        active_profile_key = req.plant_profile
        set_setting("plant_profile", active_profile_key)

    return {
        "auto_watering_enabled": auto_watering_enabled,
        "moisture_threshold": moisture_threshold,
        "plant_profile": active_profile_key
    }

@app.post("/api/simulate-anomaly")
async def simulate_anomaly(req: AnomalySimRequest):
    """Allows testing AI anomaly detection on demand."""
    sensor_manager.set_simulation_anomaly(req.anomaly_type)
    return {"success": True, "anomaly_type": req.anomaly_type}

# WebSocket for streaming live data
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        # Immediately send cached state if available
        async with telemetry_lock:
            if latest_telemetry:
                await websocket.send_text(json.dumps(latest_telemetry))
        while True:
            # Keep connection open and receive any ping/pong
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.discard(websocket)
    except Exception:
        active_connections.discard(websocket)

# Serve Web Dashboard Static Files
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "Dashboard UI is loading..."})
