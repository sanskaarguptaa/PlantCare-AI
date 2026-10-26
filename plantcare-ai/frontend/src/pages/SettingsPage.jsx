import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Save, 
  Sparkles, 
  Thermometer, 
  Droplets, 
  Sprout, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage({ settings, onSettingsUpdated }) {
  const [formData, setFormData] = useState({
    plant_name: '',
    plant_type: '',
    temp_unit: 'C',
    temp_min_c: 18.0,
    temp_max_c: 28.0,
    soil_dry_voltage: 2.65,
    soil_wet_voltage: 1.20,
    soil_invert: 1,
    water_sensor_alert_threshold: 0.80,
    dashboard_refresh_sec: 30,
    demo_mode: 0,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    if (settings) {
      setFormData({
        plant_name: settings.plant_name || 'Monstera Deliciosa',
        plant_type: settings.plant_type || 'Indoor Tropical Houseplant',
        temp_unit: settings.temp_unit || 'C',
        temp_min_c: settings.temp_min_c ?? 18.0,
        temp_max_c: settings.temp_max_c ?? 28.0,
        soil_dry_voltage: settings.soil_dry_voltage ?? 2.65,
        soil_wet_voltage: settings.soil_wet_voltage ?? 1.20,
        soil_invert: settings.soil_invert ?? 1,
        water_sensor_alert_threshold: settings.water_sensor_alert_threshold ?? 0.80,
        dashboard_refresh_sec: settings.dashboard_refresh_sec ?? 30,
        demo_mode: settings.demo_mode ?? 0,
      });
    }
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    // Validation
    const refreshSec = parseInt(formData.dashboard_refresh_sec, 10);
    if (refreshSec < 15) {
      setFeedback({ 
        type: 'error', 
        text: 'Dashboard refresh interval must be at least 15 seconds to respect ThingSpeak rate limits.' 
      });
      setIsSaving(false);
      return;
    }

    try {
      await api.updateSettings({
        plant_name: formData.plant_name.trim(),
        plant_type: formData.plant_type.trim(),
        temp_unit: formData.temp_unit,
        temp_min_c: parseFloat(formData.temp_min_c),
        temp_max_c: parseFloat(formData.temp_max_c),
        soil_dry_voltage: parseFloat(formData.soil_dry_voltage),
        soil_wet_voltage: parseFloat(formData.soil_wet_voltage),
        soil_invert: parseInt(formData.soil_invert, 10),
        water_sensor_alert_threshold: parseFloat(formData.water_sensor_alert_threshold),
        dashboard_refresh_sec: refreshSec,
        demo_mode: parseInt(formData.demo_mode, 10),
      });

      setFeedback({ type: 'success', text: 'Settings successfully saved and persisted!' });
      if (onSettingsUpdated) onSettingsUpdated();
    } catch (err) {
      setFeedback({ type: 'error', text: `Failed to save settings: ${err.message}` });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Top Header Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center font-bold">
              <Settings className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Application & Sensor Settings</h2>
              <p className="text-xs text-slate-500">
                Configure plant profiles, physiological thresholds, and polling frequencies.
              </p>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-800 text-white hover:bg-emerald-900 transition-all cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>

        {feedback && (
          <div className={`p-4 rounded-xl text-xs font-semibold flex items-center gap-2 ${
            feedback.type === 'success' 
              ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' 
              : 'bg-rose-50 text-rose-900 border border-rose-200'
          }`}>
            {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-rose-600" />}
            {feedback.text}
          </div>
        )}

        {/* Section 1: Plant Profile */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
            <Sprout className="w-4 h-4 text-emerald-700" />
            <span>Plant Profile</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Plant Nickname</label>
              <input
                type="text"
                value={formData.plant_name}
                onChange={(e) => handleChange('plant_name', e.target.value)}
                placeholder="e.g. Living Room Monstera"
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Plant Species / Variety</label>
              <input
                type="text"
                value={formData.plant_type}
                onChange={(e) => handleChange('plant_type', e.target.value)}
                placeholder="e.g. Ficus lyrata or Tomato"
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Temperature Limits & Display */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
            <Thermometer className="w-4 h-4 text-rose-600" />
            <span>Temperature Comfort Thresholds (BMP280)</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Minimum Safe Temp (°C)</label>
              <input
                type="number"
                step="0.5"
                value={formData.temp_min_c}
                onChange={(e) => handleChange('temp_min_c', e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Triggers cold stress alert</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Maximum Safe Temp (°C)</label>
              <input
                type="number"
                step="0.5"
                value={formData.temp_max_c}
                onChange={(e) => handleChange('temp_max_c', e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Triggers heat stress alert</span>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Preferred Display Unit</label>
              <select
                value={formData.temp_unit}
                onChange={(e) => handleChange('temp_unit', e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
              >
                <option value="C">Celsius (°C)</option>
                <option value="F">Fahrenheit (°F)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Telemetry Refresh & Simulation Controls */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
            <Clock className="w-4 h-4 text-sky-600" />
            <span>Polling Intervals & Demo Simulation Mode</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Dashboard Auto-Refresh Rate (seconds)
              </label>
              <input
                type="number"
                min="15"
                step="5"
                value={formData.dashboard_refresh_sec}
                onChange={(e) => handleChange('dashboard_refresh_sec', e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Recommended: 20-30s. Must be ≥ 15s to respect ThingSpeak rate limit.
              </span>
            </div>

            <div className="p-3.5 rounded-xl border border-purple-200 bg-purple-50/60">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-purple-900 block flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" /> Demo Simulation Mode
                  </span>
                  <span className="text-[11px] text-purple-700 mt-0.5 block">
                    Synthesizes realistic data for testing when offline.
                  </span>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.demo_mode == 1}
                    onChange={(e) => handleChange('demo_mode', e.target.checked ? 1 : 0)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
