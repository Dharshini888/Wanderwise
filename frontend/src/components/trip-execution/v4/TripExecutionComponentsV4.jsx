import React from 'react';
import { 
  IconCheck, IconMapPin, IconClock, IconAlertTriangle, 
  IconAmbulance, IconBuildingHospital, IconShield, 
  IconPhone, IconLeaf, IconBrain, IconDownload, IconMessageChatbot,
  IconSun, IconCloudRain, IconWind, IconEye,
  IconCar, IconBus, IconTrain, IconPlane, IconWalk, IconBike,
  IconCurrencyDollar, IconCoffee, IconBuildingSkyscraper
} from '@tabler/icons-react';

export function JourneyHeader({ routeData }) {
  if (!routeData) return null;
  const prov = routeData.provenance || {};
  return (
    <div className="glass-card p-6 rounded-2xl mb-6 flex flex-col justify-between bg-gradient-to-r from-blue-900/10 to-purple-900/10 border border-blue-500/20 gap-4">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Origin</div>
            <div className="text-xl font-bold">{routeData.origin}</div>
          </div>
          <div className="flex flex-col items-center px-4">
            <span className="text-[10px] text-purple-400 font-bold bg-purple-500/10 px-2 py-0.5 rounded-full mb-1">{routeData.distance_km} km</span>
            <div className="w-16 h-[2px] bg-gradient-to-r from-transparent via-purple-500 to-transparent"></div>
            <IconTrain size={16} className="text-purple-400 mt-1" />
          </div>
          <div className="text-center">
            <div className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1">Destination</div>
            <div className="text-xl font-bold">{routeData.destination}</div>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="bg-[var(--bg-glass)] px-4 py-2 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] text-[var(--text-muted)] uppercase">Status</div>
            <div className="text-sm font-bold text-green-400 flex items-center gap-1"><IconCheck size={14}/> {routeData.status}</div>
          </div>
          <div className="bg-[var(--bg-glass)] px-4 py-2 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] text-[var(--text-muted)] uppercase">AI Confidence</div>
            <div className="text-sm font-bold text-purple-400">{routeData.decision_panel?.confidence}%</div>
          </div>
        </div>
      </div>

      {/* Data Provenance & Live Badges */}
      <div className="pt-3 border-t border-[var(--border-color)] flex flex-wrap gap-2 text-[10px] font-semibold">
        <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 px-2.5 py-1 rounded-lg">
          📍 Map: {routeData.data_status?.routing ? `Routing (${routeData.data_status.routing.toUpperCase()})` : (prov.geocoding || 'Live OSM')}
        </span>
        <span className="bg-blue-500/10 border border-blue-500/30 text-blue-300 px-2.5 py-1 rounded-lg">
          🛣️ Route: {prov.routing || 'Live OSRM'}
        </span>
        <span className="bg-sky-500/10 border border-sky-500/30 text-sky-300 px-2.5 py-1 rounded-lg">
          🌤️ Weather: {routeData.data_status?.weather ? `Weather (${routeData.data_status.weather.toUpperCase()})` : (prov.weather || 'Live Open-Meteo')}
        </span>
        <span className="bg-purple-500/10 border border-purple-500/30 text-purple-300 px-2.5 py-1 rounded-lg">
          🏥 POIs: {routeData.data_status?.places ? `Places (${routeData.data_status.places.toUpperCase()})` : (prov.places || 'Live Overpass')}
        </span>
        <span className="bg-amber-500/10 border border-amber-500/30 text-amber-300 px-2.5 py-1 rounded-lg">
          🚌 Transit: {routeData.data_status?.transit ? `Schedule (${routeData.data_status.transit.toUpperCase()})` : (prov.transit_schedule || 'Estimated')}
        </span>
      </div>
    </div>
  );
}

