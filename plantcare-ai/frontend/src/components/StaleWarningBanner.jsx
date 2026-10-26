import React from 'react';
import { AlertTriangle, Clock, Info, ShieldAlert, Sparkles, ExternalLink } from 'lucide-react';

export default function StaleWarningBanner({ 
  latestData, 
  cloudStatus, 
  onGoToSettings,
  onGoToCloud
}) {
  const dataSource = latestData?.data_source;
  const isStale = latestData?.freshness?.is_stale;
  const secondsAgo = latestData?.freshness?.seconds_ago;
  const cloudError = latestData?.cloud_error || cloudStatus?.last_error;

  return (
    <div className="space-y-2 mb-6">
      {/* 1. Demo Mode Banner */}
      {dataSource === 'demo' && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-3.5 flex items-start gap-3 text-purple-900 shadow-xs">
          <Sparkles className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs sm:text-sm">
            <span className="font-semibold text-purple-950">Active Demo Mode: </span>
            The dashboard is currently running in simulation mode. Readings are synthesized to demonstrate interface functionality, charts, alerts, and ML anomaly evaluation.
            <button 
              onClick={onGoToSettings}
              className="ml-2 underline font-semibold text-purple-800 hover:text-purple-950 cursor-pointer"
            >
              Configure Real Cloud Keys in Settings →
            </button>
          </div>
        </div>
      )}

      {/* 2. Stale Telemetry Warning */}
      {dataSource !== 'demo' && isStale && latestData?.data && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex items-start gap-3 text-amber-900 shadow-xs">
          <Clock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs sm:text-sm">
            <span className="font-semibold text-amber-950">Stale Telemetry Notice: </span>
            The most recent reading was received{' '}
            {secondsAgo ? `${Math.round(secondsAgo / 60)} minutes ago` : 'some time ago'}. 
            Your Raspberry Pi collector may be idle, rebooting, or experiencing network latency.
            <button 
              onClick={onGoToCloud}
              className="ml-2 underline font-semibold text-amber-800 hover:text-amber-950 cursor-pointer"
            >
              Inspect Cloud Diagnostics →
            </button>
          </div>
        </div>
      )}

      {/* 3. Cloud Error or Unconfigured Channel */}
      {dataSource === 'none' && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 flex items-start gap-3 text-rose-900 shadow-xs">
          <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs sm:text-sm">
            <span className="font-semibold text-rose-950">Cloud Access Unavailable: </span>
            {cloudError || 'No sensor readings could be fetched from ThingSpeak. Please verify your Channel ID and Read API Key.'}
            <button 
              onClick={onGoToCloud}
              className="ml-2 underline font-semibold text-rose-800 hover:text-rose-950 cursor-pointer"
            >
              View Setup Instructions →
            </button>
          </div>
        </div>
      )}

      {/* 4. Water Pump Status Notice (Persistent agronomic reminder) */}
      <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-2.5 px-3 flex items-center justify-between text-xs text-emerald-900">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-emerald-700 shrink-0" />
          <span>
            <strong>Hardware Safety Guard:</strong> Physical water pump is <em>not connected</em> (no motor driver). Recommendations are informational only.
          </span>
        </div>
        <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md hidden md:inline-block">
          Manual Care Only
        </span>
      </div>
    </div>
  );
}
