import React from 'react';
import { 
  IconPlane, IconTrain, IconBus, IconCar, 
  IconCheck, IconShield, IconLeaf, IconClock, 
  IconCoin, IconAlertTriangle, IconInfoCircle, IconDownload
} from '@tabler/icons-react';

export function AIRouteHeroCard({ route }) {
  if (!route) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] bg-gradient-to-br from-[var(--bg-glass)] to-purple-900/10 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <IconCheck size={20} className="text-green-400" />
        <span className="text-sm font-bold text-green-400 tracking-wide uppercase">AI Smart Transit Recommendation</span>
      </div>
      
      <div className="flex justify-between items-start mb-6 flex-wrap gap-4">
        <div>
          <div className="text-xs text-[var(--text-muted)] mb-1">Recommended Mode</div>
          <div className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-2">
            {route.recommended_mode?.includes('Flight') ? <IconPlane /> : route.recommended_mode?.includes('Train') ? <IconTrain /> : <IconBus />}
            {route.recommended_mode}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-[var(--text-muted)] mb-1">Overall AI Score</div>
          <div className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">
            {route.confidence}%
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">Travel Time</div>
          <div className="text-sm font-bold text-[var(--text-primary)]">{route.travel_time}</div>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">Est. Cost</div>
          <div className="text-sm font-bold text-[var(--text-primary)]">₹{route.estimated_cost?.toLocaleString()}</div>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">Carbon</div>
          <div className="text-sm font-bold text-amber-400">{route.carbon}</div>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <div className="text-[10px] text-[var(--text-muted)] uppercase mb-1">Safety</div>
          <div className="text-sm font-bold text-green-400">{route.safety}</div>
        </div>
      </div>
      
      <div className="bg-purple-900/20 p-4 rounded-xl border border-purple-500/20 text-sm text-[var(--text-primary)] flex items-start gap-3">
        <IconInfoCircle size={18} className="text-purple-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-purple-300">AI Reason: </span>
          {route.reason}
        </div>
      </div>
    </div>
  );
}

export function MultiModalComparison({ routes }) {
  if (!routes || !routes.length) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)]">Multi-Modal AI Comparison</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-[var(--text-muted)]">
          <thead className="text-[10px] uppercase bg-[var(--bg-glass)] text-[var(--text-muted)]">
            <tr>
              <th className="px-4 py-3 rounded-tl-xl">Mode</th>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Cost</th>
              <th className="px-4 py-3">Carbon</th>
              <th className="px-4 py-3">Comfort</th>
              <th className="px-4 py-3 rounded-tr-xl text-right">AI Score</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((r, i) => (
              <tr key={i} className="border-b border-[var(--border-color)] hover:bg-[var(--bg-glass)] transition-colors">
                <td className="px-4 py-3 font-bold text-[var(--text-primary)]">{r.mode}</td>
                <td className="px-4 py-3">{r.time_str}</td>
                <td className="px-4 py-3">₹{r.cost_inr.toLocaleString()}</td>
                <td className="px-4 py-3">{r.carbon_rating}</td>
                <td className="px-4 py-3">{r.comfort}</td>
                <td className="px-4 py-3 text-right font-bold text-purple-400">{r.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function SmartTimeline({ timeline }) {
  if (!timeline) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)]">Smart AI Timeline</h3>
      <div className="relative border-l border-purple-500/30 ml-3 space-y-6 py-2">
        {timeline.map((step, i) => (
          <div key={i} className="pl-6 relative">
            <div className="absolute w-3 h-3 bg-purple-500 rounded-full -left-[6.5px] top-1.5 shadow-[0_0_8px_rgba(168,85,247,0.6)]"></div>
            <div className="text-xs text-purple-400 font-bold mb-1">{step.time}</div>
            <div className="text-sm text-[var(--text-primary)] font-semibold">{step.action}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function WeatherAlongRoute({ weather, warnings }) {
  if (!weather) return null;
  const weatherList = Array.isArray(weather) ? weather : (weather.stops || []);
  const warningList = warnings || weather.warnings || [];
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)]">Weather Along Route</h3>
      <div className="flex justify-between items-center mb-6 relative">
        <div className="absolute top-1/2 left-0 w-full h-px bg-[var(--border-color)] -z-10"></div>
        {weatherList.map((w, i) => (
          <div key={i} className="bg-[var(--bg-glass)] border border-[var(--border-color)] p-3 rounded-xl flex flex-col items-center min-w-[80px]">
            <div className="text-2xl mb-1">{w.icon}</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">{w.temp || (w.temp_c != null ? `${w.temp_c}°C` : '')}</div>
            <div className="text-[10px] text-[var(--text-muted)]">{w.location}</div>
          </div>
        ))}
      </div>
      {warningList && warningList.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-500/20 p-3 rounded-xl flex items-start gap-2">
          <IconAlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200">
            {warningList.map((w, i) => <div key={i}>{w}</div>)}
          </div>
        </div>
      )}
    </div>
  );
}

export function AIBudgetOptimizer({ budget }) {
  if (!budget) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconCoin size={18} className="text-emerald-400" /> AI Budget Optimizer
      </h3>
      <div className="text-xs text-[var(--text-muted)] mb-3">Estimated Cost: ₹{budget.current_cost?.toLocaleString()}</div>
      
      <div className="space-y-3 mb-4">
        {budget.suggestions?.map((s, i) => (
          <div key={i} className="flex justify-between items-center bg-emerald-900/10 border border-emerald-500/20 p-3 rounded-xl">
            <span className="text-xs text-emerald-100">{s.text}</span>
            <span className="text-xs font-bold text-emerald-400">-₹{s.savings.toLocaleString()}</span>
          </div>
        ))}
      </div>
      
      <div className="pt-3 border-t border-[var(--border-color)] flex justify-between items-center">
        <span className="text-xs text-[var(--text-muted)] font-bold">Total Potential Savings</span>
        <span className="text-lg font-extrabold text-emerald-400">₹{budget.total_savings_potential?.toLocaleString()}</span>
      </div>
    </div>
  );
}