export function AIDecisionPanel({ decision }) {
  if (!decision) return null;
  const metrics = Object.entries(decision.panel);
  
  return (
    <div className="glass-card p-6 rounded-2xl border border-purple-500/20 mb-6 bg-purple-900/5">
      <h3 className="text-sm font-bold mb-4 text-purple-400 flex items-center gap-2">
        <IconBrain size={18} /> AI Decision Analysis
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="space-y-3">
          {metrics.slice(0, 4).map(([key, value]) => (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[var(--text-muted)]">{key}</span>
                <span className="font-bold">{value}/10</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: `${value * 10}%` }}></div>
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          {metrics.slice(4).map(([key, value]) => (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[var(--text-muted)]">{key}</span>
                <span className="font-bold">{value}/10</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${value * 10}%` }}></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-[var(--bg-glass)] p-4 rounded-xl border border-[var(--border-color)] flex gap-4">
        <div className="flex-1">
          <div className="text-[10px] uppercase text-[var(--text-muted)] mb-1">Overall Recommendation</div>
          <div className="text-lg font-bold text-green-400">{decision.recommended.mode}</div>
        </div>
        <div className="flex-2 border-l border-[var(--border-color)] pl-4">
          <div className="text-[10px] uppercase text-[var(--text-muted)] mb-1">Why?</div>
          <div className="text-xs text-[var(--text-primary)] font-semibold flex flex-wrap gap-2">
            {decision.reasons.map((r, i) => <span key={i} className="bg-slate-800 px-2 py-0.5 rounded">{r}</span>)}
          </div>
        </div>
      </div>
    </div>
  );
}

export function TransportComparison({ options, recommended }) {
  if (!options) return null;
  
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconCar size={18} /> Multi-Modal Comparison
      </h3>
      <div className="space-y-3">
        {options.map((opt, i) => {
          const isBest = opt.mode === recommended.mode;
          return (
            <div key={i} className={`p-3 rounded-xl border flex items-center justify-between ${isBest ? 'border-purple-500/40 bg-purple-500/10' : 'border-[var(--border-color)] bg-[var(--bg-glass)]'}`}>
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isBest ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-800 text-slate-400'}`}>
                  {opt.mode.includes("Flight") ? <IconPlane size={16}/> : opt.mode.includes("Train") ? <IconTrain size={16}/> : opt.mode.includes("Bus") ? <IconBus size={16}/> : <IconCar size={16}/>}
                </div>
                <div>
                  <div className="text-sm font-bold">{opt.mode}</div>
                  <div className="text-[10px] text-[var(--text-muted)]">{opt.time_str}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-green-400">₹{opt.cost}</div>
                <div className="text-[10px] text-[var(--text-muted)]">Score: {opt.score_overall}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function LiveAssistantFeed({ feed }) {
  if (!feed) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] h-full">
      <h3 className="text-sm font-bold mb-4 text-blue-400 flex items-center gap-2">
        <IconBrain size={18} /> Live Assistant
      </h3>
      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
        {feed.map((msg, i) => (
          <div key={i} className="flex gap-3 items-start p-3 bg-blue-900/10 border border-blue-500/20 rounded-xl">
            <div className="mt-0.5"><IconAlertTriangle size={16} className="text-blue-400" /></div>
            <div className="text-xs text-[var(--text-primary)] leading-relaxed">{msg.replace('🚨 ', '')}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LiveTimeline({ timeline }) {
  if (!timeline) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] h-full">
      <h3 className="text-sm font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconClock size={18} /> Journey Timeline
      </h3>
      <div className="space-y-4">
        {timeline.map((step, i) => (
          <div key={i} className={`flex gap-4 p-3 rounded-xl border ${step.status === 'completed' ? 'border-green-500/20 bg-green-900/10' : step.status === 'current' ? 'border-purple-500/40 bg-purple-900/20' : step.alert ? 'border-amber-500/40 bg-amber-900/10' : 'border-[var(--border-color)] bg-[var(--bg-glass)]'}`}>
            <div className="mt-1">
              {step.status === 'completed' ? <IconCheck size={16} className="text-green-500" /> : step.status === 'current' ? <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.8)]"></div> : step.alert ? <IconAlertTriangle size={16} className="text-amber-500" /> : <div className="w-4 h-4 rounded-full border-2 border-slate-600"></div>}
            </div>
            <div>
              <div className={`text-xs font-bold mb-0.5 ${step.status === 'current' ? 'text-purple-400' : step.alert ? 'text-amber-400' : 'text-[var(--text-muted)]'}`}>{step.time}</div>
              <div className={`text-sm ${step.status === 'completed' ? 'text-green-400 line-through opacity-70' : step.alert ? 'text-amber-300 font-bold' : 'text-[var(--text-primary)] font-semibold'}`}>{step.action}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function WeatherIntelligence({ weather }) {
  if (!weather) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-4 text-sky-400 flex items-center gap-2">
        <IconSun size={18} /> Route Weather
      </h3>
      <div className="flex justify-between items-center mb-6">
        {weather.stops.map((w, i) => (
          <div key={i} className="text-center flex-1">
            <div className="text-2xl mb-1">{w.icon}</div>
            <div className="text-sm font-bold">{w.temp}</div>
            <div className="text-[10px] text-[var(--text-muted)] truncate px-1">{w.location}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] flex items-center gap-2">
          <IconCloudRain size={16} className="text-blue-400" />
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Rain Prob</div>
            <div className="text-xs font-bold">{weather.rain_probability}%</div>
          </div>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] flex items-center gap-2">
          <IconEye size={16} className="text-slate-400" />
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Visibility</div>
            <div className="text-xs font-bold">{weather.visibility}</div>
          </div>
        </div>
      </div>
      <div className="bg-amber-900/20 border border-amber-500/30 p-3 rounded-xl text-xs text-amber-200">
        <div className="font-bold mb-1">AI Travel Advisory</div>
        {weather.warnings.join(" • ")}
      </div>
    </div>
  );
}

export function BudgetIntelligence({ budget }) {
  if (!budget) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-4 text-emerald-400 flex items-center gap-2">
        <IconCurrencyDollar size={18} /> Budget Intelligence
      </h3>
      <div className="text-2xl font-black text-emerald-400 mb-4">₹{budget.total.toLocaleString()} <span className="text-sm text-[var(--text-muted)] font-normal">est. total</span></div>
      
      <div className="space-y-2 mb-6">
        {Object.entries(budget.breakdown).map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)]">{k}</span>
            <span className="font-semibold">₹{v.toLocaleString()}</span>
          </div>
        ))}
      </div>
      
      <div className="space-y-2">
        <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">AI Savings Opportunities</div>
        {budget.savings.map((s, i) => (
          <div key={i} className="flex justify-between items-center bg-emerald-900/10 border border-emerald-500/20 p-2 rounded-lg text-xs">
            <span className="text-emerald-200">{s.action}</span>
            <span className="font-bold text-emerald-400">Save ₹{s.amount.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function CarbonIntelligence({ carbon }) {
  if (!carbon) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-4 text-green-400 flex items-center gap-2">
        <IconLeaf size={18} /> Carbon Footprint
      </h3>
      <div className="flex gap-4 mb-6">
        <div className="flex-1 bg-green-900/10 border border-green-500/30 p-4 rounded-xl text-center">
          <div className="text-[10px] uppercase text-green-400/70 mb-1">Emissions</div>
          <div className="text-xl font-bold text-green-400">{carbon.current}kg</div>
        </div>
        <div className="flex-1 bg-[var(--bg-glass)] border border-[var(--border-color)] p-4 rounded-xl text-center">
          <div className="text-[10px] uppercase text-[var(--text-muted)] mb-1">AI Green Score</div>
          <div className="text-xl font-bold text-[var(--text-primary)]">{carbon.score}/100</div>
        </div>
      </div>
      <div className="space-y-2">
        <div className="text-xs text-[var(--text-muted)] flex justify-between"><span>Vs Flight Alternative:</span> <span className="font-bold text-green-400">Saved {carbon.saved}kg</span></div>
        <div className="text-xs text-[var(--text-muted)] flex justify-between"><span>Equivalent Trees:</span> <span className="font-bold">🌳 {carbon.trees} trees</span></div>
        <div className="text-xs text-[var(--text-muted)] flex justify-between"><span>Saved Electricity:</span> <span className="font-bold">⚡ {carbon.electricity_kwh} kWh</span></div>
      </div>
    </div>
  );
}

export function SafetyIntelligence({ safety }) {
  if (!safety) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] h-full">
      <h3 className="text-sm font-bold mb-4 text-rose-400 flex items-center gap-2">
        <IconShield size={18} /> Safety Intelligence
      </h3>
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="text-center">
          <div className="text-3xl font-black text-rose-400 mb-1">{safety.Overall}</div>
          <div className="text-[10px] uppercase text-[var(--text-muted)]">Overall Score</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-black text-rose-400 mb-1">{safety["Women Safety"]}</div>
          <div className="text-[10px] uppercase text-[var(--text-muted)]">Women Safety</div>
        </div>
      </div>
      <div className="space-y-2 text-xs">
        <div className="flex justify-between border-b border-[var(--border-color)] pb-1"><span className="text-[var(--text-muted)]">Night Safety</span><span className="font-semibold">{safety["Night Safety"]}/100</span></div>
        <div className="flex justify-between border-b border-[var(--border-color)] pb-1"><span className="text-[var(--text-muted)]">Medical</span><span className="font-semibold">{safety["Medical Facilities"]}</span></div>
        <div className="flex justify-between border-b border-[var(--border-color)] pb-1"><span className="text-[var(--text-muted)]">Scam Risk</span><span className="font-semibold">{safety["Scam Risk"]}</span></div>
        <div className="flex justify-between pt-1"><span className="text-[var(--text-muted)]">Emergency</span><span className="font-bold text-rose-400">{safety["Emergency Numbers"]}</span></div>
      </div>
    </div>
  );
}

export function NearbyEssentials({ nearby }) {
  if (!nearby) return null;
  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
      <h3 className="text-sm font-bold mb-4 text-[var(--text-primary)] flex items-center gap-2">
        <IconBuildingSkyscraper size={18} /> Nearby Essentials
      </h3>
      <div className="space-y-3">
        {nearby.map((place, i) => (
          <div key={i} className="flex justify-between items-center p-3 bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl">
            <div>
              <div className="text-xs font-bold">{place.name}</div>
              <div className="text-[10px] text-[var(--text-muted)]">{place.type} • {place.rating} ★</div>
            </div>
            <div className="text-xs font-semibold text-purple-400">{place.dist}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function OfflineKit() {
  return (
    <div className="glass-card p-6 rounded-2xl border border-purple-500/30 bg-purple-900/10 flex flex-col items-center justify-center text-center h-full">
      <IconDownload size={32} className="text-purple-400 mb-3" />
      <h3 className="text-sm font-bold mb-2">Offline Travel Kit</h3>
      <p className="text-xs text-[var(--text-muted)] mb-4">Download maps, emergency contacts, hotel details, and tickets for offline access.</p>
      <button className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold py-3 rounded-xl transition-colors">
        Download PDF Package
      </button>
    </div>
  );
}
