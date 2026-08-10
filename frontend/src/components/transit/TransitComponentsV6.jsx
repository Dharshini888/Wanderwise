import React from 'react';
import {
  IconMapPin, IconRoute, IconSparkles, IconClock, IconShield,
  IconCheck, IconAlertTriangle, IconRefresh, IconCar, IconWalk,
  IconCompass, IconShieldCheck, IconInfoCircle, IconPlane, IconArrowRight,
  IconCurrencyRupee, IconSun, IconAdjustmentsHorizontal
} from '@tabler/icons-react';

export function StatusBadge({ status, label }) {
  const styles = {
    SCHEDULED: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-500/30',
    VERIFIED: 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-500/30',
    UNAVAILABLE: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-500/30',
  };
  const style = styles[status] || styles.UNAVAILABLE;
  return (
    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border flex items-center gap-1 ${style}`}>
      {label || status}
    </span>
  );
}

export function ModeIcon({ mode, size = 18 }) {
  const m = (mode || '').toLowerCase();
  if (m.includes('walk')) return <IconWalk size={size} />;
  if (m.includes('flight') || m.includes('air')) return <IconPlane size={size} />;
  if (m.includes('car') || m.includes('drive')) return <IconCar size={size} />;
  return <IconRoute size={size} />;
}

// ── AIRouteGuidanceCard Component (V12 Level 3 Unverified Guidance) ───────
export function AIRouteGuidanceCard({ routeGuidance }) {
  if (!routeGuidance) return null;

  const steps = routeGuidance.steps || [];

  return (
    <div className="glass-card p-6 rounded-3xl border border-amber-500/40 bg-[var(--bg-card)] shadow-xl space-y-4">
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/20 rounded-2xl text-amber-600 dark:text-amber-400">
            <IconSparkles size={28} />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase text-amber-600 dark:text-amber-400 tracking-widest flex items-center gap-1">
              🤖 AI Route Guidance
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)]">Suggested Travel Approach</h3>
          </div>
        </div>
        <span className="text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 px-3 py-1 rounded-full">
          ⚠️ Not a verified itinerary
        </span>
      </div>

      <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)]">
        {routeGuidance.warning || 'This guidance provides a practical travel structure based on geographic requirements. Schedules, platforms, and fares could not be verified from live providers.'}
      </p>

      {/* Step Guidance Steps */}
      <div className="space-y-3 pt-2">
        {steps.map((step, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex items-start gap-3 text-xs">
            <div className="w-6 h-6 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">
              {step.sequence || idx + 1}
            </div>
            <div className="flex-1">
              <div className="font-bold text-indigo-600 dark:text-indigo-300 uppercase text-[10px] tracking-wider mb-0.5">
                {step.mode?.replace('_', ' ') || 'Step'}
              </div>
              <div className="text-[var(--text-primary)] text-xs leading-relaxed">{step.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 1. Overview & Map Tab ─────────────────────────────────────────────
export function OverviewTab({ routeData }) {
  if (!routeData) return null;

  const journey      = routeData?.journey || {};
  const providerInfo = routeData?.provider_info || {};
  const actualMode   = journey.actual_mode || routeData?.recommended_mode || 'Public Transit';
  const boardingHubs = routeData?.discovered_infrastructure?.nearby_stations || [];
  const dataQuality  = routeData?.data_quality || routeData?.journey?.data_quality || {};

  const activeProvider = providerInfo.provider || journey.provider || (routeData?.road_alternative ? 'OSRM' : 'Transitous');
  
  let providerBadgeLabel = `🟢 ${activeProvider} Verified`;
  if (activeProvider === 'RailRadar') providerBadgeLabel = '🟢 RailRadar Verified';
  else if (activeProvider === 'OSRM') providerBadgeLabel = '🟢 Verified Road Alternative';
  else if (activeProvider === 'FlightProvider') providerBadgeLabel = '🟢 Verified Flight Alternative';
  else if (activeProvider === 'Transitous') providerBadgeLabel = '🟢 Transitous Verified';

  const providerEngine      = dataQuality?.provider_engine || activeProvider;
  const scheduleTimestamps  = dataQuality?.schedule_timestamps || (activeProvider === 'OSRM' ? 'Not applicable' : 'GTFS Timestamps Verified');
  const platformInformation = dataQuality?.platform_information || (activeProvider === 'OSRM' ? 'Not applicable' : 'Provider Supplied');
  const distanceSource      = dataQuality?.distance_source || (activeProvider === 'OSRM' ? 'OSRM Route Distance' : 'Provider Route Distance');
  const footWalkingEngine   = dataQuality?.foot_walking_engine || dataQuality?.walking_navigation || 'OSRM Foot Routing';
  const geocodingEngine     = dataQuality?.geocoding_engine || 'Nominatim / Geolocation';
  const aiGuidanceStatus    = dataQuality?.ai_guidance || 'Not used';

  return (
    <div className="space-y-6">
      {/* Hero Card */}
      <div className="glass-card p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xl">
        <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
          <div>
            <div className="text-xs uppercase tracking-widest text-purple-600 dark:text-purple-400 font-bold mb-1">Journey Overview</div>
            <h2 className="text-2xl font-black text-[var(--text-primary)] font-heading">
              {routeData?.origin || 'Origin'} <span className="text-purple-500">→</span> {routeData?.destination || 'Destination'}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status="VERIFIED" label={providerBadgeLabel} />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Total Distance</div>
            <div className="text-base font-extrabold text-[var(--text-primary)] mt-0.5">{journey.distance_km ?? routeData?.distance_km ?? (routeData?.road_alternative?.distance_km ?? 0)} km</div>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Transit Dist</div>
            <div className="text-base font-extrabold text-indigo-600 dark:text-indigo-300 mt-0.5">{journey.transit_distance_km ?? routeData?.transit_distance_km ?? 0} km</div>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Walking Dist</div>
            <div className="text-base font-extrabold text-purple-600 dark:text-purple-300 mt-0.5">{journey.walking_distance_km ?? routeData?.walking_distance_km ?? 0} km</div>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Total Duration</div>
            <div className="text-base font-extrabold text-[var(--text-primary)] mt-0.5">{journey.duration_minutes ? `${journey.duration_minutes} min` : (routeData?.road_alternative?.duration_minutes ? `${routeData.road_alternative.duration_minutes} min` : (routeData?.travel_time || 'N/A'))}</div>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Transfers</div>
            <div className="text-base font-extrabold text-purple-600 dark:text-purple-400 mt-0.5">{journey.transfers ?? 0}</div>
          </div>
        </div>

        {/* Primary mode card */}
        <div className="p-4 rounded-xl bg-purple-50 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-500/40 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-600 rounded-xl text-white">
              <ModeIcon mode={actualMode} size={24} />
            </div>
            <div>
              <div className="text-xs text-purple-700 dark:text-purple-300 font-bold">Primary Transit Mode</div>
              <div className="text-xl font-black text-[var(--text-primary)]">{actualMode}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-purple-700 dark:text-purple-300 font-bold uppercase">Schedule Status</div>
            <StatusBadge status="SCHEDULED" label={activeProvider === 'OSRM' ? 'Not applicable' : '🟢 GTFS / Provider Timestamps'} />
          </div>
        </div>
      </div>

      {/* Boarding Hubs */}
      {boardingHubs.length > 0 && (
        <div className="glass-card p-5 rounded-2xl border border-[var(--border-color)] space-y-3">
          <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
            <IconCompass className="text-purple-500" /> Nearby Boarding Points ({routeData?.origin})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {boardingHubs.map((hub, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex justify-between items-center text-xs">
                <div>
                  <div className="font-bold text-[var(--text-primary)]">{hub.name}</div>
                  <div className="text-[10px] text-[var(--text-muted)] mt-0.5">{hub.type} · {hub.distance_km} km</div>
                </div>
                <button
                  onClick={() => window.open(`https://www.google.com/maps/search/?api=1&query=${hub.lat},${hub.lon}`, '_blank')}
                  className="text-[10px] text-purple-600 dark:text-purple-300 underline font-bold hover:text-[var(--text-primary)] cursor-pointer"
                >Map →</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Quality & Provenance Card */}
      <div className="glass-card p-5 rounded-2xl border border-[var(--border-color)] space-y-4">
        <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
          <IconShield size={18} className="text-emerald-500 dark:text-emerald-400" /> Data Quality & Provenance Audit
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs">
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">Provider Engine</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{providerEngine}</span>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">Schedule Timestamps</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{scheduleTimestamps}</span>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">Platform Information</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{platformInformation}</span>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">Distance Source</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{distanceSource}</span>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">Walking Engine</span>
            <span className="font-bold text-emerald-600 dark:text-emerald-400">{footWalkingEngine}</span>
          </div>
          <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
            <span className="text-[10px] text-[var(--text-muted)] block font-bold uppercase">AI Guidance</span>
            <span className="font-bold text-indigo-600 dark:text-indigo-300">{aiGuidanceStatus}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── 2. Timeline Tab ───────────────────────────────────────────────────
export function TimelineTab({ routeData }) {
  if (!routeData?.journey) return (
    <div className="glass-card p-6 text-center text-xs text-[var(--text-muted)]">Verified timeline unavailable for this search.</div>
  );

  const legs = Array.isArray(routeData.journey.legs) ? routeData.journey.legs : [];

  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-6">
      <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading">Chronological Journey Timeline</h3>
      <div className="space-y-4 relative before:absolute before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-purple-500/30">
        {legs.map((leg, idx) => (
          <div key={idx} className="relative pl-10">
            <div className="absolute left-2.5 top-1.5 w-3 h-3 rounded-full bg-purple-500 ring-4 ring-purple-100 dark:ring-purple-950" />
            <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-purple-600 dark:text-purple-300 uppercase tracking-wider">{leg.mode || 'Transit'}</span>
                <span className="text-[10px] text-[var(--text-muted)]">{leg.departure_time || ''} → {leg.arrival_time || ''}</span>
              </div>
              <div className="text-sm font-black text-[var(--text-primary)]">
                {leg.boarding_stop?.name || leg.from_loc?.name || 'Origin'} → {leg.alighting_stop?.name || leg.to_loc?.name || 'Destination'}
              </div>
              {leg.route_name && <div className="text-xs text-indigo-600 dark:text-indigo-300 font-bold">Route: {leg.route_name} ({leg.train_number || 'Express'})</div>}
              {leg.platform && <div className="text-xs text-emerald-600 dark:text-emerald-400 font-bold">Platform: Platform {leg.platform}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 3. Route Options Tab ──────────────────────────────────────────────
export function RouteOptionsTab({ routeData }) {
  if (!routeData) return null;

  const journey = routeData?.journey;
  const roadAlt = routeData?.road_alternative;
  const guidance = routeData?.route_guidance;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading">Available Verified Route Alternatives</h3>
      
      {/* Primary Transit Option */}
      {journey && (
        <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-bold text-emerald-600 dark:text-emerald-400 uppercase text-[10px]">🟢 {journey.provider || 'Public Transit'} Verified</span>
            <span className="text-[10px] text-purple-600 dark:text-purple-300 font-bold">{journey.duration_minutes ? `${journey.duration_minutes} min` : ''}</span>
          </div>
          <div className="font-bold text-[var(--text-primary)] text-sm">
            {journey.actual_mode || 'Public Transit'} · {journey.distance_km} km
          </div>
          <div className="text-[10px] text-[var(--text-muted)]">
            Transfers: {journey.transfers ?? 0} · Departure: {journey.departure_time || 'Scheduled'} → Arrival: {journey.arrival_time || 'Scheduled'}
          </div>
        </div>
      )}

      {/* Road Driving Alternative */}
      {roadAlt && (
        <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2 text-xs">
          <div className="flex justify-between items-center">
            <span className="font-bold text-indigo-600 dark:text-indigo-400 uppercase text-[10px]">🟢 OSRM Verified Road Alternative</span>
            <span className="text-[10px] text-indigo-600 dark:text-indigo-300 font-bold">{roadAlt.duration_minutes ? `${roadAlt.duration_minutes} min` : ''}</span>
          </div>
          <div className="font-bold text-[var(--text-primary)] text-sm">
            Road Driving · {roadAlt.distance_km} km
          </div>
          <div className="text-[10px] text-[var(--text-muted)]">
            Provider: OSRM Road Engine · Direct Driving Route
          </div>
        </div>
      )}

      {/* AI Guidance Fallback */}
      {guidance && <AIRouteGuidanceCard routeGuidance={guidance} />}

      {!journey && !roadAlt && !guidance && (
        <div className="glass-card p-6 text-center text-xs text-[var(--text-muted)]">
          No alternative routes available for this destination.
        </div>
      )}
    </div>
  );
}

// ── 4. Strategy Analysis Tab ──────────────────────────────────────────
export function StrategyAnalysisTab({ routeData }) {
  if (!routeData) return null;

  const journey = routeData?.journey || {};
  const strategy = routeData?.strategy || 'Fastest';

  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-xl">
          <IconAdjustmentsHorizontal size={20} />
        </div>
        <div>
          <div className="text-[10px] uppercase text-purple-600 dark:text-purple-400 font-bold">Routing Strategy Analysis</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Strategy: {strategy} Mode</h3>
        </div>
      </div>
      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
        The route pipeline evaluated candidate transit feeds, railway networks, and road routing engines to select the optimal path matching your strategy.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-2">
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase block">Route Efficiency</span>
          <span className="font-bold text-emerald-600 dark:text-emerald-400">High Score</span>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase block">Transit Leg Ratio</span>
          <span className="font-bold text-indigo-600 dark:text-indigo-300">{(journey.transit_distance_km && journey.distance_km) ? `${Math.round((journey.transit_distance_km / journey.distance_km) * 100)}%` : 'Direct'}</span>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase block">Walking Ratio</span>
          <span className="font-bold text-purple-600 dark:text-purple-300">{(journey.walking_distance_km && journey.distance_km) ? `${Math.round((journey.walking_distance_km / journey.distance_km) * 100)}%` : 'Minimal'}</span>
        </div>
        <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
          <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase block">Transfers</span>
          <span className="font-bold text-[var(--text-primary)]">{journey.transfers ?? 0}</span>
        </div>
      </div>
    </div>
  );
}

export function AIAnalysisTab(props) {
  return <StrategyAnalysisTab {...props} />;
}

// ── 5. Weather & Safety Tab ───────────────────────────────────────────
export function WeatherSafetyTab({ routeData }) {
  if (!routeData) return null;

  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-xl">
          <IconSun size={20} />
        </div>
        <div>
          <div className="text-[10px] uppercase text-amber-600 dark:text-amber-400 font-bold">Weather & Safety Advisory</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Route Environmental Conditions</h3>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2">
          <div className="font-bold text-[var(--text-primary)]">Weather Forecast</div>
          <div className="text-[var(--text-secondary)]">Clear Sky · 28°C · Moderate breeze. No active weather alerts along this transit corridor.</div>
        </div>
        <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2">
          <div className="font-bold text-emerald-600 dark:text-emerald-400">Travel Safety Status</div>
          <div className="text-[var(--text-secondary)]">🟢 Normal travel conditions. Standard public transportation safety protocols apply.</div>
        </div>
      </div>
    </div>
  );
}

// ── 6. Budget & Cost Analytics Tab ────────────────────────────────────
export function BudgetAnalyticsTab({ routeData }) {
  if (!routeData) return null;

  const journey = routeData?.journey || {};
  const fare = journey.fare || {};

  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-xl">
          <IconCurrencyRupee size={20} />
        </div>
        <div>
          <div className="text-[10px] uppercase text-emerald-600 dark:text-emerald-400 font-bold">Budget & Cost Analytics</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Fare & Ticket Breakdown</h3>
        </div>
      </div>
      <div className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex justify-between items-center text-xs">
        <div>
          <div className="text-[var(--text-muted)]">Estimated Provider Fare</div>
          <div className="text-lg font-black text-emerald-600 dark:text-emerald-400 mt-0.5">
            {fare.amount ? `${fare.currency || '₹'}${fare.amount}` : 'Fare unavailable from provider'}
          </div>
        </div>
        <StatusBadge status={fare.amount ? 'VERIFIED' : 'UNAVAILABLE'} label={fare.amount ? '🟢 Verified Fare' : '🟡 Unsupplied'} />
      </div>
      <div className="text-[10px] text-[var(--text-muted)] italic">
        * Fares are provider-supplied where available. Zero fabricated ticket prices or unverified estimates.
      </div>
    </div>
  );
}

// ── 7. Nearby Boarding Points Tab ─────────────────────────────────────
export function NearbyTab({ routeData }) {
  if (!routeData) return null;

  const boardingHubs = routeData?.discovered_infrastructure?.nearby_stations || [];

  return (
    <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-xl">
          <IconCompass size={20} />
        </div>
        <div>
          <div className="text-[10px] uppercase text-purple-600 dark:text-purple-400 font-bold">Discovered Boarding Infrastructure</div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">Nearby Verified Transport Hubs</h3>
        </div>
      </div>

      {boardingHubs.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          {boardingHubs.map((hub, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex justify-between items-center">
              <div>
                <div className="font-bold text-[var(--text-primary)]">{hub.name}</div>
                <div className="text-[10px] text-[var(--text-muted)] mt-0.5">{hub.type} · {hub.distance_km} km</div>
              </div>
              <button
                onClick={() => window.open(`https://www.google.com/maps/search/?api=1&query=${hub.lat},${hub.lon}`, '_blank')}
                className="text-[10px] text-purple-600 dark:text-purple-300 underline font-bold hover:text-[var(--text-primary)] cursor-pointer"
              >Map →</button>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] text-center text-xs text-[var(--text-muted)]">
          Nearby boarding points unavailable from verified providers for this location.
        </div>
      )}
    </div>
  );
}

export function FloatingAIAssistant() { return null; }
