import React from 'react';
import { 
  IconCheck, IconMapPin, IconClock, IconAlertTriangle, 
  IconAmbulance, IconBuildingHospital, IconShield, 
  IconPhone, IconLeaf, IconBrain, IconDownload, IconMessageChatbot
} from '@tabler/icons-react';

export function TripStatusHeader({ statusData }) {
  if (!statusData) return null;
  return (
    <div className="glass-card p-6 rounded-2xl mb-6 flex justify-between items-center bg-gradient-to-r from-purple-900/10 to-indigo-900/10 border border-purple-500/20">
      <div>
        <div className="text-xs text-[var(--text-muted)] mb-1 uppercase font-bold tracking-wider">Day {statusData.day} / {statusData.totalDays}</div>
        <div className="text-xl font-bold text-[var(--text-primary)]">{statusData.title}</div>
      </div>
      <div className="text-right flex gap-6">
        <div>
          <div className="text-[10px] text-[var(--text-muted)] mb-1 uppercase">Current</div>
          <div className="text-sm font-semibold text-[var(--text-primary)]">{statusData.current}</div>
        </div>
        <div>
          <div className="text-[10px] text-[var(--text-muted)] mb-1 uppercase">Next</div>
          <div className="text-sm font-semibold text-purple-400">{statusData.next}</div>
        </div>
      </div>
      <div className="bg-[var(--bg-glass)] border border-green-500/30 px-4 py-2 rounded-xl flex items-center gap-2">
        <IconCheck size={18} className="text-green-400" />
        <span className="text-xs font-bold text-green-400">{statusData.aiStatus}</span>
      </div>
    </div>
  );
}

