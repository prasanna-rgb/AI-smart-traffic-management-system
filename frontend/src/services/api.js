import axios from 'axios';

const API_BASE_URL = '/api/traffic';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchIntersections = async () => {
  const res = await api.get('/intersections');
  return res.data;
};

export const fetchPredictions = async (code = 'INT-01') => {
  const res = await api.get(`/predictions?code=${code}`);
  return res.data;
};

export const fetchEmissions = async (code = 'INT-01') => {
  const res = await api.get(`/emissions?code=${code}`);
  return res.data;
};

export const triggerEmergency = async (intersectionCode, active = true, vehicleType = 'AMBULANCE') => {
  const res = await api.post('/emergency/trigger', {
    intersection_code: intersectionCode,
    active,
    vehicle_type: vehicleType,
  });
  return res.data;
};

export const overrideSignal = async (intersectionCode, mode, phase, nsTimer, ewTimer) => {
  const res = await api.post('/signals/override', {
    intersection_code: intersectionCode,
    signal_mode: mode,
    active_phase: phase,
    ns_green_timer: nsTimer,
    ew_green_timer: ewTimer,
  });
  return res.data;
};

export const fetchDecisionLogs = async (limit = 20) => {
  const res = await api.get(`/decision-logs?limit=${limit}`);
  return res.data;
};

export const runCrewPipeline = async (telemetry) => {
  const res = await api.post('/run-crew', telemetry);
  return res.data;
};

export const setStreamSource = async (source) => {
  const res = await api.post('/stream/source', { source });
  return res.data;
};

export default api;
