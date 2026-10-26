import React from 'react';
import { 
  Droplets, 
  Sun, 
  Thermometer, 
  Gauge, 
  Waves, 
  CheckCircle2, 
  AlertTriangle, 
  AlertCircle, 
  ArrowUpRight, 
  ArrowDownRight, 
  Minus, 
  Sparkles,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Info
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export default function DashboardOverview({
  latestData,
  plantStatus,
  analyticsSummary,
  historyData,
  alerts,
  onResolveAlert,
  onNavigateTab,
  settings
}) {
  const telemetry = latestData?.data;
  const tempUnit = settings?.temp_unit || 'C';

  // Helper to convert C to F if needed
  const formatTemp = (celsius) => {
    if (celsius === null || celsius === undefined) return '--';
    if (tempUnit === 'F') {
      return `${((celsius * 9/5) + 32).toFixed(1)} °F`;
    }
    return `${celsius.toFixed(1)} °C`;
  };

  // Trend icon helper
  const renderTrend = (metricKey) => {
    const trend = analyticsSummary?.metrics?.[metricKey]?.trend;
    if (trend === 'rising') {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-emerald-600 gap-0.5">
          <ArrowUpRight className="w-3.5 h-3.5" /> Rising
        </span>
      );
    }
    if (trend === 'falling') {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-amber-600 gap-0.5">
          <ArrowDownRight className="w-3.5 h-3.5" /> Falling
        </span>
      );
    }
    return (
      <span className="inline-flex items-center text-xs font-medium text-slate-400 gap-0.5">
        <Minus className="w-3.5 h-3.5" /> Stable
      </span>
    );
  };

  // Status visual styles
  const getStatusStyles = (statusCode) => {
    switch (statusCode) {
      case 'critical':
        return {
          bg: 'bg-rose-50 border-rose-200',
          badge: 'bg-rose-600 text-white',
          text: 'text-rose-950',
          icon: AlertCircle,
          iconColor: 'text-rose-600'
        };
      case 'needs_attention':
        return {
          bg: 'bg-amber-50 border-amber-200',
          badge: 'bg-amber-500 text-white',
          text: 'text-amber-950',
          icon: AlertTriangle,
          iconColor: 'text-amber-600'
        };
      default:
        return {
          bg: 'bg-emerald-50/80 border-emerald-200',
          badge: 'bg-emerald-700 text-white',
          text: 'text-emerald-950',
          icon: CheckCircle2,
          iconColor: 'text-emerald-600'
        };
    }
  };

  const statusStyle = getStatusStyles(plantStatus?.status_code);
  const StatusIcon = statusStyle.icon;

  // Mini chart data: last 15 readings
  const miniChartData = (historyData?.readings || []).slice(-20).map((r, idx) => ({
    time: r.created_at ? new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : `${idx}`,
    soil: r.soil_voltage_v,
    temp: r.temperature_c
  }));

  const unresolvedAlerts = (alerts || []).filter(a => !a.resolved);

  return (
    <div className="space-y-6">
      {/* 1. Plant Vitality Status Hero Card */}
      <div className={`rounded-2xl border p-5 sm:p-6 transition-all shadow-xs ${statusStyle.bg}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-white shadow-xs shrink-0">
              <StatusIcon className={`w-8 h-8 ${statusStyle.iconColor}`} />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${statusStyle.badge}`}>
                  {plantStatus?.overall_status || 'Checking...'}
                </span>
                <span className="text-xs text-slate-500">
                  Confidence: {Math.round((plantStatus?.confidence || 0.9) * 100)}%
                </span>
              </div>
              <h2 className={`text-lg sm:text-xl font-bold mt-1 ${statusStyle.text}`}>
                {plantStatus?.explanation || 'Awaiting live sensor telemetry...'}
              </h2>
              <p className="text-xs sm:text-sm text-slate-700 mt-1 max-w-3xl leading-relaxed">
                <strong>Agronomic Advice: </strong>{plantStatus?.recommendation || 'Keep monitoring.'}
              </p>
            </div>
          </div>

          <button
            onClick={() => onNavigateTab('health')}
            className="self-start sm:self-center inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 shadow-2xs hover:shadow-xs transition-all cursor-pointer whitespace-nowrap"
          >
            Detailed Diagnostic
            <ChevronRight className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {plantStatus?.triggering_factors?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200/60 flex items-center gap-2 flex-wrap text-xs text-slate-600">
            <span className="font-semibold text-slate-700">Triggering Factors:</span>
            {plantStatus.triggering_factors.map((f, i) => (
              <span key={i} className="px-2.5 py-0.5 bg-white/80 rounded-md border border-slate-200 text-slate-800">
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 2. Sensor Cards Grid (5 actual hardware sensors) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Soil Moisture */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <Droplets className="w-4 h-4" />
              </div>
              <span className="text-xs font-semibold text-slate-700">Soil Moisture</span>
            </div>
            {renderTrend('soil_voltage_v')}
          </div>
          
          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {telemetry?.soil_voltage_v !== null && telemetry?.soil_voltage_v !== undefined 
                  ? `${telemetry.soil_voltage_v.toFixed(3)}` 
                  : '--'}
              </span>
              <span className="text-xs text-slate-500 font-medium">V (ADC A2)</span>
            </div>

            {telemetry?.soil_calibrated && telemetry?.relative_soil_moisture_pct !== null ? (
              <div className="mt-2">
                <div className="flex justify-between text-xs text-slate-600 mb-1">
                  <span>Relative Moisture</span>
                  <span className="font-bold text-emerald-800">{telemetry.relative_soil_moisture_pct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${
                      telemetry.relative_soil_moisture_pct < 25 ? 'bg-amber-500' : 'bg-emerald-600'
                    }`} 
                    style={{ width: `${telemetry.relative_soil_moisture_pct}%` }}
                  />
                </div>
              </div>
            ) : (
              <button 
                onClick={() => onNavigateTab('health')}
                className="mt-2 text-[11px] font-semibold text-emerald-700 hover:text-emerald-900 underline block cursor-pointer"
              >
                Calibrate relative % →
              </button>
            )}
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>24h Avg: {analyticsSummary?.metrics?.soil_voltage_v?.avg ?? '--'} V</span>
            <span className="text-slate-400">ADS1115</span>
          </div>
        </div>

        {/* Card 2: Light Sensor */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
                <Sun className="w-4 h-4" />
              </div>
              <span className="text-xs font-semibold text-slate-700">Light Sensor</span>
            </div>
            {renderTrend('light_voltage_v')}
          </div>

          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {telemetry?.light_voltage_v !== null && telemetry?.light_voltage_v !== undefined 
                  ? `${telemetry.light_voltage_v.toFixed(3)}` 
                  : '--'}
              </span>
              <span className="text-xs text-slate-500 font-medium">V (ADC A1)</span>
            </div>
            <div className="mt-2 inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
              {plantStatus?.diagnostics?.light?.status || 'Raw Voltage'}
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>24h Max: {analyticsSummary?.metrics?.light_voltage_v?.max ?? '--'} V</span>
            <span className="text-slate-400">Analog AO</span>
          </div>
        </div>

        {/* Card 3: BMP280 Temperature */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-700 flex items-center justify-center">
                <Thermometer className="w-4 h-4" />
              </div>
              <span className="text-xs font-semibold text-slate-700">Temperature</span>
            </div>
            {renderTrend('temperature_c')}
          </div>

          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {formatTemp(telemetry?.temperature_c)}
              </span>
            </div>
            <div className="mt-2 inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
              Target: {settings?.temp_min_c || 18}° - {settings?.temp_max_c || 28}°C
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>BMP280 (0x76)</span>
            <span className="text-[10px] text-slate-400 italic" title="BMP280 does not measure humidity">No Humidity</span>
          </div>
        </div>

        {/* Card 4: BMP280 Pressure */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center">
                <Gauge className="w-4 h-4" />
              </div>
              <span className="text-xs font-semibold text-slate-700">Barometer</span>
            </div>
            {renderTrend('pressure_hpa')}
          </div>

          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {telemetry?.pressure_hpa !== null && telemetry?.pressure_hpa !== undefined 
                  ? `${telemetry.pressure_hpa.toFixed(1)}` 
                  : '--'}
              </span>
              <span className="text-xs text-slate-500 font-medium">hPa</span>
            </div>
            <div className="mt-2 inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-sky-50 text-sky-800 border border-sky-200">
              Atmospheric Trend
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>24h Avg: {analyticsSummary?.metrics?.pressure_hpa?.avg ?? '--'} hPa</span>
            <span className="text-slate-400">Weather</span>
          </div>
        </div>

        {/* Card 5: Water Trace Sensor */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
                <Waves className="w-4 h-4" />
              </div>
              <span className="text-xs font-semibold text-slate-700">Water Sensor</span>
            </div>
            {renderTrend('water_voltage_v')}
          </div>

          <div className="mt-2">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-slate-900 font-mono">
                {telemetry?.water_voltage_v !== null && telemetry?.water_voltage_v !== undefined 
                  ? `${telemetry.water_voltage_v.toFixed(3)}` 
                  : '--'}
              </span>
              <span className="text-xs text-slate-500 font-medium">V (ADC A0)</span>
            </div>
            <div className="mt-2 inline-block px-2 py-0.5 rounded text-[11px] font-medium bg-teal-50 text-teal-800 border border-teal-200">
              {plantStatus?.diagnostics?.water_sensor?.status || 'Raw Signal'}
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="text-[10px] text-slate-400">Raw Trace (Not Tank)</span>
            <span className="text-slate-400">A0</span>
          </div>
        </div>
      </div>

      {/* 3. Bottom Grid: Alerts & Quick Mini-Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alerts Panel */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">Recorded Alerts</h3>
            </div>
            <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              {unresolvedAlerts.length} unresolved
            </span>
          </div>

          <div className="divide-y divide-slate-100 mt-2 max-h-72 overflow-y-auto pr-1">
            {unresolvedAlerts.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                <p className="text-xs font-medium">All environmental thresholds normal</p>
                <p className="text-[11px] text-slate-400 mt-0.5">No unresolved alerts recorded</p>
              </div>
            ) : (
              unresolvedAlerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="py-2.5 flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${alert.severity === 'critical' ? 'bg-rose-500' : 'bg-amber-500'}`}></span>
                      <span className="text-xs font-semibold text-slate-800">{alert.affected_sensor}</span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">{alert.rule}</p>
                    <p className="text-[11px] text-slate-500 italic mt-0.5">{alert.recommendation}</p>
                  </div>
                  <button
                    onClick={() => onResolveAlert(alert.id)}
                    className="shrink-0 text-[11px] font-semibold text-emerald-700 hover:text-emerald-900 px-2 py-1 rounded bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 cursor-pointer"
                  >
                    Resolve
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Trend Mini-Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Recent Telemetry Trend</h3>
              <p className="text-xs text-slate-400">Soil Moisture Voltage & Ambient Temperature</p>
            </div>
            <button
              onClick={() => onNavigateTab('history')}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 inline-flex items-center gap-1 cursor-pointer"
            >
              Full Analytics →
            </button>
          </div>

          <div className="h-56 mt-4">
            {miniChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={miniChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="soilColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2d6a4f" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#2d6a4f" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="tempColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#e11d48" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#e11d48" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="soil" name="Soil Voltage (V)" stroke="#2d6a4f" strokeWidth={2} fillOpacity={1} fill="url(#soilColor)" />
                  <Area type="monotone" dataKey="temp" name="Temperature (°C)" stroke="#e11d48" strokeWidth={2} fillOpacity={1} fill="url(#tempColor)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Awaiting historical telemetry points...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
