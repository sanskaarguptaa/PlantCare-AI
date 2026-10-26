import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  Activity, 
  Cpu, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw,
  Code2,
  Sliders,
  ShieldAlert
} from 'lucide-react';

export default function LiveDiagnostics({
  latestData,
  cloudStatus,
  onRefresh,
  isRefreshing,
  countdownSec,
  refreshInterval
}) {
  const telemetry = latestData?.data;
  const freshness = latestData?.freshness;
  const [showRawJson, setShowRawJson] = useState(false);

  // Diagnostic integrity checks on ADS1115 voltages
  const checkVoltage = (v, name) => {
    if (v === null || v === undefined) {
      return { status: 'missing', label: 'Missing', color: 'text-amber-600 bg-amber-50 border-amber-200' };
    }
    if (v <= 0.02) {
      return { status: 'low', label: 'Near GND (Check Ground / Wire)', color: 'text-amber-700 bg-amber-50 border-amber-200' };
    }
    if (v >= 3.28) {
      return { status: 'high', label: 'Near 3.3V Rail (Check Pull-Up / Wire)', color: 'text-amber-700 bg-amber-50 border-amber-200' };
    }
    return { status: 'healthy', label: 'Nominal Analog Signal', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
  };

  const soilDiag = checkVoltage(telemetry?.soil_voltage_v, 'Soil');
  const lightDiag = checkVoltage(telemetry?.light_voltage_v, 'Light');
  const waterDiag = checkVoltage(telemetry?.water_voltage_v, 'Water');

  const progressPct = refreshInterval > 0 
    ? Math.max(0, Math.min(100, ((refreshInterval - countdownSec) / refreshInterval) * 100))
    : 0;

  return (
    <div className="space-y-6">
      {/* 1. Header & Live Refresh Rate Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-emerald-700 pulse-indicator" />
              <h2 className="text-base font-bold text-slate-900">Live Telemetry Diagnostics</h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Real-time monitoring engine polling ThingSpeak Cloud at safe rate-limited intervals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[11px] font-medium text-slate-400 block">Next Cloud Poll In</span>
              <span className="text-sm font-bold text-slate-800 font-mono">{countdownSec}s</span>
            </div>
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-800 text-white hover:bg-emerald-900 disabled:opacity-50 transition-all flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              Poll Now
            </button>
          </div>
        </div>

        {/* Polling countdown progress bar */}
        <div className="w-full bg-slate-100 rounded-full h-1.5 mt-4 overflow-hidden">
          <div 
            className="bg-emerald-600 h-full transition-all duration-1000 ease-linear rounded-full"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* 2. Hardware Channel Inspection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Channel A0 */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800">ADS1115 Pin A0</span>
            <span className="font-mono text-slate-400">0x48 I2C</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-500 font-medium">Assigned Hardware:</span>
            <p className="text-sm font-bold text-slate-800">Water / Rain-Style Analog Sensor</p>
            <div className="mt-2 flex items-baseline gap-1 font-mono">
              <span className="text-2xl font-bold text-slate-900">
                {telemetry?.water_voltage_v !== null && telemetry?.water_voltage_v !== undefined ? telemetry.water_voltage_v.toFixed(3) : '--'}
              </span>
              <span className="text-xs text-slate-500">V</span>
            </div>
            <div className={`mt-2.5 inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${waterDiag.color}`}>
              {waterDiag.label}
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
            Raw analog surface signal. Treat as trace moisture presence, not a calibrated water tank level.
          </p>
        </div>

        {/* Channel A1 */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800">ADS1115 Pin A1</span>
            <span className="font-mono text-slate-400">0x48 I2C</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-500 font-medium">Assigned Hardware:</span>
            <p className="text-sm font-bold text-slate-800">Ambient Light Module (AO Output)</p>
            <div className="mt-2 flex items-baseline gap-1 font-mono">
              <span className="text-2xl font-bold text-slate-900">
                {telemetry?.light_voltage_v !== null && telemetry?.light_voltage_v !== undefined ? telemetry.light_voltage_v.toFixed(3) : '--'}
              </span>
              <span className="text-xs text-slate-500">V</span>
            </div>
            <div className={`mt-2.5 inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${lightDiag.color}`}>
              {lightDiag.label}
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
            Analog output voltage inversely or directly proportional to ambient photoperiod.
          </p>
        </div>

        {/* Channel A2 */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800">ADS1115 Pin A2</span>
            <span className="font-mono text-slate-400">0x48 I2C</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-500 font-medium">Assigned Hardware:</span>
            <p className="text-sm font-bold text-slate-800">Analog Soil Moisture Sensor</p>
            <div className="mt-2 flex items-baseline gap-1 font-mono">
              <span className="text-2xl font-bold text-slate-900">
                {telemetry?.soil_voltage_v !== null && telemetry?.soil_voltage_v !== undefined ? telemetry.soil_voltage_v.toFixed(3) : '--'}
              </span>
              <span className="text-xs text-slate-500">V</span>
            </div>
            <div className={`mt-2.5 inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${soilDiag.color}`}>
              {soilDiag.label}
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
            Capacitive / resistive substrate voltage. Voltage depends on sensor dielectric properties.
          </p>
        </div>

        {/* Channel A3 (Unused) */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800">ADS1115 Pin A3</span>
            <span className="font-mono text-slate-400">0x48 I2C</span>
          </div>
          <div className="mt-3">
            <span className="text-xs text-slate-500 font-medium">Assigned Hardware:</span>
            <p className="text-sm font-bold text-slate-800">Unused / Reserved</p>
            <div className="mt-2 flex items-baseline gap-1 font-mono">
              <span className="text-2xl font-bold text-slate-400">--</span>
              <span className="text-xs text-slate-400">Floating</span>
            </div>
            <div className="mt-2.5 inline-block text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Channel Available
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
            Free channel available for future analog sensors (e.g. EC salinity sensor or nutrient probe).
          </p>
        </div>

        {/* BMP280 Sensor */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs md:col-span-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800">BMP280 Sensor Module</span>
            <span className="font-mono text-slate-400">0x76 I2C Digital</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs text-slate-500 font-medium">Temperature:</span>
              <p className="text-2xl font-bold text-slate-900 font-mono mt-1">
                {telemetry?.temperature_c !== null && telemetry?.temperature_c !== undefined ? `${telemetry.temperature_c.toFixed(2)} °C` : '--'}
              </p>
              <span className="text-[11px] text-slate-500">Internal Bandgap Sensor</span>
            </div>
            <div>
              <span className="text-xs text-slate-500 font-medium">Barometric Pressure:</span>
              <p className="text-2xl font-bold text-slate-900 font-mono mt-1">
                {telemetry?.pressure_hpa !== null && telemetry?.pressure_hpa !== undefined ? `${telemetry.pressure_hpa.toFixed(2)} hPa` : '--'}
              </p>
              <span className="text-[11px] text-slate-500">Piezoresistive Barometer</span>
            </div>
          </div>
          <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="text-emerald-700 font-medium">✓ Calibrated against sea level 1013.25 hPa</span>
            <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
              No humidity sensor present
            </span>
          </div>
        </div>
      </div>

      {/* 3. Raw Payload Inspector */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-slate-600" />
            <h3 className="text-sm font-bold text-slate-900">Cloud Telemetry Payload Inspector</h3>
          </div>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 underline cursor-pointer"
          >
            {showRawJson ? 'Hide JSON' : 'Show Raw JSON Payload'}
          </button>
        </div>

        <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <span className="text-slate-400 block text-[10px]">Entry ID</span>
            <span className="font-mono font-bold text-slate-800">{telemetry?.entry_id || '--'}</span>
          </div>
          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <span className="text-slate-400 block text-[10px]">Cloud Timestamp (UTC)</span>
            <span className="font-mono text-slate-700 text-[11px] truncate block">
              {telemetry?.created_at || '--'}
            </span>
          </div>
          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <span className="text-slate-400 block text-[10px]">Data Source</span>
            <span className="font-semibold text-slate-800 uppercase text-[11px]">{latestData?.data_source}</span>
          </div>
          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
            <span className="text-slate-400 block text-[10px]">Freshness</span>
            <span className="font-semibold text-slate-800 text-[11px]">
              {freshness?.seconds_ago !== null ? `${freshness.seconds_ago}s ago` : 'N/A'}
            </span>
          </div>
        </div>

        {showRawJson && (
          <pre className="mt-4 p-4 rounded-xl bg-slate-900 text-emerald-400 font-mono text-xs overflow-x-auto max-h-64">
            {JSON.stringify(latestData, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
