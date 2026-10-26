import React, { useState } from 'react';
import { 
  Activity, 
  Sliders, 
  BrainCircuit, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  Droplets, 
  Sun, 
  Thermometer, 
  Gauge, 
  Waves, 
  Save, 
  RotateCcw,
  Sparkles,
  Info,
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';

export default function PlantHealthAnalysis({
  plantStatus,
  anomalies,
  latestData,
  settings,
  onSettingsUpdated
}) {
  const telemetry = latestData?.data;
  const currentSoilV = telemetry?.soil_voltage_v;

  // Calibration Form State
  const [dryV, setDryV] = useState(settings?.soil_dry_voltage ?? 2.65);
  const [wetV, setWetV] = useState(settings?.soil_wet_voltage ?? 1.20);
  const [invert, setInvert] = useState(settings?.soil_invert ?? 1);
  const [isSavingCalib, setIsSavingCalib] = useState(false);
  const [calibMessage, setCalibMessage] = useState(null);

  // Live preview relative moisture
  const previewMoisture = () => {
    if (currentSoilV === null || currentSoilV === undefined) return null;
    const dry = parseFloat(dryV);
    const wet = parseFloat(wetV);
    if (Math.abs(dry - wet) < 0.1) return null;

    let pct;
    if (invert == 1) {
      pct = ((dry - currentSoilV) / (dry - wet)) * 100.0;
    } else {
      pct = ((currentSoilV - dry) / (wet - dry)) * 100.0;
    }
    return Math.round(Math.max(0, Math.min(100, pct)));
  };

  const currentPreviewPct = previewMoisture();

  const handleSaveCalibration = async () => {
    setIsSavingCalib(true);
    setCalibMessage(null);
    try {
      await api.updateSettings({
        soil_dry_voltage: parseFloat(dryV),
        soil_wet_voltage: parseFloat(wetV),
        soil_invert: parseInt(invert, 10),
      });
      setCalibMessage({ type: 'success', text: 'Soil calibration successfully saved to database!' });
      if (onSettingsUpdated) onSettingsUpdated();
    } catch (err) {
      setCalibMessage({ type: 'error', text: `Failed to save calibration: ${err.message}` });
    } finally {
      setIsSavingCalib(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Agronomic Diagnostic Summary */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center font-bold">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Explainable Plant Health Analysis</h2>
            <p className="text-xs text-slate-500">
              Rule-based agronomic physiological assessment paired with environmental heuristics.
            </p>
          </div>
        </div>

        {/* Diagnosis Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          {/* Soil Diagnostic */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Droplets className="w-4 h-4 text-emerald-700" /> Soil Moisture Condition
              </span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                plantStatus?.diagnostics?.soil?.severity === 'critical' ? 'bg-rose-100 text-rose-800' :
                plantStatus?.diagnostics?.soil?.severity === 'warning' ? 'bg-amber-100 text-amber-800' :
                'bg-emerald-100 text-emerald-800'
              }`}>
                {plantStatus?.diagnostics?.soil?.status || 'Analyzing'}
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {plantStatus?.diagnostics?.soil?.detail || 'Waiting for soil moisture sensor reading.'}
            </p>
          </div>

          {/* Temperature Diagnostic */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-rose-600" /> Temperature & Climate
              </span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                plantStatus?.diagnostics?.temperature?.severity === 'critical' ? 'bg-rose-100 text-rose-800' :
                plantStatus?.diagnostics?.temperature?.severity === 'warning' ? 'bg-amber-100 text-amber-800' :
                'bg-emerald-100 text-emerald-800'
              }`}>
                {plantStatus?.diagnostics?.temperature?.status || 'Analyzing'}
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {plantStatus?.diagnostics?.temperature?.detail || 'Waiting for temperature sensor reading.'}
            </p>
            <p className="text-[11px] text-slate-500 mt-2 italic border-t border-slate-200/60 pt-1.5">
              {plantStatus?.diagnostics?.temperature?.humidity_note}
            </p>
          </div>

          {/* Light Diagnostic */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Sun className="w-4 h-4 text-amber-600" /> Lighting & Photoperiod
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800">
                {plantStatus?.diagnostics?.light?.status || 'Analyzing'}
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {plantStatus?.diagnostics?.light?.detail || 'Waiting for ambient light reading.'}
            </p>
          </div>

          {/* Barometer & Water Signal */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-800 flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-sky-600" /> Environmental Weather Context
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-100 text-sky-800">
                Atmospheric
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {plantStatus?.diagnostics?.pressure?.detail}
            </p>
            <p className="text-[11px] text-slate-500 mt-2 border-t border-slate-200/60 pt-1.5">
              {plantStatus?.diagnostics?.water_sensor?.detail}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Interactive Soil Moisture Calibration Wizard */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-800 flex items-center justify-center font-bold">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Soil Moisture Sensor Calibration Wizard</h2>
            <p className="text-xs text-slate-500">
              Calibrate raw analog voltage to your specific soil substrate and pot depth.
            </p>
          </div>
        </div>

        <div className="mt-4 bg-amber-50/60 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-900 leading-relaxed">
          <p>
            <strong>Why Calibration is Required:</strong> Analog soil moisture sensors vary by manufacturer, soil composition, and supply voltage. 
            Raw voltage cannot be accurately reported as a percentage without establishing minimum and maximum boundary reference points.
            <em> Note: Relative moisture estimates reflect sensor electrical response, not laboratory soil water potential.</em>
          </p>
        </div>

        {/* Current Live Sensor Reading Callout */}
        <div className="mt-4 p-3.5 rounded-xl bg-slate-100 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-xs text-slate-500 block">Current Live Reading from ADS1115 A2:</span>
            <span className="text-xl font-bold font-mono text-slate-900">
              {currentSoilV !== null && currentSoilV !== undefined ? `${currentSoilV.toFixed(3)} V` : 'No reading available'}
            </span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => currentSoilV && setDryV(currentSoilV.toFixed(3))}
              disabled={!currentSoilV}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 cursor-pointer disabled:opacity-50"
            >
              Set as Dry Voltage
            </button>
            <button
              onClick={() => currentSoilV && setWetV(currentSoilV.toFixed(3))}
              disabled={!currentSoilV}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 cursor-pointer disabled:opacity-50"
            >
              Set as Wet Voltage
            </button>
          </div>
        </div>

        {/* Calibration Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Dry Soil Reference (V)
            </label>
            <input
              type="number"
              step="0.01"
              value={dryV}
              onChange={(e) => setDryV(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 font-mono"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">Typical range: 2.4V - 3.0V</span>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Wet Soil Reference (V)
            </label>
            <input
              type="number"
              step="0.01"
              value={wetV}
              onChange={(e) => setWetV(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 font-mono"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">Typical range: 1.0V - 1.5V</span>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Sensor Direction / Inversion
            </label>
            <select
              value={invert}
              onChange={(e) => setInvert(parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
            >
              <option value={1}>Higher Voltage = Drier Soil (Standard Capacitive)</option>
              <option value={0}>Higher Voltage = Wetter Soil</option>
            </select>
            <span className="text-[11px] text-slate-400 mt-1 block">Matches sensor electronic design</span>
          </div>
        </div>

        {/* Live Calculation Preview */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-600">Calculated Relative Moisture Preview:</span>
            {currentPreviewPct !== null ? (
              <span className="text-lg font-bold font-mono text-emerald-800 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-200">
                {currentPreviewPct}%
              </span>
            ) : (
              <span className="text-xs text-slate-400 italic">Invalid reference values</span>
            )}
          </div>

          <button
            onClick={handleSaveCalibration}
            disabled={isSavingCalib}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-800 text-white hover:bg-emerald-900 transition-all cursor-pointer disabled:opacity-50 shadow-xs self-start sm:self-auto"
          >
            <Save className="w-4 h-4" />
            {isSavingCalib ? 'Saving...' : 'Save Calibration to Database'}
          </button>
        </div>

        {calibMessage && (
          <div className={`mt-3 p-3 rounded-xl text-xs font-semibold ${
            calibMessage.type === 'success' ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' : 'bg-rose-50 text-rose-900 border border-rose-200'
          }`}>
            {calibMessage.text}
          </div>
        )}
      </div>

      {/* 3. Machine Learning Anomaly Detection Panel (Phase 2 Roadmap) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-800 flex items-center justify-center font-bold">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Machine Learning Anomaly Detection (Phase 2)</h2>
              <p className="text-xs text-slate-500">
                Unsupervised Isolation Forest trained on 5-channel multi-sensor feature vectors.
              </p>
            </div>
          </div>

          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
            anomalies?.available 
              ? (anomalies.is_anomaly ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-emerald-100 text-emerald-800 border border-emerald-300')
              : 'bg-slate-100 text-slate-600'
          }`}>
            {anomalies?.available 
              ? (anomalies.is_anomaly ? '⚠️ ML Anomaly Detected' : '✓ ML Normal Telemetry') 
              : 'Model Not Loaded'}
          </span>
        </div>

        <div className="mt-4 text-xs text-slate-700 leading-relaxed space-y-2">
          <p>
            <strong>Model Architecture & Scope:</strong> Scikit-learn's <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-900 font-mono">IsolationForest</code> isolates sensor anomalies by constructing random decision trees over feature vectors <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-900 font-mono">[soil_voltage_v, light_voltage_v, temperature_c, pressure_hpa, water_voltage_v]</code>.
          </p>
          <p className="text-slate-500 italic">
            Limitations: ML anomaly flags indicate unusual sensor correlation or rapid drifts (e.g. sensor dislodgement, wire disconnection, or acute thermal shock). It does <strong>not</strong> substitute for agronomic pathology or diagnose specific diseases.
          </p>
        </div>

        {anomalies?.available ? (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Anomaly Decision Score</span>
              <span className="text-base font-mono font-bold text-slate-900">
                {anomalies.anomaly_score !== null ? anomalies.anomaly_score : 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Negative = Outlier, Positive = Inlier</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Model Version & Type</span>
              <span className="text-base font-semibold text-slate-900">
                {anomalies.model_info?.model_type || 'IsolationForest'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">v{anomalies.model_info?.version || '1.0'}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Training Telemetry Samples</span>
              <span className="text-base font-mono font-bold text-slate-900">
                {anomalies.model_info?.training_samples || 'N/A'}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">Historical readings</span>
            </div>
          </div>
        ) : (
          <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <p className="font-semibold text-slate-800">Model Training Command:</p>
            <p className="mt-1">
              To retrain or initialize the anomaly detector with your latest gathered readings, run:
            </p>
            <pre className="mt-2 p-2 rounded-lg bg-slate-900 text-emerald-400 font-mono text-xs">
              python ml/train_anomaly_model.py
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
