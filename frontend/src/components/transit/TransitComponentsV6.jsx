import React from 'react';
import {
  IconRoute, IconSparkles, IconClock, IconAlertTriangle, 
  IconCar, IconWalk, IconPlane, IconTrain, IconBus
} from '@tabler/icons-react';

/**
 * Safe transit time formatter.
 * Never renders 'Invalid Date'. Prefers the _display string if available.
 */
export function formatTransitTime(value, displayValue) {
  if (displayValue) return displayValue;
  if (!value) return 'Unavailable';
  try {
    const d = new Date(value);
    if (isNaN(d.getTime())) return 'Unavailable';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return 'Unavailable';
  }
}

export function ModeIcon({ mode, size = 18 }) {
  const m = (mode || '').toLowerCase();
  if (m.includes('walk')) return <IconWalk size={size} />;
  if (m.includes('flight') || m.includes('air')) return <IconPlane size={size} />;
  if (m.includes('car') || m.includes('drive')) return <IconCar size={size} />;
  if (m.includes('rail') || m.includes('train')) return <IconTrain size={size} />;
  if (m.includes('bus')) return <IconBus size={size} />;
  return <IconRoute size={size} />;
}

export function AIRouteGuidanceCard({ routeGuidance }) {
  if (!routeGuidance) return null;

  return (
    <div className="glass-card p-6 rounded-3xl border border-amber-500/40 bg-[var(--bg-card)] shadow-xl space-y-4">
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/20 rounded-2xl text-amber-600 dark:text-amber-400">
            <IconSparkles size={28} />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase text-amber-600 dark:text-amber-400 tracking-widest flex items-center gap-1">
              🤖 AI Transit Strategy
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)]">{routeGuidance.title || 'Guidance Recommended'}</h3>
          </div>
        </div>
      </div>

      <p className="text-sm font-medium text-[var(--text-primary)] leading-relaxed bg-[var(--bg-glass)] p-4 rounded-xl border border-[var(--border-color)]">
        {routeGuidance.reason || 'Schedules, platforms, and fares could not be verified from live providers.'}
      </p>

      {routeGuidance.provider_status && (
        <div className="pt-2">
          <div className="text-xs uppercase tracking-widest text-[var(--text-muted)] font-bold mb-3">Provider Status</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {Object.entries(routeGuidance.provider_status).map(([provider, status]) => (
              <div key={provider} className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex items-center justify-between">
                <span className="font-bold text-xs text-[var(--text-primary)] capitalize">{provider.replace('_', ' ')}</span>
                <span className="text-[10px] font-bold text-rose-500 bg-rose-500/10 px-2 py-1 rounded">No verified itinerary</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="pt-2 text-xs text-[var(--text-secondary)]">
        <div className="font-bold mb-1">What is NOT verified:</div>
        <ul className="list-disc pl-4 space-y-0.5 opacity-80">
          <li>Airline / Provider Name</li>
          <li>Flight / Train / Bus Number</li>
          <li>Exact Fare</li>
          <li>Departure / Arrival Times</li>
          <li>Exact Duration</li>
        </ul>
      </div>
    </div>
  );
}

// ── OVERVIEW TAB ─────────────────────────────────────────────────────────────
export function OverviewTab({ routeData, activeRoute }) {
  const isRecommended = activeRoute?.route_id === routeData?.recommended_route?.route_id;
  const whyReasons = isRecommended ? routeData?.optimization?.why_this_route : [];

  return (
    <div className="space-y-6">
      {whyReasons && whyReasons.length > 0 && (
        <div className="bg-[var(--bg-card)] p-5 rounded-2xl border border-[var(--border-color)]">
          <h3 className="text-sm font-bold flex items-center gap-2 mb-3">
            <IconSparkles className="text-amber-500" size={16} /> Why this route?
          </h3>
          <ul className="space-y-2">
            {whyReasons.map((reason, idx) => (
              <li key={idx} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                <span className="text-emerald-500 font-bold mt-0.5">✓</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-[var(--bg-glass)] p-5 rounded-2xl border border-[var(--border-color)]">
        <h3 className="text-sm font-bold mb-4">Route Quality</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-1">Fastest</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">
              {(() => {
                const dur = activeRoute?.duration_min ?? activeRoute?.duration_minutes ?? activeRoute?.total_duration_min;
                if (dur != null) {
                  const h = Math.floor(dur / 60);
                  const m = Math.floor(dur % 60);
                  return h > 0 ? `${h}h ${m}m` : `${m}m`;
                }
                return activeRoute?.duration_display || 'Calculating...';
              })()}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-1">Distance</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">
              {(() => {
                const dist = activeRoute?.distance_km ?? activeRoute?.total_distance_km;
                if (dist != null) return `${dist} km`;
                return 'Calculating...';
              })()}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-1">Route Source</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">
              {activeRoute?.provider || activeRoute?.duration_source || 'OSRM (OpenStreetMap)'}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-1">Verification</div>
            <div className="text-xs font-bold text-emerald-500">
              {activeRoute?.verification_status || 'Route Calculated'}
            </div>
          </div>
        </div>
      </div>

      {activeRoute?.provider === 'RailRadar' && (
        <div className="bg-[var(--bg-card)] p-5 rounded-2xl border border-purple-500/30 space-y-4">
          <h3 className="text-sm font-bold text-purple-600 dark:text-purple-400 flex items-center gap-2">
            <IconTrain size={18} /> Train Details
          </h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Train Number</span>
              <span className="font-bold">{activeRoute.train_number || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Train Name</span>
              <span className="font-bold">{activeRoute.train_name || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">From Station</span>
              <span className="font-bold">{activeRoute.departure_station || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">To Station</span>
              <span className="font-bold">{activeRoute.arrival_station || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Departure</span>
              <span className="font-bold">{activeRoute.departure_time_display || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Arrival</span>
              <span className="font-bold">{activeRoute.arrival_time_display || 'Unavailable from current provider.'}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Operating Days</span>
              <span className="font-bold">
                {activeRoute.operating_days && activeRoute.operating_days.length > 0
                  ? activeRoute.operating_days.join(', ')
                  : 'Unavailable from current provider.'}
              </span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Live Status</span>
              <span className="font-bold">{activeRoute.live_status || 'Unavailable from current provider.'}</span>
            </div>
            {activeRoute.delay_min != null && (
              <div>
                <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Delay</span>
                <span className="font-bold text-rose-500">{activeRoute.delay_min} min</span>
              </div>
            )}
            {activeRoute.platform && (
              <div>
                <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Platform</span>
                <span className="font-bold">{activeRoute.platform}</span>
              </div>
            )}
            {activeRoute.current_station && (
              <div>
                <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Current Station</span>
                <span className="font-bold">{activeRoute.current_station}</span>
              </div>
            )}
            {activeRoute.next_station && (
              <div>
                <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block mb-1">Next Station</span>
                <span className="font-bold">{activeRoute.next_station}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── TIMELINE TAB ─────────────────────────────────────────────────────────────
export function TimelineTab({ activeRoute }) {
  if (!activeRoute) {
    return (
      <div className="p-6 bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-2xl text-center space-y-2">
        <IconAlertTriangle size={24} className="mx-auto text-amber-500" />
        <p className="text-xs text-[var(--text-primary)] font-bold">Select a journey to view the timeline.</p>
      </div>
    );
  }

  const legs = activeRoute.legs || [];
  const connections = activeRoute.connections || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm font-bold uppercase tracking-widest text-[var(--text-muted)]">
          Door-to-Door Journey Timeline
        </div>
        <div className="text-xs font-bold text-purple-600 dark:text-purple-400">
          {activeRoute.total_duration_min ? `${Math.floor(activeRoute.total_duration_min / 60)}h ${Math.floor(activeRoute.total_duration_min % 60)}m total` : ''}
        </div>
      </div>

      {legs.length === 0 ? (
        <div className="p-4 bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl text-center text-xs text-[var(--text-muted)]">
          Detailed leg information unavailable for this route.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 border-l-2 border-purple-500/40 ml-4">
          {legs.map((leg, idx) => {
            const isFirst = leg.type === 'FIRST_MILE';
            const isLast = leg.type === 'LAST_MILE';
            const legTitle = isFirst ? 'First Mile Connection' : isLast ? 'Last Mile Connection' : 'Main Transit';
            const connection = connections[idx];

            return (
              <div key={idx} className="relative">
                {/* Node marker icon */}
                <div className={`absolute -left-[35px] top-0 w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  isFirst ? 'bg-blue-100 border-blue-500 text-blue-600' :
                  isLast ? 'bg-cyan-100 border-cyan-500 text-cyan-600' :
                  'bg-purple-100 border-purple-500 text-purple-600'
                }`}>
                  <ModeIcon mode={leg.mode} size={12} />
                </div>

                {/* Card */}
                <div className="bg-[var(--bg-card)] p-4 rounded-2xl border border-[var(--border-color)] shadow-sm -mt-2 space-y-2">
                  <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-2">
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-600 border border-purple-500/20">
                      {legTitle} · {leg.mode}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">{leg.provider}</span>
                  </div>

                  {/* Departure stop */}
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-bold text-sm text-[var(--text-primary)]">{leg.from_stop || leg.from || 'Origin'}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">Depart</div>
                    </div>
                    <div className="text-xs font-bold text-purple-600 dark:text-purple-400">
                      {leg.departure_time_display || formatTransitTime(leg.departure_time, null)}
                    </div>
                  </div>

                  {/* Segment Details */}
                  <div className="pl-4 border-l border-dashed border-[var(--border-color)] py-2 my-1 space-y-1 text-xs text-[var(--text-secondary)]">
                    {leg.train_number && (
                      <div className="font-bold text-purple-600 dark:text-purple-400">
                        🚆 Train {leg.train_number} · {leg.train_name || ''}
                      </div>
                    )}
                    <div>Distance: {leg.distance_km ? `${leg.distance_km} km` : 'Calculated'}</div>
                    {leg.duration_min && <div>Duration: {Math.round(leg.duration_min)} min</div>}
                    <div className="text-[10px] text-emerald-500 font-bold">
                      {['Provider Verified','Schedule Verified','VERIFIED'].includes(leg.verification_status) ? '🟢 ' : '⚠️ '}
                      {leg.verification_status || 'Route Calculated'}
                    </div>

                    {/* Intermediate stops if main train */}
                    {leg.intermediate_stops && leg.intermediate_stops.length > 0 && (
                      <details className="mt-2 text-[11px] cursor-pointer">
                        <summary className="font-bold text-purple-500 hover:underline">
                          View {leg.intermediate_stops.length} intermediate stations
                        </summary>
                        <div className="mt-2 space-y-1 pl-2 border-l border-purple-500/20 max-h-40 overflow-y-auto">
                          {leg.intermediate_stops.map((stop, sidx) => (
                            <div key={sidx} className="flex justify-between text-[10px] text-[var(--text-muted)]">
                              <span>{stop.station_name || stop.name}</span>
                              <span>{stop.arrival_time || stop.departure_time || ''}</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>

                  {/* Arrival stop */}
                  <div className="flex justify-between items-end">
                    <div>
                      <div className="font-bold text-sm text-[var(--text-primary)]">{leg.to_stop || leg.to || 'Destination'}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">Arrive</div>
                    </div>
                    <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      {leg.arrival_time_display || formatTransitTime(leg.arrival_time, null)}
                    </div>
                  </div>
                </div>

                {/* Connection window badge between legs */}
                {connection && (
                  <div className="my-3 pl-4">
                    <div className={`p-2 rounded-xl text-xs flex items-center gap-2 border ${
                      connection.status === 'RED' ? 'bg-red-500/10 text-red-500 border-red-500/30 font-bold' :
                      connection.status === 'YELLOW' ? 'bg-amber-500/10 text-amber-500 border-amber-500/30 font-bold' :
                      'bg-emerald-500/10 text-emerald-500 border-emerald-500/30 font-medium'
                    }`}>
                      <span>{connection.status === 'RED' ? '⚠️' : connection.status === 'YELLOW' ? '⏱️' : '✓'}</span>
                      <span>
                        {connection.transfer_time_min != null
                          ? `${Math.round(connection.transfer_time_min)} min transfer window`
                          : 'Station connection'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── ROUTES TAB ───────────────────────────────────────────────────────────────
export function RoutesTab({ routeOptions, selectedRouteId, onSelect }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-[var(--border-color)] text-[var(--text-muted)] uppercase tracking-wider">
            <th className="p-3">Route</th>
            <th className="p-3">Provider</th>
            <th className="p-3 text-right">Duration</th>
            <th className="p-3 text-right">Distance</th>
            <th className="p-3 text-right">Transfers</th>
            <th className="p-3 text-right">Fare</th>
            <th className="p-3 text-center">Status</th>
          </tr>
        </thead>
        <tbody>
          {routeOptions.map((route, idx) => (
            <tr 
              key={idx} 
              onClick={() => onSelect(route.route_id)}
              className={`border-b border-[var(--border-color)] cursor-pointer hover:bg-[var(--bg-glass)] transition-all ${selectedRouteId === route.route_id ? 'bg-purple-500/10' : ''}`}
            >
              <td className="p-3 font-bold text-[var(--text-primary)] flex items-center gap-2">
                <ModeIcon mode={route.mode} size={14} /> {route.mode}
              </td>
              <td className="p-3 text-[var(--text-secondary)]">{route.provider}</td>
              <td className="p-3 text-right font-bold">{route.duration_min}m</td>
              <td className="p-3 text-right">{route.distance_km} km</td>
              <td className="p-3 text-right">{route.transfers !== null ? route.transfers : '—'}</td>
              <td className="p-3 text-right text-emerald-500 font-bold">{route.fare ? `₹${route.fare}` : 'Unavailable'}</td>
              <td className="p-3 text-center">
                {['Provider Verified', 'Schedule Verified', 'VERIFIED'].includes(route.verification_status)
                  ? <span className="text-emerald-500">🟢 {route.verification_status}</span>
                  : <span className="text-amber-500">⚠️ {route.verification_status || 'Estimated'}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── STRATEGY TAB ─────────────────────────────────────────────────────────────
export function StrategyTab({ routeData }) {
  const VERIFIED = ['Provider Verified', 'Schedule Verified', 'VERIFIED', 'Partially Verified'];

  const renderCard = (title, route, condition, icon, accentClass = '') => (
    <div className={`bg-[var(--bg-glass)] p-4 rounded-2xl border ${accentClass || 'border-[var(--border-color)]'}`}>
      <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-2 flex items-center gap-1">
        {icon} {title}
      </div>
      {route ? (
        <>
          <div className="font-bold text-sm text-[var(--text-primary)] mb-1">{route.provider}</div>
          <div className="text-xs text-[var(--text-secondary)] mb-1">{condition}</div>
          <div className={`text-[10px] font-bold ${VERIFIED.includes(route.verification_status) ? 'text-emerald-500' : 'text-amber-500'}`}>
            {VERIFIED.includes(route.verification_status) ? '🟢' : '⚠️'} {route.verification_status || 'Estimated'}
          </div>
        </>
      ) : (
        <>
          <div className="font-bold text-sm text-[var(--text-primary)] mb-1">Cannot determine</div>
          <div className="text-xs text-[var(--text-secondary)] mb-1">{condition}</div>
        </>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-[var(--text-primary)]">Route Comparison</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {renderCard('Fastest', routeData?.fastest_route,
          routeData?.fastest_route?.duration_min
            ? `${Math.floor(routeData.fastest_route.duration_min / 60)}h ${Math.floor(routeData.fastest_route.duration_min % 60)}m`
            : 'Duration unavailable', '⚡')}

        {renderCard('Cheapest', routeData?.cheapest_route,
          routeData?.cheapest_route?.fare
            ? `₹${routeData.cheapest_route.fare}`
            : 'Cannot determine — fare unavailable for all routes', '💰')}

        {renderCard('Least Walking', routeData?.least_walking_route,
          routeData?.least_walking_route?.walking_distance_m != null
            ? `${(routeData.least_walking_route.walking_distance_m / 1000).toFixed(1)} km walking`
            : 'Cannot determine — walking data unavailable', '🚶')}

        {renderCard('Safest Connection', routeData?.safest_route,
          routeData?.safest_route
            ? `${routeData.safest_route.transfers ?? 0} transfer${(routeData.safest_route.transfers ?? 0) !== 1 ? 's' : ''} · ${VERIFIED.includes(routeData.safest_route.verification_status) ? 'Verified schedule' : 'Schedule estimated'}`
            : 'Cannot determine', '🛡️')}

        {renderCard('Greenest', routeData?.greenest_route,
          routeData?.greenest_route?.distance_km
            ? `${routeData.greenest_route.distance_km} km · ${routeData.greenest_route.mode || 'Transit'}`
            : 'Cannot determine — distance unavailable', '🌿')}

        {renderCard('Fewest Transfers', routeData?.fewest_transfers_route,
          routeData?.fewest_transfers_route != null
            ? `${routeData.fewest_transfers_route.transfers ?? 0} transfer${(routeData.fewest_transfers_route.transfers ?? 0) !== 1 ? 's' : ''}`
            : 'Cannot determine', '🔀')}

        {/* Best Overall — special card */}
        <div className="col-span-full bg-[var(--bg-glass)] p-4 rounded-2xl border border-amber-500/30">
          <div className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-2 flex items-center gap-1">
            ⭐ Best Overall
          </div>
          <div className="font-bold text-sm text-[var(--text-primary)] mb-1">{routeData?.best_overall_route?.provider || 'Unknown'}</div>
          <div className="text-xs text-[var(--text-secondary)] mb-2">Selected because:</div>
          <ul className="text-[10px] text-[var(--text-secondary)] space-y-1 pl-2 border-l-2 border-amber-500/30">
            {routeData?.optimization?.why_this_route?.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}


// ── WEATHER TAB ──────────────────────────────────────────────────────────────
export function WeatherSafetyTab({ weatherObj, origin, dest }) {
  if (!weatherObj?.stops) return <div className="text-xs p-4">Weather data unavailable.</div>;
  
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {weatherObj.stops.map((stop, idx) => (
          <div key={idx} className="bg-[var(--bg-glass)] p-4 rounded-2xl border border-[var(--border-color)]">
            <h4 className="text-xs font-bold uppercase text-[var(--text-muted)] mb-2 tracking-widest">
              {idx === 0 ? 'Departure' : 'Destination'}
            </h4>
            <div className="flex items-center gap-4">
              <div className="text-4xl">{stop.icon}</div>
              <div>
                <div className="font-bold text-[var(--text-primary)]">{stop.location}</div>
                <div className="text-sm font-bold text-purple-600">{stop.temp}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="bg-blue-500/10 p-4 rounded-2xl border border-blue-500/20">
        <h4 className="text-xs font-bold text-blue-600 uppercase mb-2 tracking-widest">💡 Travel Recommendation</h4>
        <p className="text-xs text-[var(--text-secondary)]">
          {weatherObj.recommendation || 'No specific travel recommendations based on current weather.'}
        </p>
      </div>
    </div>
  );
}

// ── BUDGET TAB ───────────────────────────────────────────────────────────────
export function BudgetAnalyticsTab({ activeRoute }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-[var(--text-primary)]">Journey Cost</h3>
      
      <div className="bg-[var(--bg-card)] p-4 rounded-2xl border border-[var(--border-color)] space-y-4">
        <div className="flex justify-between items-center pb-4 border-b border-[var(--border-color)]">
          <div>
            <div className="font-bold text-sm flex items-center gap-2">
              <ModeIcon mode={activeRoute?.mode} size={16} /> Transit Fare
            </div>
            <div className="text-xs text-[var(--text-muted)]">{activeRoute?.provider}</div>
          </div>
          <div className="text-right">
            <div className="font-bold text-lg text-[var(--text-primary)]">
              {activeRoute?.fare ? `₹${activeRoute.fare}` : 'Unavailable'}
            </div>
            <div className="text-[10px] font-bold text-emerald-500">
              {activeRoute?.fare_source}
            </div>
          </div>
        </div>
        
        <div className="flex justify-between items-center pb-4 border-b border-[var(--border-color)]">
          <div>
            <div className="font-bold text-sm">Additional costs</div>
            <div className="text-xs text-[var(--text-muted)]">Tolls, Fuel, etc.</div>
          </div>
          <div className="text-right text-xs font-bold text-[var(--text-muted)]">
            Unavailable
          </div>
        </div>
        
        <div className="flex justify-between items-center pt-2">
          <div className="font-black text-sm">Total verified transport cost</div>
          <div className="font-black text-xl text-emerald-600">
            {activeRoute?.fare ? `₹${activeRoute.fare}` : 'Unavailable'}
          </div>
        </div>
      </div>
      
      {!activeRoute?.fare && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-600">
          ⚠️ No verified monetary cost is available from {activeRoute?.provider}. WanderWise does not invent fuel or toll costs.
        </div>
      )}
    </div>
  );
}

// ── NEARBY TAB ───────────────────────────────────────────────────────────────
export function NearbyTab({ nearby, provenance }) {
  if (!nearby || nearby.length === 0) {
    return <div className="text-xs p-4">Nearby infrastructure data unavailable.</div>;
  }

  // Group by category loosely based on simple rules
  const grouped = {
    Transit: [],
    Food: [],
    Essentials: []
  };

  nearby.forEach(poi => {
    const cat = poi.category || poi.type || '';
    if (cat.toLowerCase().includes('rail') || cat.toLowerCase().includes('bus') || cat.toLowerCase().includes('station')) {
      grouped.Transit.push(poi);
    } else if (cat.toLowerCase().includes('restaurant') || cat.toLowerCase().includes('cafe')) {
      grouped.Food.push(poi);
    } else {
      grouped.Essentials.push(poi);
    }
  });

  return (
    <div className="space-y-6">
      <div className="bg-[var(--bg-glass)] p-4 rounded-2xl border border-[var(--border-color)] text-xs space-y-2">
        <div className="flex justify-between">
          <span className="font-bold text-[var(--text-muted)] uppercase">Reference Point</span>
          <span className="font-bold text-[var(--text-primary)]">{provenance?.reference_name || 'Unknown'}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-bold text-[var(--text-muted)] uppercase">Source</span>
          <span className="font-bold text-[var(--text-primary)]">{provenance?.source || 'Fallback Geocoding'}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-bold text-[var(--text-muted)] uppercase">Verification</span>
          <span className="font-bold text-emerald-500">{provenance?.verified ? '🟢 Verified' : '🟡 Estimated Fallback'}</span>
        </div>
      </div>

      {!provenance?.verified && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-[10px] font-bold text-amber-600">
          ⚠️ Exact boarding point unavailable from selected provider. Showing verified infrastructure near {provenance?.reference_name}.
        </div>
      )}

      {Object.entries(grouped).map(([category, items]) => {
        if (items.length === 0) return null;
        return (
          <div key={category} className="space-y-3">
            <h4 className="text-sm font-bold border-b border-[var(--border-color)] pb-2">{category}</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {items.map((poi, idx) => (
                <div key={idx} className="bg-[var(--bg-card)] p-3 rounded-xl border border-[var(--border-color)] flex justify-between items-center">
                  <div>
                    <div className="font-bold text-xs text-[var(--text-primary)] truncate max-w-[150px]">{poi.name}</div>
                    <div className="text-[10px] text-[var(--text-muted)]">{poi.type || poi.category} · {poi.distance_km} km</div>
                  </div>
                  {poi.verified && <span className="text-[10px] text-emerald-500 font-bold bg-emerald-500/10 px-2 py-1 rounded">🟢 Verified</span>}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── LEGACY EXPORTS FOR ACTIVE_TRIP.JSX ───────────────────────────────────────
export function RouteOptionsTab({ routeData }) {
  return <div className="p-4 bg-[var(--bg-glass)] rounded-2xl">Route details available in Transit Planner.</div>;
}

export function AIAnalysisTab({ routeData }) {
  return <div className="p-4 bg-[var(--bg-glass)] rounded-2xl">AI Strategy available in Transit Planner.</div>;
}

export function FloatingAIAssistant() {
  return null;
}
