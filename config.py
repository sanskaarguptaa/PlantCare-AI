"""
Central Configuration for AI Smart Plant Monitoring and Automatic Watering System.
Easily customize thresholds, GPIO pins, I2C addresses, and plant presets.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "plant_monitor.db"
MODEL_PATH = BASE_DIR / "ml" / "anomaly_model.pkl"

# Operational Mode
# Set STRICT_HARDWARE_MODE = True to disable simulator entirely.
# The system will strictly read real I2C/GPIO hardware and will report an error if any wire is loose.
STRICT_HARDWARE_MODE = True
FORCE_SIMULATION = False

# GPIO Pin Mapping (Raspberry Pi BCM numbering)
# Physical Pin 11 = BCM GPIO 17
PUMP_GPIO_PIN = 17
PUMP_ACTIVE_LOW = True  # Most relay modules trigger on LOW (0V) signal. Set False if active HIGH.

# I2C Addresses
I2C_BUS = 1
ADS1115_I2C_ADDR = 0x48   # Default ADS1115 address
BME280_I2C_ADDR = 0x76    # Default BME280 address (sometimes 0x77)
BH1750_I2C_ADDR = 0x23    # Default BH1750 address (sometimes 0x5C)

# Capacitive Soil Moisture Sensor Calibration (ADS1115 Raw ADC values / Voltage)
# Calibrate these by testing your sensor in dry air vs a glass of water:
# In dry air: raw voltage is high (~2.8V - 3.0V, or ~22000 ADC count)
# Submerged in water: raw voltage is low (~1.2V - 1.4V, or ~10000 ADC count)
SOIL_DRY_ADC = 22500      # 0% moisture baseline
SOIL_WET_ADC = 11000      # 100% moisture baseline
SOIL_ADC_CHANNEL = 0      # A0 on ADS1115

# Watering Safety Constraints (Prevents pump burnout & flooding)
DEFAULT_MOISTURE_THRESHOLD = 35.0   # Trigger auto-watering if moisture drops below this %
WATERING_DURATION_SECONDS = 3.5     # Run pump for 3.5 seconds per watering cycle
PUMP_COOLDOWN_MINUTES = 20          # Wait at least 20 minutes before watering again (allows water to soak)
MAX_DAILY_WATERING_CYCLES = 5       # Emergency limit per 24 hours

# Telemetry & Sampling
READING_INTERVAL_SECONDS = 3        # Read sensors every 3 seconds for live dashboard
DB_LOG_INTERVAL_SECONDS = 60        # Persist a permanent history record every 60 seconds

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# Plant Profiles (Optimal targets for different plant families)
PLANT_PROFILES = {
    "houseplant": {
        "name": "General Houseplant (e.g. Pothos, Monstera)",
        "min_moisture": 35.0,
        "max_moisture": 75.0,
        "min_temp": 18.0,
        "max_temp": 28.0,
        "min_humidity": 45.0,
        "max_humidity": 70.0,
        "min_lux": 800,
        "max_lux": 10000,
        "optimal_vpd_min": 0.6,
        "optimal_vpd_max": 1.2
    },
    "succulent": {
        "name": "Succulent & Cactus",
        "min_moisture": 15.0,
        "max_moisture": 45.0,
        "min_temp": 16.0,
        "max_temp": 32.0,
        "min_humidity": 30.0,
        "max_humidity": 55.0,
        "min_lux": 2500,
        "max_lux": 30000,
        "optimal_vpd_min": 0.8,
        "optimal_vpd_max": 1.5
    },
    "herb": {
        "name": "Culinary Herb (e.g. Basil, Mint)",
        "min_moisture": 45.0,
        "max_moisture": 80.0,
        "min_temp": 19.0,
        "max_temp": 27.0,
        "min_humidity": 50.0,
        "max_humidity": 75.0,
        "min_lux": 2000,
        "max_lux": 25000,
        "optimal_vpd_min": 0.5,
        "optimal_vpd_max": 1.1
    }
}
DEFAULT_PROFILE = "houseplant"
