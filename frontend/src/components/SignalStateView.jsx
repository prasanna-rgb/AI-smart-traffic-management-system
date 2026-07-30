import React, { useState } from 'react';
import { Sliders, CheckCircle, Zap, ShieldAlert } from 'lucide-react';
import { overrideSignal } from '../services/api';

export default function SignalStateView({ intersectionNode, onSignalUpdated }) {
  const mode = intersectionNode?.signal_mode || 'AI_AUTO';
  const phase = intersectionNode?.active_phase || 'NORTH_SOUTH_GREEN';
  const nsTimer = intersectionNode?.ns_green_timer || 45;
  const ewTimer = intersectionNode?.ew_green_timer || 25;

  const [loading, setLoading] = useState(false);

  const handleOverride = async (newMode, newPhase, newNs, newEw) => {
    setLoading(true);
    try {
      await overrideSignal(intersectionNode?.code || 'INT-01', newMode, newPhase, newNs, newEw);
      if (onSignalUpdated) onSignalUpdated();
    } catch (e) {
      console.error("Signal override failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const isNsGreen = phase === 'NORTH_SOUTH_GREEN';

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Signal Controller</h2>
            <p className="text-xs text-slate-400">Dynamic Phase Timing & Mode Override</p>
          </div>
        </div>

        <span className={`px-2.5 py-1 text-xs font-semibold rounded-lg border font-mono ${
          mode === 'EMERGENCY_CORRIDOR'
            ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse'
            : (mode === 'AI_AUTO' ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40' : 'bg-amber-500/20 text-amber-400 border-amber-500/40')
        }`}>
          MODE: {mode}
        </span>
      </div>

      {/* Traffic Light Widgets Grid */}
      <div className="grid grid-cols-2 gap-4 my-2">
        {/* North-South Light Box */}
        <div className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
          isNsGreen ? 'bg-slate-900 border-emerald-500/50 shadow-lg shadow-emerald-500/10' : 'bg-slate-950 border-slate-800'
        }`}>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">NORTH - SOUTH</span>
            <p className="text-lg font-bold text-white mt-1 font-mono">{nsTimer} <span className="text-xs text-slate-400 font-normal">sec green</span></p>
            <span className={`inline-block mt-2 px-2 py-0.5 text-xs font-bold rounded ${
              isNsGreen ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
            }`}>
              {isNsGreen ? '🟢 GREEN' : '🔴 RED'}
            </span>
          </div>

          <div className="flex flex-col gap-1.5 p-2 bg-slate-950 rounded-xl border border-slate-800">
            <span className={`w-4 h-4 rounded-full ${!isNsGreen ? 'bg-red-500 shadow-md shadow-red-500/50' : 'bg-red-950'}`} />
            <span className="w-4 h-4 rounded-full bg-yellow-950" />
            <span className={`w-4 h-4 rounded-full ${isNsGreen ? 'bg-emerald-500 shadow-md shadow-emerald-500/50' : 'bg-emerald-950'}`} />
          </div>
        </div>

        {/* East-West Light Box */}
        <div className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
          !isNsGreen ? 'bg-slate-900 border-emerald-500/50 shadow-lg shadow-emerald-500/10' : 'bg-slate-950 border-slate-800'
        }`}>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">EAST - WEST</span>
            <p className="text-lg font-bold text-white mt-1 font-mono">{ewTimer} <span className="text-xs text-slate-400 font-normal">sec green</span></p>
            <span className={`inline-block mt-2 px-2 py-0.5 text-xs font-bold rounded ${
              !isNsGreen ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
            }`}>
              {!isNsGreen ? '🟢 GREEN' : '🔴 RED'}
            </span>
          </div>

          <div className="flex flex-col gap-1.5 p-2 bg-slate-950 rounded-xl border border-slate-800">
            <span className={`w-4 h-4 rounded-full ${isNsGreen ? 'bg-red-500 shadow-md shadow-red-500/50' : 'bg-red-950'}`} />
            <span className="w-4 h-4 rounded-full bg-yellow-950" />
            <span className={`w-4 h-4 rounded-full ${!isNsGreen ? 'bg-emerald-500 shadow-md shadow-emerald-500/50' : 'bg-emerald-950'}`} />
          </div>
        </div>
      </div>

      {/* Manual Override Action Controls */}
      <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-800">
        <button
          onClick={() => handleOverride('AI_AUTO', 'NORTH_SOUTH_GREEN', 45, 25)}
          disabled={loading}
          className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-semibold rounded-lg transition-all"
        >
          Reset AI Auto Mode
        </button>
        <button
          onClick={() => handleOverride('MANUAL', isNsGreen ? 'EAST_WEST_GREEN' : 'NORTH_SOUTH_GREEN', isNsGreen ? 20 : 60, isNsGreen ? 60 : 20)}
          disabled={loading}
          className="flex-1 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-200 border border-cyan-500/40 text-xs font-semibold rounded-lg transition-all"
        >
          Toggle Signal Phase
        </button>
      </div>
    </div>
  );
}
