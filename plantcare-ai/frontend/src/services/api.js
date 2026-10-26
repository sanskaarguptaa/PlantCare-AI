/**
 * PlantCare AI - Unified Frontend API Client
 * Interfaces with the Flask backend REST API with safe error handling.
 */

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api';

async function fetchJson(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      const message = errorBody.message || `HTTP ${res.status}: ${res.statusText}`;
      const error = new Error(message);
      error.status = res.status;
      error.data = errorBody;
      throw error;
    }

    return await res.json();
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'} ${url}]:`, err.message);
    throw err;
  }
}

export const api = {
  // System Health & Cloud Diagnostics
  getHealth: () => fetchJson(`${API_BASE}/health`),
  getCloudStatus: () => fetchJson(`${API_BASE}/status/cloud`),

  // Sensor Telemetry
  getLatestSensorData: (force = false) => fetchJson(`${API_BASE}/sensors/latest?force=${force}`),
  getSensorHistory: (range = '24h', limit = 100) => 
    fetchJson(`${API_BASE}/sensors/history?range=${encodeURIComponent(range)}&limit=${limit}`),

  // Agronomic Analytics & ML
  getAnalyticsSummary: () => fetchJson(`${API_BASE}/analytics/summary`),
  getPlantStatus: () => fetchJson(`${API_BASE}/analytics/plant-status`),
  getAnomalies: () => fetchJson(`${API_BASE}/analytics/anomalies`),

  // Alerts Management
  getAlerts: (unresolvedOnly = false) => 
    fetchJson(`${API_BASE}/alerts?unresolved=${unresolvedOnly}`),
  resolveAlert: (id) => 
    fetchJson(`${API_BASE}/alerts/${id}/resolve`, { method: 'POST' }),

  // Settings & Calibration
  getSettings: () => fetchJson(`${API_BASE}/settings`),
  updateSettings: (payload) => 
    fetchJson(`${API_BASE}/settings`, { method: 'PUT', body: JSON.stringify(payload) }),
  toggleDemo: (enabled = null) => 
    fetchJson(`${API_BASE}/demo/toggle`, { 
      method: 'POST', 
      body: JSON.stringify(enabled !== null ? { enabled } : {}) 
    }),

  // CSV Export URL helper
  getExportCsvUrl: (range = '24h') => `${API_BASE}/export/csv?range=${encodeURIComponent(range)}`,
};
