/**
 * FloraAI Dashboard Controller
 * WebSocket real-time telemetry, Chart.js multi-series graphing, and control interactions.
 */

let ws = null;
let currentChartTab = "moisture";
let telemetryChart = null;
let historyData = [];

// Initialize Lucide Icons
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  initChart();
  connectWebSocket();
  loadInitialHistory();
  refreshLogs();
});

// WebSocket Connection & Reconnection
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/live`;

  const wsIndicator = document.getElementById("ws-indicator");
  const wsStatus = document.getElementById("ws-status");

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    wsIndicator.className = "w-2 h-2 rounded-full bg-emerald-400";
    wsStatus.textContent = "Live";
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateDashboard(data);
      appendDataToChart(data);
    } catch (e) {
      console.error("Error parsing WS packet:", e);
    }
  };

  ws.onclose = () => {
    wsIndicator.className = "w-2 h-2 rounded-full bg-amber-400";
    wsStatus.textContent = "Reconnecting...";
    setTimeout(connectWebSocket, 2500);
  };

  ws.onerror = () => {
    ws.close();
  };
}

// Update UI elements with incoming telemetry
function updateDashboard(data) {
  // 1. Hardware vs Simulation Mode
  const modeBadge = document.getElementById("mode-badge");
  const modeText = document.getElementById("mode-text");
  if (data.is_simulated) {
    modeBadge.className = "px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 border bg-amber-500/10 text-amber-300 border-amber-500/30";
    modeText.textContent = "Simulation Mode";
  } else {
    modeBadge.className = "px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 border bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
    modeText.textContent = "Hardware Mode (Pi I2C)";
  }

  // 2. AI Health & Anomaly
  const healthVal = document.getElementById("health-index-val");
  const healthRing = document.getElementById("health-ring");
  const healthScore = Math.round(data.health_index || 0);
  healthVal.textContent = healthScore;
  healthRing.setAttribute("stroke-dasharray", `${healthScore}, 100`);

  const statusBadge = document.getElementById("ai-status-badge");
  statusBadge.textContent = data.status_title || "Healthy";
  if (healthScore >= 80) {
    statusBadge.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    healthVal.className = "text-3xl font-extrabold text-emerald-400";
  } else if (healthScore >= 50) {
    statusBadge.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30";
    healthVal.className = "text-3xl font-extrabold text-amber-400";
  } else {
    statusBadge.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30";
    healthVal.className = "text-3xl font-extrabold text-rose-400";
  }

  // Anomaly Badge
  const anomalyBadge = document.getElementById("anomaly-badge");
  if (data.is_anomaly) {
    anomalyBadge.classList.remove("hidden");
    anomalyBadge.textContent = `Anomaly (${data.anomaly_score})`;
  } else {
    anomalyBadge.classList.add("hidden");
  }

  // Diagnostic Insights Text
  const insightText = document.getElementById("ai-insight-text");
  if (data.insights && data.insights.length > 0) {
    insightText.innerHTML = data.insights.map(i => `• ${i}`).join("<br/>");
  }

  // 3. Sensor Cards
  // Soil Moisture
  const m = data.soil_moisture;
  document.getElementById("val-moisture").textContent = `${m}%`;
  document.getElementById("bar-moisture").style.width = `${Math.min(100, Math.max(0, m))}%`;
  const mBadge = document.getElementById("badge-moisture");
  if (m < 30) {
    mBadge.textContent = "Dry";
    mBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-rose-500/20 text-rose-300";
  } else if (m > 75) {
    mBadge.textContent = "Very Wet";
    mBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-blue-500/20 text-blue-300";
  } else {
    mBadge.textContent = "Optimal";
    mBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-500/20 text-emerald-300";
  }

  // Temperature
  const t = data.temperature;
  document.getElementById("val-temp").textContent = `${t}°C`;
  const tempPct = Math.min(100, Math.max(0, ((t - 10) / 30) * 100));
  document.getElementById("bar-temp").style.width = `${tempPct}%`;
  const tBadge = document.getElementById("badge-temp");
  if (t < 15) {
    tBadge.textContent = "Cold";
    tBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-500/20 text-cyan-300";
  } else if (t > 30) {
    tBadge.textContent = "Hot";
    tBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-amber-500/20 text-amber-300";
  } else {
    tBadge.textContent = "Comfortable";
    tBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-500/20 text-emerald-300";
  }

  // Humidity & VPD
  const h = data.humidity;
  document.getElementById("val-humidity").textContent = `${h}%`;
  document.getElementById("bar-humidity").style.width = `${Math.min(100, Math.max(0, h))}%`;
  document.getElementById("badge-vpd").textContent = `VPD: ${data.vpd} kPa`;
  document.getElementById("val-pressure").textContent = `${data.pressure} hPa`;

  // Light
  const lux = data.lux;
  document.getElementById("val-lux").textContent = `${lux} Lux`;
  const luxPct = Math.min(100, Math.max(0, (lux / 10000) * 100));
  document.getElementById("bar-lux").style.width = `${luxPct}%`;
  const lBadge = document.getElementById("badge-lux");
  if (lux < 250) {
    lBadge.textContent = "Dim / Dark";
    lBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-slate-800 text-slate-300";
  } else if (lux > 8000) {
    lBadge.textContent = "Direct Sun";
    lBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-amber-500/20 text-amber-300";
  } else {
    lBadge.textContent = "Bright Indirect";
    lBadge.className = "text-xs px-2 py-0.5 rounded-full font-medium bg-yellow-500/20 text-yellow-300";
  }

  // 4. Pump state
  const pumpBadge = document.getElementById("pump-status-badge");
  const manualBtn = document.getElementById("btn-manual-water");
  if (data.pump_active) {
    pumpBadge.className = "px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse";
    pumpBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span><span>Dispensing Water...</span>`;
    manualBtn.disabled = true;
  } else {
    pumpBadge.className = "px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 bg-slate-800 text-slate-400 border border-slate-700";
    pumpBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-slate-500"></span><span>Pump Idle</span>`;
    manualBtn.disabled = false;
  }

  // 5. Settings sync
  if (data.auto_watering_enabled !== undefined) {
    document.getElementById("toggle-autowater").checked = data.auto_watering_enabled;
  }
  if (data.moisture_threshold !== undefined) {
    document.getElementById("slider-threshold").value = data.moisture_threshold;
    document.getElementById("slider-threshold-val").textContent = `${data.moisture_threshold}%`;
    document.getElementById("threshold-marker").textContent = `Target: ${data.moisture_threshold}%`;
  }
  if (data.plant_profile !== undefined) {
    document.getElementById("select-profile").value = data.plant_profile;
  }
}

