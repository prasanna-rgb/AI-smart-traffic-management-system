import React from 'react';
import { Siren, ShieldAlert, Navigation, CheckCircle2, Zap } from 'lucide-react';
import { triggerEmergency } from '../services/api';

export default function EmergencyCorridor({ selectedCode, metrics, onEmergencyToggle }) {
  const isEmergency = metrics?.ambulance > 0;
  const corridorRoute = ['INT-01', 'INT-02', 'INT-03'];

  const handleToggle = async (activeState) => {
    try {
      await triggerEmergency(selectedCode, activeState, 'AMBULANCE');
      if (onEmergencyToggle) onEmergencyToggle(activeState);
    } catch (e) {
      console.error("Failed to trigger emergency corridor:", e);
    }
  };

  return (
    <div className={`p-5 rounded-2xl border transition-all ${
      isEmergency ? 'glass-panel-glow border-red-500/50 bg-red-950/20' : 'glass-panel border-slate-800'
    }`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${isEmergency ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-bounce' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
            <Siren className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Emergency Agent Corridor</h2>
            <p className="text-xs text-slate-400">First-Responder Signal Preemption Network</p>
          </div>
        </div>

        <button
          onClick={() => handleToggle(!isEmergency)}
          className={`px-3 py-1.5 rounded-xl text-xs font-bold tracking-wide transition-all border shadow-lg ${
            isEmergency
              ? 'bg-red-600 hover:bg-red-500 text-white border-red-400 shadow-red-600/30 animate-pulse'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
          }`}
        >
          {isEmergency ? '🚨 AMBULANCE ACTIVE (CLEAR CORRIDOR)' : 'Simulate Ambulance Detection'}
        </button>
      </div>

      {/* Corridor Status Card */}
      {isEmergency ? (
        <div className="p-4 bg-red-950/40 border border-red-500/40 rounded-xl space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-red-400 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4" /> PRIORITY LEVEL 10 / GREEN CORRIDOR ENGAGED
            </span>
            <span className="px-2 py-0.5 bg-red-500/30 text-red-200 rounded font-mono font-bold">100% PREEMPTION</span>
          </div>

          <p className="text-xs text-red-200">
            Emergency Agent has locked green light signals along the priority route to provide zero-delay passage for first responders.
          </p>

          <div className="flex items-center gap-2 pt-1 border-t border-red-500/30">
            <Navigation className="w-4 h-4 text-red-400 shrink-0" />
            <span className="text-xs text-red-300 font-semibold">Active Corridor Route:</span>
            <div className="flex items-center gap-1.5 font-mono text-xs text-white">
              {corridorRoute.map((node, i) => (
                <React.Fragment key={node}>
                  <span className="px-2 py-0.5 bg-red-500/30 border border-red-400/40 rounded">{node}</span>
                  {i < corridorRoute.length - 1 && <span className="text-red-400">→</span>}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Emergency Corridor System Standby. No active first-responder vehicle detected.</span>
          </div>
          <span className="font-mono text-slate-500">PRIORITY 0</span>
        </div>
      )}
    </div>
  );
}
