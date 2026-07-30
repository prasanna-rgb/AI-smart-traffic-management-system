import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LiveVisionFeed from './components/LiveVisionFeed';
import TrafficMetrics from './components/TrafficMetrics';
import PredictionChart from './components/PredictionChart';
import PollutionMonitor from './components/PollutionMonitor';
import EmergencyCorridor from './components/EmergencyCorridor';
import SignalStateView from './components/SignalStateView';
import DecisionLogView from './components/DecisionLogView';
import IntersectionMap from './components/IntersectionMap';
import {
  fetchIntersections,
  fetchPredictions,
  fetchEmissions,
  fetchDecisionLogs,
  runCrewPipeline
} from './services/api';

export default function App() {
  const [intersections, setIntersections] = useState([
    { code: 'INT-01', name: 'Downtown Central Hub (5th & Main)', signal_mode: 'AI_AUTO', active_phase: 'NORTH_SOUTH_GREEN', ns_green_timer: 45, ew_green_timer: 25 },
    { code: 'INT-02', name: 'Broadway Expressway Junction', signal_mode: 'AI_AUTO', active_phase: 'EAST_WEST_GREEN', ns_green_timer: 30, ew_green_timer: 50 },
    { code: 'INT-03', name: 'Hospital Emergency Corridor (Oak St)', signal_mode: 'AI_AUTO', active_phase: 'NORTH_SOUTH_GREEN', ns_green_timer: 60, ew_green_timer: 20 },
    { code: 'INT-04', name: 'Industrial Park & Port Way', signal_mode: 'AI_AUTO', active_phase: 'NORTH_SOUTH_GREEN', ns_green_timer: 35, ew_green_timer: 35 }
  ]);

  const [selectedCode, setSelectedCode] = useState('INT-01');
  const [frameB64, setFrameB64] = useState('');
  const [visionMetrics, setVisionMetrics] = useState({
    car: 14, bus: 2, truck: 1, motorcycle: 5, ambulance: 0,
    total_vehicles: 22, average_speed: 38.5, density_pct: 48.8
  });
  const [predictionData, setPredictionData] = useState(null);
  const [pollutionData, setPollutionData] = useState(null);
  const [decisionLogs, setDecisionLogs] = useState([]);
  const [isCrewRunning, setIsCrewRunning] = useState(false);
  const [activeSource, setActiveSource] = useState('synthetic');

  // WebSocket Subscription
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/traffic`;
    
    let ws;
    try {
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'TELEMETRY_UPDATE') {
            if (data.frame_b64) setFrameB64(data.frame_b64);
            if (data.metrics) setVisionMetrics(data.metrics);
            if (data.intersections && data.intersections.length > 0) {
              setIntersections(data.intersections);
            }
          }
        } catch (err) {
          console.error("Error parsing WS message:", err);
        }
      };

      ws.onerror = (err) => console.log("WebSocket connection info:", err);
    } catch (e) {
      console.log("WebSocket init exception:", e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Poll REST data periodically
  const loadData = async () => {
    try {
      const [nodesRes, predRes, polRes, logsRes] = await Promise.allSettled([
        fetchIntersections(),
        fetchPredictions(selectedCode),
        fetchEmissions(selectedCode),
        fetchDecisionLogs(15)
      ]);

      if (nodesRes.status === 'fulfilled' && nodesRes.value?.intersections) {
        setIntersections(nodesRes.value.intersections);
      }
      if (predRes.status === 'fulfilled' && predRes.value?.prediction) {
        setPredictionData(predRes.value.prediction);
      }
      if (polRes.status === 'fulfilled' && polRes.value?.pollution) {
        setPollutionData(polRes.value.pollution);
      }
      if (logsRes.status === 'fulfilled' && logsRes.value?.decision_logs) {
        setDecisionLogs(logsRes.value.decision_logs);
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, [selectedCode]);

  // Trigger 6-agent CrewAI pipeline
  const handleTriggerCrew = async () => {
    setIsCrewRunning(true);
    try {
      const payload = {
        intersection_code: selectedCode,
        car: visionMetrics?.car || 15,
        bus: visionMetrics?.bus || 2,
        truck: visionMetrics?.truck || 1,
        motorcycle: visionMetrics?.motorcycle || 4,
        ambulance: visionMetrics?.ambulance || 0,
        total_vehicles: visionMetrics?.total_vehicles || 22,
        average_speed: visionMetrics?.average_speed || 38.5,
        emergency_vehicle: (visionMetrics?.ambulance || 0) > 0
      };
      await runCrewPipeline(payload);
      await loadData();
    } catch (err) {
      console.error("Crew execution error:", err);
    } finally {
      setIsCrewRunning(false);
    }
  };

  const selectedNode = intersections.find((n) => n.code === selectedCode) || intersections[0];

  return (
    <div className="min-h-screen bg-dark-900 text-slate-100 flex flex-col font-sans pb-10">
      {/* Header Bar */}
      <Navbar
        intersections={intersections}
        selectedCode={selectedCode}
        onSelectCode={setSelectedCode}
        onTriggerCrew={handleTriggerCrew}
        isCrewRunning={isCrewRunning}
      />

      {/* Main Grid Content */}
      <main className="container mx-auto px-6 space-y-6 flex-1">
        {/* Top Metric Cards */}
        <TrafficMetrics
          metrics={visionMetrics}
          los={predictionData?.predicted_los_15m || 'C'}
        />

        {/* Middle Main Section: Live Vision Stream + Signal & Emergency Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Live Vision Feed (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <LiveVisionFeed
              frameB64={frameB64}
              metrics={visionMetrics}
              activeSource={activeSource}
            />
            <EmergencyCorridor
              selectedCode={selectedCode}
              metrics={visionMetrics}
              onEmergencyToggle={loadData}
            />
          </div>

          {/* Right Column: Signal Controller & Predictions & Pollution (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <SignalStateView
              intersectionNode={selectedNode}
              onSignalUpdated={loadData}
            />
            <PredictionChart
              predictionData={predictionData}
              currentDensity={visionMetrics?.density_pct}
            />
            <PollutionMonitor
              pollutionData={pollutionData}
            />
          </div>
        </div>

        {/* Bottom Section: Network Map + Explainable AI Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <IntersectionMap
              intersections={intersections}
              selectedCode={selectedCode}
              onSelectCode={setSelectedCode}
            />
          </div>
          <div className="lg:col-span-7">
            <DecisionLogView
              decisionLogs={decisionLogs}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 text-center text-xs text-slate-500 border-t border-slate-900 pt-6">
        <p>Agentic AI Smart Traffic Management System • Powered by CrewAI, FastAPI, OpenCV, YOLOv8 & PostgreSQL</p>
      </footer>
    </div>
  );
}