// Chart.js Setup
function initChart() {
  const ctx = document.getElementById("telemetryChart").getContext("2d");
  telemetryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: { color: "#94a3b8", boxWidth: 12, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "#334155",
          borderWidth: 1
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#64748b", maxRotation: 0 }
        },
        y: {
          grid: { color: "rgba(51, 65, 85, 0.3)" },
          ticks: { color: "#64748b" }
        }
      }
    }
  });

  updateChartStructure();
}

function updateChartStructure() {
  if (!telemetryChart) return;

  if (currentChartTab === "moisture") {
    telemetryChart.data.datasets = [
      {
        label: "Soil Moisture (%)",
        data: historyData.map(d => d.soil_moisture),
        borderColor: "#06b6d4",
        backgroundColor: "rgba(6, 182, 212, 0.1)",
        fill: true,
        tension: 0.35,
        borderWidth: 2.5,
        pointRadius: 2
      }
    ];
    telemetryChart.options.scales.y.title = { display: true, text: "Moisture %", color: "#64748b" };
    telemetryChart.options.scales.y.min = 0;
    telemetryChart.options.scales.y.max = 100;
  } else if (currentChartTab === "temp-hum") {
    telemetryChart.data.datasets = [
      {
        label: "Temperature (°C)",
        data: historyData.map(d => d.temperature),
        borderColor: "#f59e0b",
        backgroundColor: "transparent",
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 2
      },
      {
        label: "Humidity (%)",
        data: historyData.map(d => d.humidity),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.05)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 2
      }
    ];
    telemetryChart.options.scales.y.title = { display: false };
    delete telemetryChart.options.scales.y.min;
    delete telemetryChart.options.scales.y.max;
  } else if (currentChartTab === "light") {
    telemetryChart.data.datasets = [
      {
        label: "Light (Lux)",
        data: historyData.map(d => d.lux),
        borderColor: "#eab308",
        backgroundColor: "rgba(234, 179, 8, 0.1)",
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 2
      }
    ];
    telemetryChart.options.scales.y.title = { display: true, text: "Lux", color: "#64748b" };
    delete telemetryChart.options.scales.y.min;
    delete telemetryChart.options.scales.y.max;
  }

  telemetryChart.data.labels = historyData.map(d => d.timeLabel || "");
  telemetryChart.update();
}

