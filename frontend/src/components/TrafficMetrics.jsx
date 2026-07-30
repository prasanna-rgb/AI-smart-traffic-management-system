import React from 'react';
import { Car, Bus, Truck, Bike, Ambulance, Gauge, Activity, AlertTriangle } from 'lucide-react';

export default function TrafficMetrics({ metrics, los }) {
  const total = metrics?.total_vehicles || 0;
  const speed = metrics?.average_speed || 40.0;
  const density = metrics?.density_pct || 0.0;
  const currentLos = los || 'C';

  const getLosColor = (grade) => {
    switch (grade) {
      case 'A': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      case 'B': return 'bg-green-500/20 text-green-400 border-green-500/40';
      case 'C': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'D': return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'E': return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'F': return 'bg-red-500/20 text-red-400 border-red-500/40';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/40';
    }
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {/* Total Vehicles Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Vehicles</p>
          <p className="text-2xl font-black text-white mt-1 font-mono">{total}</p>
          <p className="text-xs text-cyan-400 mt-1">Vision Detected</p>
        </div>
        <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
          <Car className="w-6 h-6" />
        </div>
      </div>

      {/* Average Speed Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Speed</p>
          <p className="text-2xl font-black text-white mt-1 font-mono">{speed} <span className="text-sm font-normal text-slate-400">km/h</span></p>
          <p className="text-xs text-emerald-400 mt-1">Flow Velocity</p>
        </div>
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
          <Gauge className="w-6 h-6" />
        </div>
      </div>

      {/* Density Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Occupancy Density</p>
          <p className="text-2xl font-black text-white mt-1 font-mono">{density}%</p>
          <div className="w-24 bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                density > 75 ? 'bg-red-500' : density > 50 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(100, density)}%` }}
            />
          </div>
        </div>
        <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl text-purple-400">
          <Activity className="w-6 h-6" />
        </div>
      </div>

      {/* Level of Service (LOS) Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Level of Service</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-3 py-1 text-xl font-black rounded-lg border font-mono ${getLosColor(currentLos)}`}>
              LOS {currentLos}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Capacity Grade</p>
        </div>
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400">
          <AlertTriangle className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}
