"""
ADS1115 16-Bit ADC Reader for Capacitive Soil Moisture Sensor.
Converts analog voltage/count to calibrated soil moisture percentage.
"""
import logging
from config import (
    ADS1115_I2C_ADDR,
    SOIL_ADC_CHANNEL,
    SOIL_DRY_ADC,
    SOIL_WET_ADC
)

logger = logging.getLogger("SensorADS1115")

class ADS1115Reader:
    def __init__(self, i2c_bus=None, address=ADS1115_I2C_ADDR):
        self.address = address
        self.adc = None
        self.chan = None
        self.is_connected = False
        
        try:
            import board
            import busio
            import adafruit_ads1x15.ads1115 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn
            
            i2c = i2c_bus if i2c_bus is not None else busio.I2C(board.SCL, board.SDA)
            self.adc = ADS.ADS1115(i2c, address=self.address)
            
            channel_map = {
                0: ADS.P0,
                1: ADS.P1,
                2: ADS.P2,
                3: ADS.P3
            }
            selected_pin = channel_map.get(SOIL_ADC_CHANNEL, ADS.P0)
            self.chan = AnalogIn(self.adc, selected_pin)
            self.is_connected = True
            logger.info("ADS1115 ADC initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize ADS1115 hardware: {e}")
            self.is_connected = False

    def read_raw(self):
        """Returns (raw_value, voltage)."""
        if not self.is_connected or self.chan is None:
            raise RuntimeError("ADS1115 hardware not connected")
        return self.chan.value, self.chan.voltage

    def read_moisture_percentage(self) -> float:
        """
        Calculates calibrated soil moisture percentage (0% to 100%).
        Note on capacitive sensors: Higher raw value = drier soil. Lower raw value = wetter soil.
        """
        raw_val, _ = self.read_raw()
        
        # Linear conversion based on dry and wet calibration points
        # If dry = 22500 and wet = 11000
        span = SOIL_DRY_ADC - SOIL_WET_ADC
        if span == 0:
            return 50.0
            
        percentage = ((SOIL_DRY_ADC - raw_val) / span) * 100.0
        # Clamp within 0% to 100%
        return max(0.0, min(100.0, round(percentage, 1)))
