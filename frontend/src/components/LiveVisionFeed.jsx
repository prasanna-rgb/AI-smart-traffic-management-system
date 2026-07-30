import React, { useState } from 'react';
import { Camera, Eye, Video, Play, Monitor, Layers } from 'lucide-react';
import { setStreamSource } from '../services/api';

export default function LiveVisionFeed({ frameB64, metrics, activeSource }) {
  const [source, setSource] = useState(activeSource || 'synthetic');

  const handleSourceChange = async (newSource) => {
    setSource(newSource);
    try {
      await setStreamSource(newSource);
    } catch (e) {
      console.error("Failed to set stream source:", e);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 relative flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
            <Camera className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">Vision Agent Stream</h2>
            <p className="text-xs text-slate-400">YOLOv8 Real-time Object Detection & Tracking</p>
          </div>
        </div>

        {/* Source Switcher */}
        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => handleSourceChange('synthetic')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              source === 'synthetic' ? 'bg-cyan-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Synthetic HD
          </button>
          <button
            onClick={() => handleSourceChange('0')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
              source === '0' ? 'bg-cyan-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Webcam Feed
          </button>
        </div>
      </div>

      {/* Frame Display */}
      <div className="relative aspect-video bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center group">
        {frameB64 ? (
          <img
            src={`data:image/jpeg;base64,${frameB64}`}
            alt="Live YOLOv8 Traffic Stream"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-3 text-slate-500 p-8 text-center">
            <Video className="w-12 h-12 animate-pulse text-cyan-500/40" />
            <p className="text-xs font-mono">INITIALIZING YOLOv8 VISION PIPELINE...</p>
          </div>
        )}

        {/* Live Overlay Badge */}
        <div className="absolute top-3 left-3 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 text-xs">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
          <span className="font-semibold text-emerald-400">YOLOv8 ACTIVE</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300 font-mono">10 FPS</span>
        </div>

        {/* Floating Class Count Badges */}
        <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 bg-slate-900/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-slate-700/60 text-xs">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 font-medium">Detected Fleet:</span>
            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded font-mono">
              Cars: {metrics?.car || 0}
            </span>
            <span className="px-2 py-0.5 bg-orange-500/20 text-orange-300 border border-orange-500/30 rounded font-mono">
              Buses: {metrics?.bus || 0}
            </span>
            <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded font-mono">
              Trucks: {metrics?.truck || 0}
            </span>
            <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 rounded font-mono">
              Bikes: {metrics?.motorcycle || 0}
            </span>
          </div>

          {metrics?.ambulance > 0 && (
            <span className="px-2.5 py-0.5 bg-red-500/30 text-red-300 border border-red-500/50 rounded font-bold animate-pulse">
              🚨 AMBULANCE DETECTED
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
