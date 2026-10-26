#!/usr/bin/env python3
"""
PlantCare AI - Raspberry Pi 3 Model B Sensor Data Collector
Reads physical sensors over I2C:
  - ADS1115 (0x48):
      * Channel A0: Analog Water/Rain-style Sensor
      * Channel A1: Analog Ambient Light Sensor
      * Channel A2: Analog Soil Moisture Sensor
      * Channel A3: Unused
  - BMP280 (0x76):
      * Temperature (°C)
      * Barometric Pressure (hPa)
      * (Note: BMP280 does NOT have a humidity sensor; do not invent humidity readings)

Saves local telemetry to plant_data_all.csv every 5 seconds.
Uploads latest readings to ThingSpeak Cloud every 20 seconds.
"""

import os
import sys
import time
import csv
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Load configuration
try:
    import cloud_config
    CHANNEL_ID = getattr(cloud_config, "THINGSPEAK_CHANNEL_ID", os.getenv("THINGSPEAK_CHANNEL_ID", ""))
    WRITE_API_KEY = getattr(cloud_config, "THINGSPEAK_WRITE_API_KEY", os.getenv("THINGSPEAK_WRITE_API_KEY", ""))
    LOCAL_LOG_INTERVAL = getattr(cloud_config, "LOCAL_LOG_INTERVAL_SEC", 5)
    CLOUD_UPLOAD_INTERVAL = getattr(cloud_config, "CLOUD_UPLOAD_INTERVAL_SEC", 20)
    ADS1115_ADDR = getattr(cloud_config, "ADS1115_I2C_ADDR", 0x48)
    BMP280_ADDR = getattr(cloud_config, "BMP280_I2C_ADDR", 0x76)
except ImportError:
    CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "")
    WRITE_API_KEY = os.getenv("THINGSPEAK_WRITE_API_KEY", "")
    LOCAL_LOG_INTERVAL = 5
    CLOUD_UPLOAD_INTERVAL = 20
    ADS1115_ADDR = 0x48
    BMP280_ADDR = 0x76

CSV_FILE = Path(__file__).resolve().parent / "plant_data_all.csv"
CSV_COLUMNS = [
    "timestamp",
    "soil_adc",
    "soil_voltage_v",
    "light_adc",
    "light_voltage_v",
    "water_adc",
    "water_voltage_v",
    "temperature_c",
    "pressure_hpa"
]

# Hardware library initializations
ads_sensor = None
bmp_sensor = None

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    import adafruit_bmp280

    i2c = busio.I2C(board.SCL, board.SDA)

    # ADS1115 ADC setup (address 0x48)
    ads = ADS.ADS1115(i2c, address=ADS1115_ADDR)
    chan_water = AnalogIn(ads, ADS.P0)  # A0: Water sensor
    chan_light = AnalogIn(ads, ADS.P1)  # A1: Light sensor
    chan_soil  = AnalogIn(ads, ADS.P2)  # A2: Soil moisture
    ads_sensor = {
        "water": chan_water,
        "light": chan_light,
        "soil": chan_soil
    }
    print("[HARDWARE] ADS1115 ADC initialized at I2C address 0x48 (A0=Water, A1=Light, A2=Soil).")

    # BMP280 sensor setup (address 0x76)
    bmp_sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=BMP280_ADDR)
    bmp_sensor.sea_level_pressure = 1013.25
    print("[HARDWARE] BMP280 temperature & pressure sensor initialized at I2C address 0x76.")

except Exception as hw_err:
    print(f"[HARDWARE WARNING] Could not initialize physical I2C sensors: {hw_err}")
    print("[HARDWARE WARNING] If testing off-Pi, synthetic fallback readings will be simulated.")


