"""
BME280 Environmental Sensor Reader.
Measures Ambient Temperature (°C), Relative Humidity (%), and Pressure (hPa).
"""
import logging
from config import BME280_I2C_ADDR

logger = logging.getLogger("SensorBME280")

class BME280Reader:
    def __init__(self, i2c_bus=None, address=BME280_I2C_ADDR):
        self.address = address
        self.sensor = None
        self.is_connected = False
        
        try:
            import board
            import busio
            from adafruit_bme280 import basic as adafruit_bme280
            
            i2c = i2c_bus if i2c_bus is not None else busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=self.address)
            self.is_connected = True
            logger.info("BME280 sensor initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize BME280 hardware: {e}")
            self.is_connected = False

    def read(self):
        """Returns dict of temperature, humidity, pressure."""
        if not self.is_connected or self.sensor is None:
            raise RuntimeError("BME280 hardware not connected")
            
        temp = round(self.sensor.temperature, 2)
        humidity = round(self.sensor.relative_humidity, 2)
        pressure = round(self.sensor.pressure, 2)
        
        return {
            "temperature": temp,
            "humidity": humidity,
            "pressure": pressure
        }