export function LiveTripTimeline({ timeline }) {
  if (!timeline) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6 border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-5 text-[var(--text-primary)]">Live Timeline</h3>
      <div className="space-y-4">
        {timeline.map((step, i) => (
          <div key={i} className={`flex items-start gap-4 p-3 rounded-xl border ${step.status === 'completed' ? 'border-green-500/20 bg-green-900/10 opacity-75' : step.status === 'current' ? 'border-purple-500/40 bg-purple-900/20' : 'border-[var(--border-color)] bg-[var(--bg-glass)]'}`}>
            <div className="mt-0.5">
              {step.status === 'completed' ? <IconCheck size={16} className="text-green-500" /> : step.status === 'current' ? <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.8)]"></div> : <IconClock size={16} className="text-[var(--text-muted)]" />}
            </div>
            <div className="flex-1">
              <div className={`text-xs font-bold mb-1 ${step.status === 'current' ? 'text-purple-400' : 'text-[var(--text-muted)]'}`}>{step.time}</div>
              <div className={`text-sm font-semibold ${step.status === 'completed' ? 'text-green-400 line-through' : 'text-[var(--text-primary)]'}`}>{step.action}</div>
            </div>
            {step.status === 'upcoming' && <div className="text-[10px] text-[var(--text-muted)] bg-[var(--bg-glass)] px-2 py-1 rounded-md">Upcoming</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

export function EmergencyAssistant({ emergencyData }) {
  if (!emergencyData) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6 border border-red-500/20 bg-red-900/5">
      <h3 className="text-sm font-bold mb-4 text-red-400 flex items-center gap-2">
        <IconAmbulance size={18} /> One-Tap Emergency Assistance
      </h3>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <button className="bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-300 p-3 rounded-xl flex items-center gap-2 text-xs font-bold transition-colors">
          <IconAmbulance size={16} /> Medical
        </button>
        <button className="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 text-blue-300 p-3 rounded-xl flex items-center gap-2 text-xs font-bold transition-colors">
          <IconShield size={16} /> Police
        </button>
      </div>
      <div className="space-y-2 text-xs text-[var(--text-muted)]">
        <div className="flex justify-between p-2 bg-[var(--bg-glass)] rounded-lg"><span>Nearest Hospital</span><span className="text-[var(--text-primary)] font-semibold">{emergencyData.hospital}</span></div>
        <div className="flex justify-between p-2 bg-[var(--bg-glass)] rounded-lg"><span>Your Hotel</span><span className="text-[var(--text-primary)] font-semibold">{emergencyData.hotel_address}</span></div>
      </div>
    </div>
  );
}

export function TravelLearningWidget({ memory }) {
  if (!memory) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6 border border-indigo-500/20 bg-indigo-900/10">
      <h3 className="text-sm font-bold mb-4 text-indigo-400 flex items-center gap-2">
        <IconBrain size={18} /> Travel Learning Engine
      </h3>
      <div className="text-[10px] text-[var(--text-muted)] mb-3">AI Learned Preferences:</div>
      <div className="space-y-2 mb-4">
        {memory.insights.map((insight, i) => (
          <div key={i} className="text-xs text-indigo-200 bg-[var(--bg-glass)] border border-indigo-500/10 p-2 rounded-lg">
            {insight}
          </div>
        ))}
      </div>
      <div className="text-[10px] font-bold text-indigo-400 bg-indigo-500/20 px-3 py-1.5 rounded-lg inline-block">
        🚀 {memory.improvement_metric}
      </div>
    </div>
  );
}

export function GreenTravelScore({ sustainability }) {
  if (!sustainability) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6 border border-green-500/20 bg-green-900/10">
      <h3 className="text-sm font-bold mb-4 text-green-400 flex items-center gap-2">
        <IconLeaf size={18} /> Trip Sustainability Score
      </h3>
      <div className="text-2xl font-extrabold text-green-400 mb-4">{sustainability.score_stars}</div>
      <div className="space-y-2 text-xs text-[var(--text-muted)]">
        <div className="flex justify-between p-2 bg-[var(--bg-glass)] rounded-lg"><span>Carbon Saved</span><span className="text-green-300 font-bold">{sustainability.carbon_saved_kg} kg CO₂</span></div>
        <div className="flex justify-between p-2 bg-[var(--bg-glass)] rounded-lg"><span>Equivalent to</span><span className="text-green-300 font-bold">🌳 {sustainability.equivalent_trees} trees planted</span></div>
        <div className="p-2 bg-green-500/20 text-green-300 rounded-lg font-semibold mt-2">{sustainability.better_choice}</div>
      </div>
    </div>
  );
}

export function OfflinePackGenerator({ onGenerate }) {
  return (
    <div className="glass-card p-5 rounded-2xl mb-6 border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-2 text-[var(--text-primary)] flex items-center gap-2">
        <IconDownload size={18} /> Offline Travel Pack
      </h3>
      <p className="text-[10px] text-[var(--text-muted)] mb-4">Download maps, emergency contacts, and tickets for offline use.</p>
      <button onClick={onGenerate} className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 p-3 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-colors">
        <IconDownload size={16} /> Generate Offline Package
      </button>
    </div>
  );
}

export function AILiveChat() {
  return (
    <div className="glass-card flex flex-col h-[400px] rounded-2xl border border-[var(--border-color)] overflow-hidden">
      <div className="bg-purple-900/30 p-3 border-b border-purple-500/20 flex items-center gap-2">
        <IconMessageChatbot size={18} className="text-purple-400" />
        <span className="text-xs font-bold text-purple-300">Live Journey Assistant</span>
      </div>
      <div className="flex-1 p-4 space-y-4 overflow-y-auto bg-[var(--bg-glass)]">
        <div className="flex justify-end">
          <div className="bg-purple-600/30 border border-purple-500/30 text-purple-100 text-xs p-3 rounded-2xl rounded-tr-sm max-w-[80%]">
            Can I visit Uluwatu today?
          </div>
        </div>
        <div className="flex justify-start">
          <div className="bg-slate-800/50 border border-slate-700 text-slate-300 text-xs p-3 rounded-2xl rounded-tl-sm max-w-[80%]">
            Yes. Current weather is 27°C. Travel time is 45 mins. Best visiting time: 4:30 PM for sunset.
          </div>
        </div>
      </div>
      <div className="p-3 border-t border-[var(--border-color)] bg-[var(--bg-glass)]">
        <input type="text" placeholder="Ask your companion..." className="w-full bg-slate-900/50 border border-[var(--border-color)] rounded-xl px-4 py-2 text-xs text-[var(--text-primary)] outline-none" />
      </div>
    </div>
  );
}
