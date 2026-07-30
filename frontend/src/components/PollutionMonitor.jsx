import React from 'react';
import { Leaf, Flame, Wind, Droplet, ShieldCheck } from 'lucide-react';

export default function PollutionMonitor({ pollutionData }) {
  const co2 = pollutionData?.co2_kg_hr || 18.5;
  const nox = pollutionData?.nox_g_hr || 120.0;
  const pm25 = pollutionData?.pm25_g_hr || 8.4;
  const fuel = pollutionData?.fuel_liters_hr || 7.2;
  const ecoIndex = pollutionData?.eco_index || 82.0;

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400">
            <Leaf className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Pollution Agent Monitor</h2>
            <p className="text-xs text-slate-400">Tailpipe Carbon Footprint & Environmental Impact</p>
          </div>
        </div>

        <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5" /> Eco Index: {ecoIndex}/100
        </span>
      </div>

      {/* Grid Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Flame className="w-3.5 h-3.5 text-amber-400" /> CO₂ Emission
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{co2} <span className="text-xs font-normal text-slate-400">kg/hr</span></p>
        </div>

        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Wind className="w-3.5 h-3.5 text-cyan-400" /> NOₓ Pollutants
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{nox} <span className="text-xs font-normal text-slate-400">g/hr</span></p>
        </div>

        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Wind className="w-3.5 h-3.5 text-purple-400" /> PM2.5 Fine Particulates
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{pm25} <span className="text-xs font-normal text-slate-400">g/hr</span></p>
        </div>

        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Droplet className="w-3.5 h-3.5 text-blue-400" /> Fuel Burn Rate
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{fuel} <span className="text-xs font-normal text-slate-400">L/hr</span></p>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-400">Green Air Quality Rating:</span>
          <span className="font-semibold text-emerald-400">{ecoIndex > 70 ? 'CLEAN AIR' : 'MODERATE EMISSIONS'}</span>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
          <div
            className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full transition-all duration-500"
            style={{ width: `${ecoIndex}%` }}
          />
        </div>
      </div>
    </div>
  );
}
