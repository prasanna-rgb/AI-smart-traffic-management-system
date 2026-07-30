import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Clock } from 'lucide-react';

export default function PredictionChart({ predictionData, currentDensity }) {
  const forecast = predictionData?.forecast || {
    '5_min': Math.min(100, (currentDensity || 40) * 1.02),
    '10_min': Math.min(100, (currentDensity || 40) * 1.05),
    '15_min': Math.min(100, (currentDensity || 40) * 1.08),
    '30_min': Math.min(100, (currentDensity || 40) * 1.12),
  };

  const chartData = [
    { time: 'Now', score: currentDensity || 40 },
    { time: '+5 Min', score: forecast['5_min'] },
    { time: '+10 Min', score: forecast['10_min'] },
    { time: '+15 Min', score: forecast['15_min'] },
    { time: '+30 Min', score: forecast['30_min'] },
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Prediction Agent Forecast</h2>
            <p className="text-xs text-slate-400">Short-Term Congestion Trend Horizon</p>
          </div>
        </div>

        <span className="px-2.5 py-1 text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-lg flex items-center gap-1 font-mono">
          <Clock className="w-3.5 h-3.5" /> 30-MIN HORIZON
        </span>
      </div>

      {/* Chart */}
      <div className="h-44 w-full my-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="predictionGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#818cf8" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#f8fafc', fontSize: '12px' }}
              formatter={(val) => [`${val}% Congestion`, 'Forecast Score']}
            />
            <Area type="monotone" dataKey="score" stroke="#818cf8" strokeWidth={2.5} fillOpacity={1} fill="url(#predictionGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Trend Summary */}
      <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-300">
        <span className="font-semibold text-indigo-400">Trend Assessment: </span>
        {predictionData?.trend_summary || 'Traffic flow expected to remain within standard thresholds.'}
      </div>
    </div>
  );
}
