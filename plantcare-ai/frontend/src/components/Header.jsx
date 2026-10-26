import React from 'react';
import { 
  Sprout, 
  Activity, 
  LineChart, 
  Cpu, 
  Settings, 
  RefreshCw, 
  Cloud, 
  CloudOff, 
  CheckCircle2, 
  AlertTriangle,
  Radio,
  Sliders
} from 'lucide-react';

export default function Header({
  activeTab,
  setActiveTab,
  latestData,
  isRefreshing,
  onRefresh,
  settings,
  cloudStatus,
  relativeTimeStr
}) {
  const dataSource = latestData?.data_source || 'none';
  const isStale = latestData?.freshness?.is_stale ?? true;

  // Render connection badge
  const renderConnectionBadge = () => {
    if (dataSource === 'demo') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-purple-600 pulse-indicator"></span>
          🟣 Demo Mode (Simulated)
        </span>
      );
    }
    if (dataSource === 'cloud') {
      return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold shadow-xs ${
          isStale 
            ? 'bg-amber-100 text-amber-800 border border-amber-300' 
            : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isStale ? 'bg-amber-500' : 'bg-emerald-500 pulse-indicator'}`}></span>
          {isStale ? '🟡 Cloud (Stale Telemetry)' : '🟢 Live ThingSpeak Cloud'}
        </span>
      );
    }
    if (dataSource === 'cached') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          🟡 Cached Cloud Telemetry
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200 shadow-xs">
        <span className="w-2 h-2 rounded-full bg-rose-500"></span>
        🔴 Cloud Offline / Unconfigured
      </span>
    );
  };

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: Sprout },
    { id: 'diagnostics', label: 'Live Diagnostics', icon: Radio },
    { id: 'history', label: 'History & Trends', icon: LineChart },
    { id: 'health', label: 'Plant Health & AI', icon: Activity },
    { id: 'device', label: 'Cloud & Hardware', icon: Cpu },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
      {/* Top Banner Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3.5 border-b border-slate-100">
          {/* Logo and Plant Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-700 to-teal-800 flex items-center justify-center text-white shadow-md shadow-emerald-900/10">
              <Sprout className="w-6 h-6 text-emerald-200" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900 font-sans">
                  PlantCare <span className="text-emerald-700">AI</span>
                </h1>
                <span className="text-xs px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 font-medium border border-emerald-200 hidden sm:inline-block">
                  IoT Smart Agriculture
                </span>
              </div>
              <p className="text-xs text-slate-500 flex items-center gap-1.5">
                Monitoring: <strong className="text-slate-700">{settings?.plant_name || 'My Plant'}</strong>
                <span className="text-slate-300">•</span>
                <span className="italic">{settings?.plant_type || 'Indoor Houseplant'}</span>
              </p>
            </div>
          </div>

          {/* Right Status & Refresh Controls */}
          <div className="flex items-center gap-3">
            {renderConnectionBadge()}

            <div className="hidden md:flex flex-col text-right">
              <span className="text-[11px] font-medium text-slate-400">Last Synced</span>
              <span className="text-xs font-semibold text-slate-700 font-mono">
                {relativeTimeStr || 'Never'}
              </span>
            </div>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Fetch latest reading from backend"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 active:scale-95 transition-all disabled:opacity-50 cursor-pointer border border-slate-200"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 sm:space-x-3 overflow-x-auto py-2 no-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-emerald-800 text-white shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-200' : 'text-slate-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
