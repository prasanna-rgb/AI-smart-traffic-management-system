import React, { useState } from 'react';
import { MessageSquareText, ChevronDown, ChevronUp, Bot, Sparkles, Terminal } from 'lucide-react';

export default function DecisionLogView({ decisionLogs }) {
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const logs = decisionLogs && decisionLogs.length > 0 ? decisionLogs : [
    {
      id: 1,
      timestamp: new Date().toISOString(),
      intersection_code: 'INT-01',
      agent_name: 'Decision Agent',
      reasoning: '✅ BALANCED TRAFFIC OPTIMIZATION for INT-01: Vision Agent detected 19 vehicles at 38 km/h. Prediction Agent projects stable flow. Maintaining 45s N-S green light duration split.',
      prompt_summary: 'Inputs: Vision(19 veh, 38km/h), Analysis(LOS C), Prediction(15m: 42%), Pollution(18.5kg CO2/hr), Emergency(False)',
      action_taken: 'Maintained balanced cycle splits NS=45s, EW=25s.'
    }
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Explainable AI (XAI) Decision Logs</h2>
            <p className="text-xs text-slate-400">Natural Language Reasoning & Prompt Trace Timeline</p>
          </div>
        </div>

        <span className="px-2.5 py-1 text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-lg flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5" /> LLM REASONING AUDIT
        </span>
      </div>

      {/* Log Feed List */}
      <div className="space-y-3 max-h-72 overflow-y-auto custom-scrollbar pr-1">
        {logs.map((log) => (
          <div
            key={log.id || log.timestamp}
            className="p-3.5 bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-xl transition-all cursor-pointer"
            onClick={() => toggleExpand(log.id)}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded font-mono font-bold">
                  {log.intersection_code}
                </span>
                <span className="font-semibold text-slate-300">{log.agent_name}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-500 font-mono">
                <span>{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Just now'}</span>
                {expandedId === log.id ? <ChevronUp className="w-4 h-4 text-cyan-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </div>

            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {log.reasoning}
            </p>

            <div className="mt-2 text-xs font-mono text-cyan-400/90 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5" />
              <span>Action: {log.action_taken}</span>
            </div>

            {/* Expandable LLM Prompt Trace */}
            {expandedId === log.id && log.prompt_summary && (
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-xs font-mono text-slate-400 bg-slate-950 p-2.5 rounded-lg">
                <span className="text-cyan-400 font-semibold">Agent Context Trace:</span>
                <p className="mt-1 text-slate-300">{log.prompt_summary}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