export function CarbonFootprint({ carbon }) {
  if (!carbon) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconLeaf size={18} className="text-green-500" /> Carbon Footprint
      </h3>
      <div className="space-y-3 mb-4">
        {carbon.modes?.map((m, i) => (
          <div key={i} className="flex justify-between items-center">
            <div className="text-xs text-[var(--text-primary)] w-16">{m.mode}</div>
            <div className="flex-1 mx-3 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className={`h-full ${m.mode === 'Flight' ? 'bg-red-500' : 'bg-green-500'}`}
                style={{ width: `${Math.min(100, (m.co2_kg / 500) * 100)}%` }}
              ></div>
            </div>
            <div className="text-xs text-[var(--text-muted)] w-16 text-right">{m.co2_kg} kg CO₂</div>
          </div>
        ))}
      </div>
      <div className="bg-green-900/20 p-3 rounded-xl border border-green-500/20 text-xs text-green-300">
        <span className="font-bold">AI Suggestion: </span>{carbon.suggestion}
      </div>
    </div>
  );
}

export function SafetyIntelligence({ safety }) {
  if (!safety) return null;
  return (
    <div className="glass-card p-5 rounded-2xl mb-6">
      <h3 className="text-md font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconShield size={18} className="text-blue-400" /> Safety Intelligence
      </h3>
      <div className="flex justify-between items-end mb-5">
        <div>
          <div className="text-[10px] text-[var(--text-muted)] uppercase">Overall Safety Score</div>
          <div className="text-3xl font-extrabold text-blue-400">{safety.safety_score}</div>
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-bold text-[var(--text-primary)]">Emergency Contacts:</span> {safety.emergency_contacts}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs text-[var(--text-muted)]">
        <div className="flex justify-between bg-[var(--bg-glass)] p-2 rounded-lg"><span>Medical Access</span><span className="text-amber-400">{safety.medical_access}</span></div>
        <div className="flex justify-between bg-[var(--bg-glass)] p-2 rounded-lg"><span>Night Safety</span><span className="text-amber-400">{safety.night_safety}</span></div>
        <div className="flex justify-between bg-[var(--bg-glass)] p-2 rounded-lg"><span>Women Safety</span><span className="text-amber-400">{safety.women_safety}</span></div>
        <div className="flex justify-between bg-[var(--bg-glass)] p-2 rounded-lg"><span>Crime Index</span><span className="text-[var(--text-primary)] font-bold">{safety.crime_index}</span></div>
      </div>
    </div>
  );
}
