import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import StaleWarningBanner from './components/StaleWarningBanner';
import DashboardOverview from './pages/DashboardOverview';
import LiveDiagnostics from './pages/LiveDiagnostics';
import HistoricalAnalytics from './pages/HistoricalAnalytics';
import PlantHealthAnalysis from './pages/PlantHealthAnalysis';
import CloudHardwareStatus from './pages/CloudHardwareStatus';
import SettingsPage from './pages/SettingsPage';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  // Application Data States
  const [latestData, setLatestData] = useState(null);
  const [plantStatus, setPlantStatus] = useState(null);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [settings, setSettings] = useState(null);
  const [cloudStatus, setCloudStatus] = useState(null);
  const [anomalies, setAnomalies] = useState(null);

  // UI States
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyRange, setHistoryRange] = useState('24h');
  const [countdownSec, setCountdownSec] = useState(30);
  const [relativeTimeStr, setRelativeTimeStr] = useState('');

  const refreshIntervalRef = useRef(30);

  // 1. Fetch settings and initial cloud status
  const loadInitialSettings = useCallback(async () => {
    try {
      const [fetchedSettings, fetchedCloud] = await Promise.all([
        api.getSettings(),
        api.getCloudStatus()
      ]);
      setSettings(fetchedSettings);
      setCloudStatus(fetchedCloud);
      if (fetchedSettings?.dashboard_refresh_sec) {
        refreshIntervalRef.current = Math.max(15, fetchedSettings.dashboard_refresh_sec);
        setCountdownSec(refreshIntervalRef.current);
      }
    } catch (err) {
      console.warn('Initial setup load warning:', err.message);
    }
  }, []);

  // 2. Fetch live sensor telemetry & agronomic status
  const fetchLiveTelemetry = useCallback(async (force = false) => {
    setIsRefreshing(true);
    try {
      const [latest, status, summary, alertsRes, anom] = await Promise.allSettled([
        api.getLatestSensorData(force),
        api.getPlantStatus(),
        api.getAnalyticsSummary(),
        api.getAlerts(false),
        api.getAnomalies()
      ]);

      if (latest.status === 'fulfilled') setLatestData(latest.value);
      if (status.status === 'fulfilled') setPlantStatus(status.value);
      if (summary.status === 'fulfilled') setAnalyticsSummary(summary.value);
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value?.alerts || []);
      if (anom.status === 'fulfilled') setAnomalies(anom.value);

      // Reset countdown timer
      setCountdownSec(refreshIntervalRef.current);
    } catch (err) {
      console.error('Telemetry fetch error:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // 3. Fetch historical data on demand or when range changes
  const fetchHistory = useCallback(async (range) => {
    setIsLoadingHistory(true);
    try {
      const hist = await api.getSensorHistory(range, 200);
      setHistoryData(hist);
    } catch (err) {
      console.error('History fetch error:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  // Initial Boot
  useEffect(() => {
    loadInitialSettings();
    fetchLiveTelemetry(true);
    fetchHistory('24h');
  }, [loadInitialSettings, fetchLiveTelemetry, fetchHistory]);

  // Handle range change in History tab
  const handleRangeChange = (newRange) => {
    setHistoryRange(newRange);
    fetchHistory(newRange);
  };

  // Polling Interval & Countdown Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdownSec((prev) => {
        if (prev <= 1) {
          fetchLiveTelemetry(false);
          return refreshIntervalRef.current;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [fetchLiveTelemetry]);

  // Relative Time String computation
  useEffect(() => {
    const updateTimeStr = () => {
      const ts = latestData?.data?.created_at;
      if (!ts) {
        setRelativeTimeStr('No sync yet');
        return;
      }
      try {
        const d = new Date(ts);
        const elapsedSec = Math.max(0, Math.round((Date.now() - d.getTime()) / 1000));
        if (elapsedSec < 10) setRelativeTimeStr('Just now');
        else if (elapsedSec < 60) setRelativeTimeStr(`${elapsedSec}s ago`);
        else if (elapsedSec < 3600) setRelativeTimeStr(`${Math.round(elapsedSec / 60)}m ago`);
        else setRelativeTimeStr(`${Math.round(elapsedSec / 3600)}h ago`);
      } catch {
        setRelativeTimeStr('Syncing');
      }
    };

    updateTimeStr();
    const interval = setInterval(updateTimeStr, 5000);
    return () => clearInterval(interval);
  }, [latestData]);

  // Resolve alert action
  const handleResolveAlert = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
      setAlerts((prev) => prev.map(a => a.id === alertId ? { ...a, resolved: 1 } : a));
    } catch (err) {
      console.error('Resolve alert error:', err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f7faf8]">
      {/* 1. Responsive Header & Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        latestData={latestData}
        isRefreshing={isRefreshing}
        onRefresh={() => fetchLiveTelemetry(true)}
        settings={settings}
        cloudStatus={cloudStatus}
        relativeTimeStr={relativeTimeStr}
      />

      {/* 2. Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Warning & Stale Banner */}
        <StaleWarningBanner
          latestData={latestData}
          cloudStatus={cloudStatus}
          onGoToSettings={() => setActiveTab('settings')}
          onGoToCloud={() => setActiveTab('device')}
        />

        {/* Tab Views */}
        {activeTab === 'overview' && (
          <DashboardOverview
            latestData={latestData}
            plantStatus={plantStatus}
            analyticsSummary={analyticsSummary}
            historyData={historyData}
            alerts={alerts}
            onResolveAlert={handleResolveAlert}
            onNavigateTab={setActiveTab}
            settings={settings}
          />
        )}

        {activeTab === 'diagnostics' && (
          <LiveDiagnostics
            latestData={latestData}
            cloudStatus={cloudStatus}
            onRefresh={() => fetchLiveTelemetry(true)}
            isRefreshing={isRefreshing}
            countdownSec={countdownSec}
            refreshInterval={refreshIntervalRef.current}
          />
        )}

        {activeTab === 'history' && (
          <HistoricalAnalytics
            historyData={historyData}
            activeRange={historyRange}
            onChangeRange={handleRangeChange}
            isLoadingHistory={isLoadingHistory}
            analyticsSummary={analyticsSummary}
          />
        )}

        {activeTab === 'health' && (
          <PlantHealthAnalysis
            plantStatus={plantStatus}
            anomalies={anomalies}
            latestData={latestData}
            settings={settings}
            onSettingsUpdated={() => {
              loadInitialSettings();
              fetchLiveTelemetry(true);
            }}
          />
        )}

        {activeTab === 'device' && (
          <CloudHardwareStatus
            cloudStatus={cloudStatus}
            latestData={latestData}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsPage
            settings={settings}
            onSettingsUpdated={() => {
              loadInitialSettings();
              fetchLiveTelemetry(true);
            }}
          />
        )}
      </main>

      {/* 3. Minimal Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 mt-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
          <p>
            🌿 <strong>PlantCare AI</strong> — Connected to Raspberry Pi 3 Model B & ThingSpeak Cloud.
          </p>
          <p className="text-slate-400">
            Explainable Agronomic Rules • Scikit-Learn Isolation Forest • Advisory Mode
          </p>
        </div>
      </footer>
    </div>
  );
}
