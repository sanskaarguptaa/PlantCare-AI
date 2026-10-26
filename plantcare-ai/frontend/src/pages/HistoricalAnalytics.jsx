import React, { useState } from 'react';
import { 
  LineChart as ChartIcon, 
  Download, 
  Calendar, 
  Filter, 
  Droplets, 
  Sun, 
  Thermometer, 
  Gauge, 
  Waves,
  Info
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { api } from '../services/api';

export default function HistoricalAnalytics({
  historyData,
  activeRange,
  onChangeRange,
  isLoadingHistory,
  analyticsSummary
}) {
  const [selectedMetric, setSelectedMetric] = useState('all');

  const readings = historyData?.readings || [];

  // Prepare chart data with friendly timestamp formatting
  const chartData = readings.map((r) => {
    const d = r.created_at ? new Date(r.created_at) : null;
    const timeLabel = d 
      ? (activeRange === '7d' || activeRange === 'all' 
          ? d.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit' })
          : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
      : '';

    return {
      timestamp: timeLabel,
      fullTime: d ? d.toLocaleString() : '',
      soil_voltage: r.soil_voltage_v,
      light_voltage: r.light_voltage_v,
      temperature: r.temperature_c,
      pressure: r.pressure_hpa,
      water_voltage: r.water_voltage_v,
    };
  });

  const ranges = [
    { id: '1h', label: 'Last 1 Hour' },
    { id: '24h', label: 'Last 24 Hours' },
    { id: '7d', label: 'Last 7 Days' },
    { id: 'all', label: 'All Cached History' },
  ];

  const metricsConfig = {
    soil: { label: 'Soil Moisture Voltage', unit: 'V', color: '#2d6a4f', dataKey: 'soil_voltage', icon: Droplets },
    light: { label: 'Light Voltage', unit: 'V', color: '#d97706', dataKey: 'light_voltage', icon: Sun },
    temp: { label: 'BMP280 Temperature', unit: '°C', color: '#e11d48', dataKey: 'temperature', icon: Thermometer },
    pressure: { label: 'BMP280 Pressure', unit: 'hPa', color: '#0284c7', dataKey: 'pressure', icon: Gauge },
    water: { label: 'Water Sensor Voltage', unit: 'V', color: '#0d9488', dataKey: 'water_voltage', icon: Waves },
  };

  const handleExportCsv = () => {
    const url = api.getExportCsvUrl(activeRange);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* 1. Filter Controls & CSV Export Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Time range selector */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5 mr-1">
            <Calendar className="w-3.5 h-3.5" /> Time Range:
          </span>
          <div className="flex bg-slate-100 p-1 rounded-xl gap-1">
            {ranges.map((r) => (
              <button
                key={r.id}
                onClick={() => onChangeRange(r.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  activeRange === r.id
                    ? 'bg-white text-emerald-900 font-bold shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* CSV Download Button */}
        <button
          onClick={handleExportCsv}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-800 text-white hover:bg-emerald-900 active:scale-95 transition-all shadow-xs cursor-pointer self-start md:self-auto"
        >
          <Download className="w-3.5 h-3.5" />
          Download Filtered CSV
        </button>
      </div>

      {/* 2. Summary Statistics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {Object.entries(metricsConfig).map(([key, config]) => {
          const summaryMetricKey = 
            key === 'soil' ? 'soil_voltage_v' :
            key === 'light' ? 'light_voltage_v' :
            key === 'temp' ? 'temperature_c' :
            key === 'pressure' ? 'pressure_hpa' : 'water_voltage_v';

          const stats = analyticsSummary?.metrics?.[summaryMetricKey];
          const Icon = config.icon;

          return (
            <div key={key} className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-2xs">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <Icon className="w-3.5 h-3.5" style={{ color: config.color }} />
                <span className="font-semibold text-slate-700 truncate">{config.label}</span>
              </div>
              <div className="flex items-baseline gap-1 mt-1 font-mono">
                <span className="text-lg font-bold text-slate-900">
                  {stats?.latest ?? '--'}
                </span>
                <span className="text-[10px] text-slate-400 font-sans">{config.unit}</span>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 grid grid-cols-3 gap-1 text-[10px] text-slate-500 font-mono">
                <div>
                  <span className="text-slate-400 block text-[9px]">MIN</span>
                  {stats?.min ?? '--'}
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px]">AVG</span>
                  {stats?.avg ?? '--'}
                </div>
                <div>
                  <span className="text-slate-400 block text-[9px]">MAX</span>
                  {stats?.max ?? '--'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Metric Focus Selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-slate-400 font-medium">Chart View:</span>
        <button
          onClick={() => setSelectedMetric('all')}
          className={`px-3 py-1.5 rounded-lg font-medium cursor-pointer transition-all ${
            selectedMetric === 'all'
              ? 'bg-emerald-800 text-white font-semibold'
              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          All Metrics (Normalized)
        </button>
        {Object.entries(metricsConfig).map(([key, config]) => (
          <button
            key={key}
            onClick={() => setSelectedMetric(key)}
            className={`px-3 py-1.5 rounded-lg font-medium cursor-pointer transition-all whitespace-nowrap ${
              selectedMetric === key
                ? 'bg-emerald-800 text-white font-semibold'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {config.label}
          </button>
        ))}
      </div>

      {/* 4. Main Interactive Time-Series Chart */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {selectedMetric === 'all' 
                ? 'Multi-Sensor Environmental Telemetry' 
                : metricsConfig[selectedMetric]?.label}
            </h3>
            <p className="text-xs text-slate-400">
              {readings.length} readings retrieved • Source: {historyData?.data_source || 'cached'}
            </p>
          </div>
          {isLoadingHistory && (
            <span className="text-xs text-emerald-700 animate-pulse font-medium">
              Updating historical dataset...
            </span>
          )}
        </div>

        <div className="h-80 sm:h-96 mt-4">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis 
                  dataKey="timestamp" 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  angle={-20}
                  textAnchor="end"
                  height={45}
                />
                <YAxis 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  domain={['auto', 'auto']}
                />
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-md text-xs">
                          <p className="font-semibold text-slate-800 mb-1 border-b pb-1">
                            {payload[0]?.payload?.fullTime || label}
                          </p>
                          {payload.map((entry, idx) => (
                            <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
                              <span className="flex items-center gap-1.5" style={{ color: entry.color }}>
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></span>
                                {entry.name}:
                              </span>
                              <span className="font-mono font-bold text-slate-900">
                                {typeof entry.value === 'number' ? entry.value.toFixed(3) : entry.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

                {/* Render lines based on selected metric */}
                {(selectedMetric === 'all' || selectedMetric === 'soil') && (
                  <Line 
                    type="monotone" 
                    dataKey="soil_voltage" 
                    name="Soil Voltage (V)" 
                    stroke={metricsConfig.soil.color} 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'light') && (
                  <Line 
                    type="monotone" 
                    dataKey="light_voltage" 
                    name="Light Voltage (V)" 
                    stroke={metricsConfig.light.color} 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'temp') && (
                  <Line 
                    type="monotone" 
                    dataKey="temperature" 
                    name="Temperature (°C)" 
                    stroke={metricsConfig.temp.color} 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'pressure') && (
                  <Line 
                    type="monotone" 
                    dataKey="pressure" 
                    name="Pressure (hPa)" 
                    stroke={metricsConfig.pressure.color} 
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'water') && (
                  <Line 
                    type="monotone" 
                    dataKey="water_voltage" 
                    name="Water Trace (V)" 
                    stroke={metricsConfig.water.color} 
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
              <Info className="w-8 h-8 mb-2 text-slate-300" />
              <p>No historical telemetry available for this range.</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Data accumulates automatically as your Raspberry Pi collector uploads to ThingSpeak.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