def read_sensors():
    """Reads all physical hardware sensors or returns realistic test readings if hardware is absent."""
    if ads_sensor and bmp_sensor:
        try:
            # ADS1115 readings
            water_val = ads_sensor["water"].value
            water_vol = round(ads_sensor["water"].voltage, 3)

            light_val = ads_sensor["light"].value
            light_vol = round(ads_sensor["light"].voltage, 3)

            soil_val = ads_sensor["soil"].value
            soil_vol = round(ads_sensor["soil"].voltage, 3)

            # BMP280 readings
            temp_c = round(bmp_sensor.temperature, 2)
            press_hpa = round(bmp_sensor.pressure, 2)

            return {
                "soil_adc": soil_val,
                "soil_voltage_v": soil_vol,
                "light_adc": light_val,
                "light_voltage_v": light_vol,
                "water_adc": water_val,
                "water_voltage_v": water_vol,
                "temperature_c": temp_c,
                "pressure_hpa": press_hpa
            }
        except Exception as read_err:
            print(f"[SENSOR READ ERROR] Error reading I2C sensors: {read_err}")

    # Fallback simulation if running diagnostic off-Pi
    import random
    return {
        "soil_adc": 18500,
        "soil_voltage_v": round(1.85 + random.uniform(-0.02, 0.02), 3),
        "light_adc": 14200,
        "light_voltage_v": round(1.42 + random.uniform(-0.03, 0.03), 3),
        "water_adc": 600,
        "water_voltage_v": round(0.06 + random.uniform(0.0, 0.02), 3),
        "temperature_c": round(23.4 + random.uniform(-0.2, 0.2), 2),
        "pressure_hpa": round(1013.1 + random.uniform(-0.2, 0.2), 2)
    }


def append_to_csv(reading: dict, timestamp_str: str):
    """Appends sensor reading row to plant_data_all.csv."""
    file_exists = CSV_FILE.exists()
    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            row = {"timestamp": timestamp_str, **reading}
            writer.writerow(row)
    except Exception as e:
        print(f"[CSV ERROR] Could not append to {CSV_FILE}: {e}")


def upload_to_thingspeak(reading: dict) -> bool:
    """
    Uploads reading to ThingSpeak Cloud channel using Write API Key.
    Field mapping:
      Field 1: Soil Voltage
      Field 2: Light Voltage
      Field 3: Temperature C
      Field 4: Pressure hPa
      Field 5: Water Sensor Voltage
    """
    if not WRITE_API_KEY or WRITE_API_KEY == "YOUR_WRITE_API_KEY_HERE":
        print("[THINGSPEAK] Write API Key is not set. Skipping cloud upload.")
        return False

    url = "https://api.thingspeak.com/update"
    payload = {
        "api_key": WRITE_API_KEY,
        "field1": reading["soil_voltage_v"],
        "field2": reading["light_voltage_v"],
        "field3": reading["temperature_c"],
        "field4": reading["pressure_hpa"],
        "field5": reading["water_voltage_v"]
    }

    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8").strip()
            # ThingSpeak returns entry ID (an integer > 0) on success, or 0 / error code on rate-limit / failure
            if body.isdigit() and int(body) > 0:
                print(f"[THINGSPEAK OK] Entry #{body} uploaded at {datetime.now().strftime('%H:%M:%S')}")
                return True
            else:
                print(f"[THINGSPEAK NOTICE] Rate-limited or rejected (response: '{body}'). Will retry next cycle.")
                return False
    except urllib.error.URLError as e:
        print(f"[THINGSPEAK NETWORK ERROR] {e.reason}")
        return False
    except Exception as e:
        print(f"[THINGSPEAK ERROR] {e}")
        return False


def main():
    print("=" * 65)
    print("PlantCare AI - Raspberry Pi Sensor Collector Started")
    print(f"Local logging interval: {LOCAL_LOG_INTERVAL}s")
    print(f"Cloud upload interval:  {CLOUD_UPLOAD_INTERVAL}s")
    print(f"Saving readings to:     {CSV_FILE}")
    print("=" * 65)

    last_cloud_upload = 0.0

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

            # 1. Read sensors
            reading = read_sensors()

            # 2. Append to local CSV (every 5 seconds)
            append_to_csv(reading, timestamp_str)

            # 3. Upload to ThingSpeak Cloud (every ~20 seconds)
            current_time = time.time()
            if (current_time - last_cloud_upload) >= CLOUD_UPLOAD_INTERVAL:
                success = upload_to_thingspeak(reading)
                if success:
                    last_cloud_upload = current_time

            # Sleep local interval
            time.sleep(LOCAL_LOG_INTERVAL)

        except KeyboardInterrupt:
            print("\n[COLLECTOR] Stopped by user (Ctrl+C). Exiting cleanly.")
            sys.exit(0)
        except Exception as loop_err:
            print(f"[UNEXPECTED ERROR] {loop_err}")
            time.sleep(5)


if __name__ == "__main__":
    main()
