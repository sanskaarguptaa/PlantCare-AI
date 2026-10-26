# 🍓 PlantCare AI - Raspberry Pi Collector Guide

This folder contains the complete collector script and systemd background service configuration for running on your **Raspberry Pi 3 Model B** with **Raspbian GNU/Linux 13 (Trixie)**.

---

## 🔌 Hardware Connections Review

| Sensor | Sensor Pin / Output | Connected To | I2C Address | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **ADS1115 ADC** | SDA, SCL, VCC (3.3V), GND | Raspberry Pi Pin 3 (SDA), Pin 5 (SCL), Pin 1 (3.3V), Pin 6 (GND) | `0x48` | Reads all 3 analog sensors |
| **BMP280 Sensor** | SDA, SCL, VCC (3.3V), GND | Shares Raspberry Pi I2C Bus (Pins 3 & 5) | `0x76` | Reads Temperature (°C) & Pressure (hPa) |
| **Water / Rain Sensor** | Analog Output (S) | ADS1115 Channel **A0** | - | Raw voltage signal (not tank level) |
| **Light Sensor** | Analog Output (AO) | ADS1115 Channel **A1** | - | Raw voltage signal |
| **Soil Moisture Sensor**| Analog Output | ADS1115 Channel **A2** | - | Raw voltage signal |
| **ADS1115 A3** | Unused | - | - | Free for future expansion |
| **Water Pump** | **NOT CONNECTED** | - | - | Pump is disabled (no motor driver) |

> ⚠️ **Important Reminder**: Analog sensors cannot be connected directly to Raspberry Pi GPIO pins because the Pi has no built-in ADC. They are properly read through the **ADS1115** 16-bit converter.
> ⚠️ **BMP280 Sensor Note**: The BMP280 measures temperature and barometric pressure. Unlike the BME280, it does **not** measure humidity. The application does not fabricate humidity readings.

---

## 🚀 Raspberry Pi Setup Commands

Run these commands in a terminal on your Raspberry Pi:

### 1. Enable I2C (if not already enabled)
```bash
sudo raspi-config
```
Navigate to: `Interface Options` -> `I2C` -> `Enable` -> `Finish`.

Verify I2C devices:
```bash
sudo apt-get update && sudo apt-get install -y i2c-tools
i2cdetect -y 1
```
You should see:
- `48` (ADS1115)
- `76` (BMP280)

### 2. Enter your project directory & virtual environment
```bash
cd ~/plant-monitor
source .venv/bin/activate
```

Install hardware dependencies if needed:
```bash
pip install adafruit-circuitpython-ads1x15 adafruit-circuitpython-bmp280
```

### 3. Configure ThingSpeak Credentials
Copy `cloud_config.example.py` to `cloud_config.py`:
```bash
cp cloud_config.example.py cloud_config.py
nano cloud_config.py
```
Fill in your `THINGSPEAK_CHANNEL_ID` and `THINGSPEAK_WRITE_API_KEY`. Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

### 4. Test run the collector
```bash
python collect_cloud.py
```
You should see output like:
```
[HARDWARE] ADS1115 ADC initialized at I2C address 0x48 (A0=Water, A1=Light, A2=Soil).
[HARDWARE] BMP280 temperature & pressure sensor initialized at I2C address 0x76.
[THINGSPEAK OK] Entry #1 uploaded at 14:20:05
```

### 5. Run as an automatic background service (Optional)
To have the collector start automatically whenever your Pi boots up:
```bash
sudo cp plantcare-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable plantcare-collector.service
sudo systemctl start plantcare-collector.service
```

Check service status anytime:
```bash
sudo systemctl status plantcare-collector.service
```

View live logs:
```bash
journalctl -u plantcare-collector.service -f
```
