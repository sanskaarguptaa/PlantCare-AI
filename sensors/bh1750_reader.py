"""
BH1750 Ambient Light Sensor Reader.
Measures Ambient Light illuminance in Lux.
"""
import logging
from config import BH1750_I2C_ADDR

logger = logging.getLogger("SensorBH1750")

class BH1750Reader:
    def __init__(self, i2c_bus=None, address=BH1750_I2C_ADDR):
        self.address = address
        self.sensor = None
        self.is_connected = False
        
        try:
            import board
            import busio
            import adafruit_bh1750
            
            i2c = i2c_bus if i2c_bus is not None else busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_bh1750.BH1750(i2c, address=self.address)
            self.is_connected = True
            logger.info("BH1750 light sensor initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize BH1750 hardware: {e}")
            self.is_connected = False

    def read_lux(self) -> float:
        """Returns light intensity in Lux."""
        if not self.is_connected or self.sensor is None:
            raise RuntimeError("BH1750 hardware not connected")
            
        return round(self.sensor.lux, 2)
