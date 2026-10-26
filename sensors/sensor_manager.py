"""
Unified Sensor Manager with intelligent hardware auto-detection & realistic simulation mode.
Allows testing the entire AI pipeline, web dashboard, and automation on any PC without physical hardware,
and seamlessly interfaces with physical I2C sensors when run on a Raspberry Pi.
"""
import time
import math
import random
import logging
from typing import Dict, Any, Optional

from config import FORCE_SIMULATION, STRICT_HARDWARE_MODE
from sensors.ads1115_reader import ADS1115Reader
from sensors.bme280_reader import BME280Reader
from sensors.bh1750_reader import BH1750Reader

logger = logging.getLogger("SensorManager")

class SensorManager:
    def __init__(self):
        self.is_simulated = False if STRICT_HARDWARE_MODE else True
        self.ads_reader: Optional[ADS1115Reader] = None
        self.bme_reader: Optional[BME280Reader] = None
        self.bh_reader: Optional[BH1750Reader] = None
        self.hardware_errors = []

        # Simulation state (used only if STRICT_HARDWARE_MODE is False)
        self._sim_moisture = 48.0
        self._sim_temp = 23.5
        self._sim_humidity = 58.0
        self._sim_pressure = 1013.25
        self._sim_lux = 1850.0
        self._sim_anomaly_override = None
        self._last_sim_tick = time.time()

        if not FORCE_SIMULATION:
            self._init_hardware()

    def _init_hardware(self):
        self.hardware_errors.clear()
        
        # 1. ADS1115 (Soil Moisture)
        try:
            self.ads_reader = ADS1115Reader()
            if not self.ads_reader.is_connected:
                self.hardware_errors.append("ADS1115 (0x48) not detected! Verify SDA (Pin 3), SCL (Pin 5), 3.3V (Pin 1), GND (Pin 6).")
        except Exception as e:
            self.hardware_errors.append(f"ADS1115 init error: {e}")

        # 2. BME280 (Temperature, Humidity, Pressure)
        try:
            self.bme_reader = BME280Reader()
            if not self.bme_reader.is_connected:
                self.hardware_errors.append("BME280 (0x76/0x77) not detected! Verify SDA, SCL, 3.3V, GND.")
        except Exception as e:
            self.hardware_errors.append(f"BME280 init error: {e}")

        # 3. BH1750 (Light Sensor)
        try:
            self.bh_reader = BH1750Reader()
            if not self.bh_reader.is_connected:
                self.hardware_errors.append("BH1750 (0x23) not detected! Verify SDA, SCL, 3.3V, GND, ADDR to GND.")
        except Exception as e:
            self.hardware_errors.append(f"BH1750 init error: {e}")

        if not self.hardware_errors:
            self.is_simulated = False
            logger.info(">>> SUCCESS: All physical sensors (ADS1115, BME280, BH1750) verified on real I2C bus! <<<")
        else:
            if STRICT_HARDWARE_MODE:
                self.is_simulated = False
                for err in self.hardware_errors:
                    logger.error(f"[HARDWARE ERROR] {err}")
            else:
                self.is_simulated = True
                logger.warning("One or more physical sensors missing. Running simulator because STRICT_HARDWARE_MODE=False.")

    def read_all(self) -> Dict[str, Any]:
        """
        Reads from physical sensors if available; otherwise returns realistic simulated data.
        Returns:
            {
                'soil_moisture': float,
                'temperature': float,
                'humidity': float,
                'pressure': float,
                'lux': float,
                'is_simulated': bool
            }
        """
        if not self.is_simulated:
            try:
                if not self.ads_reader or not self.ads_reader.is_connected:
                    raise RuntimeError("ADS1115 ADC is not responding! Check I2C address 0x48 and Pin 3 (SDA), Pin 5 (SCL).")
                if not self.bme_reader or not self.bme_reader.is_connected:
                    raise RuntimeError("BME280 sensor is not responding! Check I2C address 0x76/0x77 and wiring.")
                if not self.bh_reader or not self.bh_reader.is_connected:
                    raise RuntimeError("BH1750 light sensor is not responding! Check I2C address 0x23 and wiring.")

                moisture = self.ads_reader.read_moisture_percentage()
                env = self.bme_reader.read()
                lux = self.bh_reader.read_lux()
                return {
                    "soil_moisture": moisture,
                    "temperature": env["temperature"],
                    "humidity": env["humidity"],
                    "pressure": env["pressure"],
                    "lux": lux,
                    "is_simulated": False
                }
            except Exception as e:
                if STRICT_HARDWARE_MODE:
                    logger.error(f"STRICT HARDWARE READ FAILURE: {e}")
                    raise RuntimeError(f"Real Hardware Failure: {e}")
                logger.warning(f"Error reading hardware sensors ({e}). Temporarily using simulator.")

        return self._generate_simulated_readings()

    def notify_watering(self, amount_percent: float = 28.0):
        """Called by PumpController to instantly reflect watering in simulation mode."""
        if self.is_simulated:
            self._sim_moisture = min(92.0, self._sim_moisture + amount_percent)
            logger.info(f"[SIMULATOR] Plant watered! Simulated soil moisture boosted to {self._sim_moisture:.1f}%")

    def set_simulation_anomaly(self, anomaly_type: Optional[str]):
        """Inject synthetic anomaly for testing ML detection ('heatwave', 'drought', 'darkness', or None)."""
        self._sim_anomaly_override = anomaly_type
        logger.info(f"[SIMULATOR] Set anomaly override to: {anomaly_type}")

    def _generate_simulated_readings(self) -> Dict[str, Any]:
        """Generates realistic diurnal changes and continuous soil drying."""
        now = time.time()
        dt = max(1.0, min(10.0, now - self._last_sim_tick))
        self._last_sim_tick = now

        # Natural continuous soil moisture evaporation (~0.05% - 0.15% per minute depending on temp)
        evaporation_rate = (0.04 + (self._sim_temp - 20.0) * 0.01) * (dt / 60.0)
        self._sim_moisture = max(8.0, self._sim_moisture - evaporation_rate)

        # Diurnal solar cycle simulation (sinusoidal pattern based on current minute)
        # Completes a cycle every 300 seconds for quick visual demo, or uses real time
        cycle_progress = (now % 300) / 300.0  # 0 to 1 over 5 minutes
        sun_factor = max(0.0, math.sin(cycle_progress * 2 * math.pi))

        base_lux = 20.0 + sun_factor * 3500.0 + random.uniform(-30, 30)
        base_temp = 21.0 + sun_factor * 6.0 + random.uniform(-0.15, 0.15)
        base_humidity = 65.0 - sun_factor * 20.0 + random.uniform(-0.5, 0.5)

        # Apply synthetic test anomalies if requested
        if self._sim_anomaly_override == "heatwave":
            base_temp += 14.0       # e.g., 38°C
            base_humidity -= 25.0   # low humidity
            self._sim_moisture = max(5.0, self._sim_moisture - 0.3)
        elif self._sim_anomaly_override == "drought":
            self._sim_moisture = 11.5
        elif self._sim_anomaly_override == "darkness":
            base_lux = 0.5
        elif self._sim_anomaly_override == "sensor_failure":
            base_temp = -99.0

        self._sim_temp = round(base_temp, 2)
        self._sim_humidity = round(max(10.0, min(99.0, base_humidity)), 2)
        self._sim_lux = round(max(0.0, base_lux), 1)

        return {
            "soil_moisture": round(self._sim_moisture, 1),
            "temperature": self._sim_temp,
            "humidity": self._sim_humidity,
            "pressure": round(self._sim_pressure + random.uniform(-0.2, 0.2), 2),
            "lux": self._sim_lux,
            "is_simulated": True
        }
