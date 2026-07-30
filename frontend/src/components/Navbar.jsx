import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, Radio, RefreshCw, Zap } from 'lucide-react';

export default function Navbar({ intersections, selectedCode, onSelectCode, onTriggerCrew, isCrewRunning }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="glass-panel sticky top-0 z-50 border-b border-slate-800 px-6 py-3.5 mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Brand Title */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-lg shadow-cyan-500/10">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white">Smart Traffic AI</h1>
              <span className="px-2 py-0.5 text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                7-AGENT CREW
              </span>

            </div>
            <p className="text-xs text-slate-400">Autonomous Multi-Agent Intersection Controller & Vision Engine</p>
          </div>
        </div>

        {/* Intersection Switcher & Status Badges */}
        <div className="flex items-center flex-wrap gap-4">
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700/60 rounded-xl px-3 py-1.5">
            <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
            <select
              value={selectedCode}
              onChange={(e) => onSelectCode(e.target.value)}
              className="bg-transparent text-sm text-slate-200 font-medium focus:outline-none cursor-pointer"
            >
              {intersections.map((node) => (
                <option key={node.code} value={node.code} className="bg-slate-900 text-slate-200">
                  {node.code} - {node.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={onTriggerCrew}
            disabled={isCrewRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            {isCrewRunning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {isCrewRunning ? 'Executing 6 Agents...' : 'Run CrewAI Reasoner'}
          </button>

          <div className="hidden md:flex items-center gap-3 text-xs font-mono text-slate-400 bg-slate-900/60 px-3 py-1.5 border border-slate-800 rounded-xl">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>LIVE 10Hz</span>
            <span className="text-slate-600">|</span>
            <span>{time}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
