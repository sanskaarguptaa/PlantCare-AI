"""
Actuator Module: Safe Water Pump & Relay Controller.
Includes cooldown locks, max run safety timer, and daily watering limits.
"""
import time
import threading
import logging
from typing import Optional, Tuple
from config import (
    PUMP_GPIO_PIN,
    PUMP_ACTIVE_LOW,
    WATERING_DURATION_SECONDS,
    PUMP_COOLDOWN_MINUTES,
    MAX_DAILY_WATERING_CYCLES,
    FORCE_SIMULATION
)
from database.db import log_watering, log_alert

logger = logging.getLogger("PumpController")

class PumpController:
    def __init__(self, sensor_manager=None):
        self.pin = PUMP_GPIO_PIN
        self.active_low = PUMP_ACTIVE_LOW
        self.sensor_manager = sensor_manager
        
        self.is_hardware_available = False
        self.is_pumping = False
        self.last_watered_time: float = 0.0
        self.daily_cycle_count = 0
        self.last_day_reset = time.strftime("%Y-%m-%d")
        self._lock = threading.Lock()

        if not FORCE_SIMULATION:
            self._init_gpio()

    def _init_gpio(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            initial_state = GPIO.HIGH if self.active_low else GPIO.LOW
            GPIO.setup(self.pin, GPIO.OUT, initial=initial_state)
            self.is_hardware_available = True
            logger.info(f"Relay GPIO pin {self.pin} initialized.")
        except Exception as e:
            self.is_hardware_available = False
            logger.info(f"RPi.GPIO not accessible ({e}). Running pump in simulated mode.")

    def _set_pump_state(self, on: bool):
        if self.is_hardware_available:
            try:
                import RPi.GPIO as GPIO
                if self.active_low:
                    GPIO.output(self.pin, GPIO.LOW if on else GPIO.HIGH)
                else:
                    GPIO.output(self.pin, GPIO.HIGH if on else GPIO.LOW)
            except Exception as e:
                logger.error(f"GPIO error toggling pump: {e}")
        else:
            state_str = "ON" if on else "OFF"
            logger.info(f"[SIMULATED PUMP] Relay switched {state_str}")

    def _check_daily_reset(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.last_day_reset:
            self.daily_cycle_count = 0
            self.last_day_reset = today

    def can_water(self, is_manual: bool = False) -> Tuple[bool, str]:
        """Validates if watering is permitted based on safety rules."""
        if self.is_pumping:
            return False, "Pump is currently running."

        self._check_daily_reset()

        if self.daily_cycle_count >= MAX_DAILY_WATERING_CYCLES:
            return False, f"Daily limit reached ({MAX_DAILY_WATERING_CYCLES} cycles max). Check reservoir & soil."

        now = time.time()
        elapsed = now - self.last_watered_time

        # For auto watering, enforce full cooldown (e.g., 20 mins)
        # For manual watering, allow shorter cooldown (15 seconds safety)
        cooldown_needed = 15 if is_manual else (PUMP_COOLDOWN_MINUTES * 60)
        if elapsed < cooldown_needed:
            remaining = int(cooldown_needed - elapsed)
            return False, f"Safety cooldown active. Wait {remaining}s."

        return True, "Ready"

    def trigger_watering(self, duration: float = WATERING_DURATION_SECONDS, trigger_type: str = "auto", current_moisture: Optional[float] = None) -> Tuple[bool, str]:
        """Triggers the pump asynchronously for safety and logs the event."""
        with self._lock:
            allowed, reason = self.can_water(is_manual=(trigger_type == "manual"))
            if not allowed:
                logger.warning(f"Watering rejected: {reason}")
                return False, reason

            # Cap duration to prevent flooding
            safe_duration = max(1.0, min(12.0, duration))

            thread = threading.Thread(
                target=self._run_pump_worker,
                args=(safe_duration, trigger_type, current_moisture),
                daemon=True
            )
            thread.start()
            return True, f"Watering started for {safe_duration}s ({trigger_type})"

    def _run_pump_worker(self, duration: float, trigger_type: str, moisture_before: Optional[float]):
        try:
            self.is_pumping = True
            logger.info(f"Activating water pump for {duration} seconds [{trigger_type}]...")
            self._set_pump_state(True)

            time.sleep(duration)

        finally:
            self._set_pump_state(False)
            self.is_pumping = False
            self.last_watered_time = time.time()
            self.daily_cycle_count += 1
            logger.info("Water pump deactivated.")

            # Notify simulation if active
            if self.sensor_manager:
                self.sensor_manager.notify_watering(amount_percent=25.0)

            # Log to DB
            log_watering(
                duration_seconds=duration,
                trigger_type=trigger_type,
                moisture_before=moisture_before,
                moisture_after=None
            )
            log_alert(
                severity="info",
                title=f"Watering Completed ({trigger_type.capitalize()})",
                message=f"Dispensed water for {duration}s. Next cycle locked for {PUMP_COOLDOWN_MINUTES}m."
            )

    def cleanup(self):
        """Safe cleanup on shutdown."""
        self._set_pump_state(False)
        if self.is_hardware_available:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup(self.pin)
            except Exception:
                pass
