"""
PlantCare AI - Raspberry Pi Cloud Configuration Template
Copy this file to 'cloud_config.py' on your Raspberry Pi:
    cp cloud_config.example.py cloud_config.py
And enter your actual ThingSpeak Channel ID and Write API Key.
NEVER commit cloud_config.py with real API keys to GitHub!
"""

# Your ThingSpeak Channel ID (Found on ThingSpeak Channel Settings)
THINGSPEAK_CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"

# Your ThingSpeak Write API Key (Found on ThingSpeak -> API Keys -> Write API Key)
THINGSPEAK_WRITE_API_KEY = "YOUR_WRITE_API_KEY_HERE"

# Local logging interval (seconds between saving to plant_data_all.csv)
LOCAL_LOG_INTERVAL_SEC = 5

# Cloud upload interval (seconds between uploading to ThingSpeak)
# ThingSpeak free tier requires >= 15 seconds. 20 seconds is safe and recommended.
CLOUD_UPLOAD_INTERVAL_SEC = 20

# I2C Addresses
ADS1115_I2C_ADDR = 0x48
BMP280_I2C_ADDR = 0x76
