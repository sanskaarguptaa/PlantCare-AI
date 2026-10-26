"""
Hardware Diagnostic & Calibration Utility for Raspberry Pi.
Run this script directly on your Raspberry Pi to test individual sensors and the relay.
Usage: python test_hardware.py
"""
import sys
import time

def test_i2c():
    print("\n--- 1. Testing I2C Bus Detection ---")
    try:
        import busio
        import board
        i2c = busio.I2C(board.SCL, board.SDA)
        while not i2c.try_lock():
            pass
        addresses = [hex(x) for x in i2c.scan()]
        i2c.unlock()
        print(f"Detected I2C Addresses: {addresses}")
        
        expected = {
            "0x48": "ADS1115 ADC Module",
            "0x76": "BME280 Environmental Sensor (or 0x77)",
            "0x77": "BME280 Environmental Sensor (alt address)",
            "0x23": "BH1750 Light Sensor (or 0x5c)",
            "0x5c": "BH1750 Light Sensor (alt address)"
        }
        for addr, name in expected.items():
            if addr in addresses:
                print(f"  [OK] Found {name} at {addr}")
            else:
                print(f"  [?] Not found: {name} (expected {addr})")
    except Exception as e:
        print(f"I2C test error: {e}")

def test_ads1115():
    print("\n--- 2. Testing Capacitive Soil Moisture Sensor (ADS1115) ---")
    try:
        from sensors.ads1115_reader import ADS1115Reader
        reader = ADS1115Reader()
        if not reader.is_connected:
            print("ADS1115 hardware not connected.")
            return
        for i in range(5):
            raw, volt = reader.read_raw()
            pct = reader.read_moisture_percentage()
            print(f"[{i+1}/5] Raw Value: {raw:5d} | Voltage: {volt:4.2f}V | Calculated Moisture: {pct:5.1f}%")
            time.sleep(1)
        print(">> Calibration Tip: Put sensor in dry air, note raw value. Submerge tip in water, note raw value.")
    except Exception as e:
        print(f"ADS1115 error: {e}")

def test_bme280():
    print("\n--- 3. Testing BME280 Sensor ---")
    try:
        from sensors.bme280_reader import BME280Reader
        reader = BME280Reader()
        if not reader.is_connected:
            print("BME280 hardware not connected.")
            return
        data = reader.read()
        print(f"Temperature: {data['temperature']} °C")
        print(f"Humidity:    {data['humidity']} %")
        print(f"Pressure:    {data['pressure']} hPa")
    except Exception as e:
        print(f"BME280 error: {e}")

def test_bh1750():
    print("\n--- 4. Testing BH1750 Light Sensor ---")
    try:
        from sensors.bh1750_reader import BH1750Reader
        reader = BH1750Reader()
        if not reader.is_connected:
            print("BH1750 hardware not connected.")
            return
        lux = reader.read_lux()
        print(f"Light Intensity: {lux} Lux")
    except Exception as e:
        print(f"BH1750 error: {e}")

def test_relay():
    print("\n--- 5. Testing Relay / Pump Control (GPIO 17) ---")
    ans = input("Do you want to test toggling the relay for 1 second? (y/N): ").strip().lower()
    if ans == 'y':
        try:
            import RPi.GPIO as GPIO
            from config import PUMP_GPIO_PIN, PUMP_ACTIVE_LOW
            GPIO.setmode(GPIO.BCM)
            initial = GPIO.HIGH if PUMP_ACTIVE_LOW else GPIO.LOW
            active = GPIO.LOW if PUMP_ACTIVE_LOW else GPIO.HIGH
            
            GPIO.setup(PUMP_GPIO_PIN, GPIO.OUT, initial=initial)
            print("Clicking Relay ON...")
            GPIO.output(PUMP_GPIO_PIN, active)
            time.sleep(1.0)
            print("Clicking Relay OFF...")
            GPIO.output(PUMP_GPIO_PIN, initial)
            GPIO.cleanup(PUMP_GPIO_PIN)
            print("[OK] Relay test completed.")
        except Exception as e:
            print(f"Relay test error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  FloraAI Hardware Diagnostic Tool")
    print("=" * 60)
    test_i2c()
    test_ads1115()
    test_bme280()
    test_bh1750()
    test_relay()
    print("\nDiagnostics finished.")