function switchChartTab(tab) {
  currentChartTab = tab;
  const tabs = ["moisture", "temp-hum", "light"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    if (t === tab) {
      el.className = "px-3 py-1 rounded-lg bg-emerald-500 text-white font-semibold transition";
    } else {
      el.className = "px-3 py-1 rounded-lg text-slate-400 hover:text-white transition";
    }
  });
  updateChartStructure();
}

function appendDataToChart(reading) {
  const now = new Date();
  const timeLabel = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

  const entry = {
    timeLabel: timeLabel,
    soil_moisture: reading.soil_moisture,
    temperature: reading.temperature,
    humidity: reading.humidity,
    lux: reading.lux
  };

  historyData.push(entry);
  if (historyData.length > 30) {
    historyData.shift();
  }

  telemetryChart.data.labels = historyData.map(d => d.timeLabel);
  if (currentChartTab === "moisture") {
    telemetryChart.data.datasets[0].data = historyData.map(d => d.soil_moisture);
  } else if (currentChartTab === "temp-hum") {
    telemetryChart.data.datasets[0].data = historyData.map(d => d.temperature);
    telemetryChart.data.datasets[1].data = historyData.map(d => d.humidity);
  } else if (currentChartTab === "light") {
    telemetryChart.data.datasets[0].data = historyData.map(d => d.lux);
  }

  telemetryChart.update("none");
}

async function loadInitialHistory() {
  try {
    const res = await fetch("/api/history?limit=25");
    const json = await res.json();
    if (json.readings && json.readings.length > 0) {
      historyData = json.readings.map(r => {
        const d = new Date(r.timestamp);
        return {
          timeLabel: `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`,
          soil_moisture: r.soil_moisture,
          temperature: r.temperature,
          humidity: r.humidity,
          lux: r.lux
        };
      });
      updateChartStructure();
    }
  } catch (e) {
    console.warn("Could not fetch historical telemetry:", e);
  }
}

// User Actions
async function triggerManualWater() {
  const btn = document.getElementById("btn-manual-water");
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin"></i> Dispensing Water...`;
  lucide.createIcons();

  try {
    const res = await fetch("/api/water", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration: 3.5 })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(`Watering warning: ${data.detail || "Action disallowed"}`);
    } else {
      setTimeout(refreshLogs, 4000);
    }
  } catch (e) {
    alert(`Request error: ${e.message}`);
  } finally {
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.disabled = false;
      lucide.createIcons();
    }, 3800);
  }
}

async function updateSettings() {
  const autowater = document.getElementById("toggle-autowater").checked;
  const threshold = parseFloat(document.getElementById("slider-threshold").value);
  const profile = document.getElementById("select-profile").value;

  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        auto_watering_enabled: autowater,
        moisture_threshold: threshold,
        plant_profile: profile
      })
    });
  } catch (e) {
    console.error("Failed to update settings:", e);
  }
}

async function simulateAnomaly(type) {
  try {
    await fetch("/api/simulate-anomaly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anomaly_type: type })
    });
  } catch (e) {
    console.error("Failed to set synthetic anomaly:", e);
  }
}

async function refreshLogs() {
  try {
    const res = await fetch("/api/watering-history?limit=8");
    const json = await res.json();
    const tbody = document.getElementById("logs-tbody");
    tbody.innerHTML = "";

    if (!json.events || json.events.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-500">No watering cycles recorded yet.</td></tr>`;
      return;
    }

    json.events.forEach(ev => {
      const row = document.createElement("tr");
      const d = new Date(ev.timestamp);
      const timeStr = `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
      const triggerBadge = ev.trigger_type === "auto"
        ? `<span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 font-medium border border-emerald-500/20">Auto</span>`
        : `<span class="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 font-medium border border-cyan-500/20">Manual</span>`;

      row.innerHTML = `
        <td class="py-2.5 font-mono text-slate-400">${timeStr}</td>
        <td class="py-2.5 font-medium text-slate-200">Pump Activation</td>
        <td class="py-2.5 text-slate-300">${ev.duration_seconds}s</td>
        <td class="py-2.5">${triggerBadge}</td>
        <td class="py-2.5 text-cyan-400 font-semibold">${ev.moisture_before !== null ? ev.moisture_before + '%' : '--'}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (e) {
    console.warn("Could not fetch watering history:", e);
  }
}
