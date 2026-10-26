import React from 'react';
import { 
  Cloud, 
  Cpu, 
  Server, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Info,
  Terminal,
  ZapOff
} from 'lucide-react';

export default function CloudHardwareStatus({ cloudStatus, latestData }) {
  const isConfigured = cloudStatus?.configured;
  const channelId = cloudStatus?.channel_id;
  const hasReadKey = cloudStatus?.has_read_key;
  const demoMode = cloudStatus?.demo_mode;
  const lastStatusCode = cloudStatus?.last_status_code;
  const lastError = cloudStatus?.last_error;
  const consecutiveFailures = cloudStatus?.consecutive_failures ?? 0;

  return (
    <div className="space-y-6">
      {/* 1. ThingSpeak Cloud Integration Diagnostic */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-800 flex items-center justify-center font-bold">
              <Cloud className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">ThingSpeak Cloud Diagnostic</h2>
              <p className="text-xs text-slate-500">
                REST API channel integration, rate-limit safeguards, and credential state.
              </p>
            </div>
          </div>

          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
            isConfigured 
              ? (consecutiveFailures > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800')
              : 'bg-rose-100 text-rose-800'
          }`}>
            {isConfigured 
              ? (consecutiveFailures > 0 ? '⚠️ Cloud Degraded' : '✓ Connected') 
              : '🔴 Unconfigured'}
          </span>
        </div>

        {/* Cloud Diagnostics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[11px] text-slate-400 block font-medium">Channel ID</span>
            <span className="text-sm font-bold font-mono text-slate-800 mt-0.5 block">
              {channelId || 'Not Configured'}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">Public or Private Channel</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[11px] text-slate-400 block font-medium">Read API Key</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              {hasReadKey ? (
                <>
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-semibold text-emerald-800">Present (Masked)</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-4 h-4 text-slate-400" />
                  <span className="text-xs text-slate-500">Public Channel Mode</span>
                </>
              )}
            </div>
            <span className="text-[10px] text-slate-400 mt-1 block">Never exposed to frontend</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[11px] text-slate-400 block font-medium">Cache TTL Guard</span>
            <span className="text-sm font-bold font-mono text-slate-800 mt-0.5 block">
              {cloudStatus?.cache_ttl_seconds || 20} Seconds
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">Protects against rate limits</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[11px] text-slate-400 block font-medium">Last HTTP Response</span>
            <span className={`text-sm font-bold font-mono mt-0.5 block ${
              lastStatusCode === 200 ? 'text-emerald-700' : 'text-slate-700'
            }`}>
              {lastStatusCode ? `HTTP ${lastStatusCode}` : 'No requests yet'}
            </span>
            <span className="text-[10px] text-slate-400 mt-1 block">
              {consecutiveFailures > 0 ? `${consecutiveFailures} failures` : 'Clean responses'}
            </span>
          </div>
        </div>

        {lastError && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <strong className="block font-semibold">Latest Backend Warning:</strong>
              {lastError}
            </div>
          </div>
        )}

        {/* ThingSpeak Private View Verification Instructions */}
        <div className="mt-5 p-4 rounded-xl bg-sky-50/60 border border-sky-200 text-xs text-sky-950 space-y-2">
          <div className="flex items-center gap-2 font-bold text-sky-900">
            <ExternalLink className="w-4 h-4 text-sky-700" />
            How to verify your channel on ThingSpeak:
          </div>
          <ol className="list-decimal list-inside space-y-1 text-sky-900/90 pl-1">
            <li>Log into <a href="https://thingspeak.mathworks.com/" target="_blank" rel="noreferrer" className="underline font-semibold hover:text-sky-950">ThingSpeak.com</a> and click on your Channel.</li>
            <li>In <strong>Private View</strong>, you should see charts updating for Field 1 (Soil), Field 2 (Light), Field 3 (Temperature), Field 4 (Pressure), and Field 5 (Water).</li>
            <li>Check <strong>Channel Settings</strong> to verify that Fields 1 through 5 are enabled.</li>
            <li>Go to <strong>API Keys</strong> tab. If your channel is private, copy the <em>Read API Key</em> into your <code className="bg-white/80 px-1 py-0.5 rounded font-mono">.env</code> file.</li>
          </ol>
        </div>
      </div>

      {/* 2. Raspberry Pi Hardware Configuration */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center font-bold">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Raspberry Pi Hardware Architecture</h2>
            <p className="text-xs text-slate-500">
              Raspberry Pi 3 Model B • Raspbian GNU/Linux 13 (Trixie) • I²C Bus #1
            </p>
          </div>
        </div>

        {/* Hardware Mapping Table */}
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[10px]">
                <th className="py-2.5 px-3">Physical Sensor</th>
                <th className="py-2.5 px-3">Interface / Pin</th>
                <th className="py-2.5 px-3">I²C Address</th>
                <th className="py-2.5 px-3">ThingSpeak Field</th>
                <th className="py-2.5 px-3">Measurement Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-slate-700">
              <tr>
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">Analog Soil Moisture</td>
                <td className="py-2.5 px-3">ADS1115 Pin A2</td>
                <td className="py-2.5 px-3">0x48</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold">Field 1</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Soil moisture voltage (V)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">Analog Light Sensor</td>
                <td className="py-2.5 px-3">ADS1115 Pin A1</td>
                <td className="py-2.5 px-3">0x48</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold">Field 2</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Light intensity voltage (V)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">BMP280 Temperature</td>
                <td className="py-2.5 px-3">I2C SDA (Pin 3) / SCL (Pin 5)</td>
                <td className="py-2.5 px-3">0x76</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold">Field 3</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Ambient temperature (°C)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">BMP280 Barometer</td>
                <td className="py-2.5 px-3">I2C SDA (Pin 3) / SCL (Pin 5)</td>
                <td className="py-2.5 px-3">0x76</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold">Field 4</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Barometric pressure (hPa)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">Water / Rain Trace</td>
                <td className="py-2.5 px-3">ADS1115 Pin A0</td>
                <td className="py-2.5 px-3">0x48</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold">Field 5</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Raw water sensor voltage (V)</td>
              </tr>
              <tr className="bg-slate-50/50">
                <td className="py-2.5 px-3 font-sans text-slate-400">ADS1115 Channel A3</td>
                <td className="py-2.5 px-3 text-slate-400">Pin A3</td>
                <td className="py-2.5 px-3 text-slate-400">0x48</td>
                <td className="py-2.5 px-3 text-slate-400">--</td>
                <td className="py-2.5 px-3 font-sans text-slate-400 italic">Unused / Reserved</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Pump Safety Status Block */}
        <div className="mt-5 p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 space-y-2">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <ZapOff className="w-4 h-4 text-amber-700" />
            Water Pump Status: DISCONNECTED (Safety Enforced)
          </div>
          <p className="leading-relaxed">
            The water pump is intentionally not connected because a dedicated motor driver module (such as an L298N, MOSFET driver, or optocoupled relay) is required to supply high motor current. 
            Connecting inductive DC motors directly to Raspberry Pi GPIO pins can permanently damage the processor.
          </p>
          <p className="text-amber-800 italic">
            Until a suitable driver is installed, PlantCare AI operates exclusively in advisory mode and presents watering recommendations for manual care.
          </p>
        </div>
      </div>
    </div>
  );
}
