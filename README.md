# 🌿 FloraAI: AI-Based Smart Plant Monitoring & Automatic Watering System

An intelligent IoT and Machine Learning system running on a **Raspberry Pi 3 Model B** that monitors environmental conditions in real time, assesses plant health using agronomic metrics (VPD) and ML Anomaly Detection (Isolation Forest), serves a responsive real-time web dashboard, and automatically waters plants safely.

---

## 🌟 Key Features

1. **Multi-Sensor Environmental Telemetry**:
   - **Soil Moisture**: Analog capacitive soil moisture sensor read through an **ADS1115 16-bit ADC**.
   - **Temperature & Humidity**: **BME280** high-precision I2C digital sensor.
   - **Light Intensity**: **BH1750** ambient light sensor measuring lux levels.
2. **Machine Learning & Agronomic AI Engine**:
   - **Vapor Pressure Deficit (VPD)**: Real-time calculation of atmospheric drying pressure and transpiration stress.
   - **Health Index (0-100%)**: Multi-variable plant vitality score based on plant profiles (Houseplants, Succulents, Herbs).
   - **Unsupervised Anomaly Detection (Isolation Forest)**: Flags unusual sensor drifts, rapid moisture depletion (leaks), or extreme climate stress.
   - **AI Diagnostic Insights**: Human-readable status notes explaining plant conditions.
3. **Safety-Guarded Automatic Watering**:
   - Automated relay trigger when soil moisture drops below user threshold.
   - Safety cooldown timer (default 20 mins) to allow water to permeate roots.
   - Maximum continuous pumping duration and daily cycle safety limit to prevent accidental flooding or pump burnout.
4. **Real-Time Interactive Web Dashboard**:
   - Live WebSocket data streaming every 3 seconds.
   - Dynamic Chart.js telemetry trends.
   - Manual watering button with countdown timer and safety locks.
   - Configurable sensitivity threshold sliders and plant species profiles.
   - AI Testing Sandbox for simulating anomalies.
5. **Seamless Cross-Platform Simulation**:
   - Can run on Windows, Mac, or Linux without physical hardware attached using an intelligent diurnal physics simulator.
   - Automatically detects physical I2C sensors when booted on a Raspberry Pi.

---

## 🛠️ Hardware Bill of Materials (BOM)

| Component | Purpose | Interface |
| :--- | :--- | :--- |
| **Raspberry Pi 3 Model B** | Central controller & web server | Linux / GPIO |
| **Capacitive Soil Moisture Sensor v1.2** | Corrosion-resistant soil moisture reading | Analog Output |
| **ADS1115 ADC Module** | Converts analog soil voltage to digital I2C | I2C (`0x48`) |
| **BME280 Sensor** | Temperature, Relative Humidity, Pressure | I2C (`0x76` or `0x77`) |
| **BH1750 Sensor** | Ambient light measurement | I2C (`0x23` or `0x5C`) |
| **5V Single-Channel Relay Module** | Electrically isolated switch for pump | GPIO 17 (Pin 11) |
| **3V-6V Mini Submersible Water Pump** | Pumps water from reservoir to plant | Relay Switched |
| **Silicone Tubing & Breadboard Wires** | Water distribution & circuit connections | - |

For complete pin-by-pin connections, see [hardware/wiring_diagram.md](hardware/wiring_diagram.md).

---

## 📸 Hardware Setup & Proof of Implementation

Physical hardware implementation running on Raspberry Pi 3 Model B with analog-to-digital converter (ADS1115) and environmental telemetry sensors:

| Hardware Setup Overview | Sensor Wiring & Breadboard Connections |
| :---: | :---: |
| <img src="hardware/images/hardware_setup_1.jpg" alt="PlantCare IoT Hardware Setup 1" width="450"/> | <img src="hardware/images/hardware_setup_2.jpg" alt="PlantCare IoT Hardware Setup 2" width="450"/> |
| *Raspberry Pi 3 Model B, ADS1115 ADC, and sensor telemetry assembly* | *Breadboard wiring, power distribution rails, and sensor pinout* |

---

## 📂 Project Architecture

```
Plant monitor/
├── config.py                 # Central configurations, pin numbers, thresholds, calibration
├── requirements.txt          # Python dependencies
├── run_demo.py               # One-click launch script
├── test_hardware.py          # Diagnostic tool to test I2C sensors and relay on the Pi
├── setup_pi.sh               # Raspberry Pi automated installer & systemd setup
├── database/
│   └── db.py                 # SQLite database for telemetry, logs, and settings
├── sensors/
│   ├── sensor_manager.py     # Unified manager: switches between physical I2C and simulator
│   ├── ads1115_reader.py     # ADS1115 16-bit ADC reader
│   ├── bme280_reader.py      # BME280 temperature & humidity reader
│   └── bh1750_reader.py      # BH1750 ambient light reader
├── actuators/
│   └── pump_controller.py    # Relay safety controller (anti-flood guards, cooldowns)
├── ml/
│   ├── plant_ai.py           # Isolation Forest anomaly detection, VPD & Health scoring
│   └── train_model.py        # Model training script
├── static/
│   ├── index.html            # Web dashboard
│   ├── app.js                # Frontend WebSocket & Chart.js logic
│   └── style.css             # Dashboard styling
└── server.py                 # FastAPI backend & WebSocket server
```

---

## 🚀 Getting Started

### 1. Test on your PC right now (Simulation Mode)

You don't need the Raspberry Pi plugged in to test the dashboard, AI, and controls!

1. Open your terminal in this directory:
   ```bash
   python run_demo.py
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```
3. You can watch live simulated data, adjust thresholds, test manual watering, or click **"Simulate Heatwave"** in the AI Sandbox to see the Machine Learning anomaly detector in action!

---

### 2. Deploy to Raspberry Pi 3 Model B

1. Connect your sensors and relay according to [hardware/wiring_diagram.md](hardware/wiring_diagram.md).
2. Copy this project folder to your Raspberry Pi (via SCP, Git, or USB drive).
3. Open a terminal on the Raspberry Pi and run the automated setup script:
   ```bash
   bash setup_pi.sh
   ```
   This script will:
   - Enable the Raspberry Pi I2C interface.
   - Install all necessary system libraries (`i2c-tools`, `libgpiod-dev`, etc.).
   - Set up a Python virtual environment and install dependencies.
   - Train the initial AI model.
   - Create and enable a background service `flora_plant_monitor.service` so it runs 24/7 on boot!

4. Verify your physical sensors with the diagnostic tool:
   ```bash
   source venv/bin/activate
   python test_hardware.py
   ```

5. Access your live plant dashboard from any phone, tablet, or laptop on the same Wi-Fi network:
   ```
   http://<raspberry-pi-ip>:8000
   ```
