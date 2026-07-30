import React from 'react';
import { MapPin, Navigation, Radio } from 'lucide-react';

export default function IntersectionMap({ intersections, selectedCode, onSelectCode }) {
  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg text-blue-400">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Smart Grid Network Map</h2>
            <p className="text-xs text-slate-400">Interconnected Multi-Intersection Nodes</p>
          </div>
        </div>

        <span className="px-2.5 py-1 text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-lg flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" /> 4 NODES ONLINE
        </span>
      </div>

      {/* Grid Network Map Node Cards */}
      <div className="grid grid-cols-2 gap-3">
        {intersections.map((node) => {
          const isSelected = node.code === selectedCode;
          const isEmergency = node.signal_mode === 'EMERGENCY_CORRIDOR';

          return (
            <div
              key={node.code}
              onClick={() => onSelectCode(node.code)}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500'
                  : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-xs text-cyan-400">{node.code}</span>
                <span className={`w-2.5 h-2.5 rounded-full ${
                  isEmergency ? 'bg-red-500 animate-ping' : (node.signal_mode === 'AI_AUTO' ? 'bg-emerald-400' : 'bg-amber-400')
                }`} />
              </div>

              <h3 className="text-xs font-bold text-white mt-1 truncate">{node.name}</h3>

              <div className="flex items-center justify-between text-xs mt-2 pt-2 border-t border-slate-800/80 text-slate-400 font-mono">
                <span>Phase: {node.active_phase === 'NORTH_SOUTH_GREEN' ? 'N-S' : 'E-W'}</span>
                <span className="text-slate-300 font-bold">{node.ns_green_timer}s / {node.ew_green_timer}s</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
