#!/usr/bin/env bash
# ==============================================================================
# FloraAI Raspberry Pi 3 Model B Automated Installation Script
# Run this on your Raspberry Pi: bash setup_pi.sh
# ==============================================================================

set -e

echo "================================================================="
echo "  Setting up FloraAI Smart Plant Monitor on Raspberry Pi 3B"
echo "================================================================="

# 1. Update APT packages and install prerequisites
echo "[1/6] Installing system dependencies (i2c-tools, python3-venv, etc.)..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv python3-dev i2c-tools libgpiod-dev

# 2. Enable I2C Interface automatically
echo "[2/6] Enabling Raspberry Pi I2C interface..."
sudo raspi-config nonint do_i2c 0

# Check if i2c-dev kernel module is loaded
if ! lsmod | grep -q i2c_dev; then
    echo "Loading i2c-dev module..."
    sudo modprobe i2c-dev
    echo "i2c-dev" | sudo tee -a /etc/modules
fi

# 3. Create Python Virtual Environment
echo "[3/6] Setting up Python virtual environment..."
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
fi
source venv/bin/activate

# 4. Install Python dependencies
echo "[4/6] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Train initial Machine Learning Model
echo "[5/6] Initializing AI Anomaly Detection model..."
python ml/train_model.py

# 6. Optional: Create Systemd Service for Auto-start on Boot
echo "[6/6] Configuring systemd background service..."
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

SERVICE_FILE="/etc/systemd/system/flora_plant_monitor.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=FloraAI Smart Plant Monitor & Auto-Watering Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable flora_plant_monitor.service

echo "================================================================="
echo "  SETUP COMPLETE!"
echo "================================================================="
echo "To test sensors right now:  source venv/bin/activate && python test_hardware.py"
echo "To run the dashboard:        source venv/bin/activate && python run_demo.py"
echo "To start 24/7 background:    sudo systemctl start flora_plant_monitor"
echo "To check background logs:    journalctl -u flora_plant_monitor -f"
echo "Dashboard access:            http://$(hostname -I | awk '{print $1}'):8000"
echo "================================================================="
