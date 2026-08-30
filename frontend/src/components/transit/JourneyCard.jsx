/**
 * JourneyCard.jsx — Google-Maps-style journey card for WanderWise
 * 
 * Renders a single door-to-door journey with expandable legs, connection
 * gaps, and verification badges. Selection updates map + timeline.
 *
 * Truth-First: Only displays backend-provided data. Never calculates
 * transit facts. All "Unavailable" states are shown explicitly.
 */

import React, { useState } from 'react';

const MODE_ICONS = {
  train: '🚆', rail: '🚆', railway: '🚆',
  bus: '🚌', metro: '🚇', subway: '🚇',
  tram: '🚃', walk: '🚶', walking: '🚶',
  flight: '✈️', air: '✈️', road: '🚗',
  car: '🚗', driving: '🚗', ferry: '⛴️',
};

function modeIcon(mode) {
  if (!mode) return '🚌';
  const m = mode.toLowerCase();
  for (const [key, icon] of Object.entries(MODE_ICONS)) {
    if (m.includes(key)) return icon;
  }
  return '🚌';
}

function modeColor(mode) {
  if (!mode) return 'var(--text-muted)';
  const m = mode.toLowerCase();
  if (m.includes('train') || m.includes('rail')) return '#9333ea';
  if (m.includes('bus')) return '#2563eb';
  if (m.includes('walk')) return '#6b7280';
  if (m.includes('metro') || m.includes('subway')) return '#0891b2';
  if (m.includes('flight') || m.includes('air')) return '#0ea5e9';
  if (m.includes('road') || m.includes('car') || m.includes('driv')) return '#d97706';
  if (m.includes('ferry')) return '#059669';
  return '#7c3aed';
}

function ConnectionGap({ connection }) {
  if (!connection) return null;
  const status = connection.status || 'UNKNOWN';
  const mins = connection.transfer_time_min;
  const colors = { GREEN: '#10b981', YELLOW: '#f59e0b', RED: '#ef4444', UNKNOWN: '#6b7280' };
  const color = colors[status] || colors.UNKNOWN;
  return (
    <div className="flex items-center gap-2 my-1 pl-6 text-xs" style={{ color }}>
      <div className="w-px h-4 ml-2" style={{ background: color, opacity: 0.4 }} />
      <span className="font-medium">
        {status === 'RED' ? '⚠️ ' : status === 'YELLOW' ? '⏱ ' : '✓ '}
        {mins != null ? `${Math.round(mins)} min transfer` : 'Transfer — schedule data unavailable'}
      </span>
    </div>
  );
}

function LegRow({ leg, connection }) {
  const icon = modeIcon(leg.mode);
  const color = modeColor(leg.mode);
  const legType = (leg.type || 'MAIN_TRANSIT').replace('_', ' ');

  const typeColorClass = leg.type === 'FIRST_MILE'
    ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30'
    : leg.type === 'LAST_MILE'
    ? 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 border-cyan-500/30'
    : 'bg-purple-500/20 text-purple-600 dark:text-purple-400 border-purple-500/30';

  return (
    <div className="text-xs mb-2 p-2 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
      {/* Header row with leg type badge */}
      <div className="flex items-center justify-between mb-1.5">
        <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider border ${typeColorClass}`}>
          {legType}
        </span>
        <span className="text-[10px] text-[var(--text-muted)] font-mono">
          {leg.provider || 'OSRM'}
        </span>
      </div>

      {/* Departure row */}
      <div className="flex items-center gap-2">
        <span className="font-bold w-16 text-right shrink-0" style={{ color }}>
          {leg.departure_time_display || '—'}
        </span>
        <span className="text-lg">{icon}</span>
        <div>
          <span className="font-semibold text-[var(--text-primary)]">{leg.from_stop || leg.from || 'Origin'}</span>
          {leg.train_number && (
            <span className="ml-2 text-[10px] text-purple-500 font-bold">
              {leg.train_number} {leg.train_name ? `· ${leg.train_name}` : ''}
            </span>
          )}
          {leg.route_number && !leg.train_number && (
            <span className="ml-2 text-[10px] text-blue-500 font-bold">#{leg.route_number}</span>
          )}
        </div>
      </div>

      {/* Mode line */}
      <div className="flex items-stretch gap-2 my-1">
        <div className="w-16 shrink-0" />
        <div className="w-px ml-[9px] my-0.5" style={{ background: color, opacity: 0.3 }} />
        <div className="flex flex-col justify-center pl-1 text-[10px] text-[var(--text-muted)] space-y-0.5">
          <span>{leg.mode} · {leg.duration_min ? `${Math.round(leg.duration_min)} min` : ''} {leg.distance_km ? `(${leg.distance_km} km)` : ''}</span>
          <span className={
            ['Provider Verified','Schedule Verified','VERIFIED'].includes(leg.verification_status)
              ? 'text-emerald-500 font-bold'
              : 'text-amber-500'
          }>
            {['Provider Verified','Schedule Verified','VERIFIED'].includes(leg.verification_status)
              ? '🟢 ' : '⚠️ '}
            {leg.verification_status || 'Estimated'}
          </span>
        </div>
      </div>

      {/* Arrival row */}
      <div className="flex items-center gap-2">
        <span className="font-bold w-16 text-right shrink-0" style={{ color }}>
          {leg.arrival_time_display || '—'}
          {leg.is_overnight && <span className="text-[9px] ml-0.5 text-orange-500">+1</span>}
        </span>
        <div className="text-lg opacity-30">·</div>
        <span className="font-semibold text-[var(--text-primary)]">{leg.to_stop || leg.to || 'Destination'}</span>
      </div>

      {/* Connection gap to next leg */}
      {connection && <ConnectionGap connection={connection} />}
    </div>
  );
}

export default function JourneyCard({
  journey,
  isSelected,
  isBestOverall,
  isFastest,
  isCheapest,
  isSafest,
  isGreenest,
  isFewestTransfers,
  onSelect,
}) {
  const [expanded, setExpanded] = useState(isSelected);
  const legs = journey.legs || [];
  const connections = journey.connections || [];

  const verifiedStatuses = ['Provider Verified', 'Schedule Verified', 'VERIFIED', 'Partially Verified'];

  const tags = [];
  if (isBestOverall) tags.push({ label: '⭐ Best Overall', cls: 'bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30' });
  if (isFastest) tags.push({ label: '⚡ Fastest', cls: 'bg-purple-500/20 text-purple-600 dark:text-purple-400 border border-purple-500/30' });
  if (isCheapest) tags.push({ label: '💰 Cheapest', cls: 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' });
  if (isSafest) tags.push({ label: '🛡️ Safest', cls: 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-500/30' });
  if (isGreenest) tags.push({ label: '🌿 Greenest', cls: 'bg-green-500/20 text-green-600 dark:text-green-400 border border-green-500/30' });
  if (isFewestTransfers) tags.push({ label: '🔀 Fewest Transfers', cls: 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30' });

  const totalDur = journey.total_duration_min ?? journey.duration_min;
  const durH = totalDur != null ? `${Math.floor(totalDur / 60)}h ${Math.floor(totalDur % 60)}m` : null;

  // Mode summary for collapsed view
  const modeSummary = legs.map(l => modeIcon(l.mode)).join(' → ');

  const verificationStatus = journey.verification_status || 'Estimated';
  const isVerified = verifiedStatuses.includes(verificationStatus);

  return (
    <div
      className={`rounded-2xl border transition-all cursor-pointer ${
        isSelected
          ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/10'
          : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:border-purple-500/40'
      }`}
      onClick={() => { onSelect(journey.route_id || journey.journey_id); setExpanded(true); }}
    >
      {/* Header */}
      <div className="p-4">
        {/* Tags row */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {tags.map((t, i) => (
              <span key={i} className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${t.cls}`}>
                {t.label}
              </span>
            ))}
          </div>
        )}

        {/* Top summary row */}
        <div className="flex items-center justify-between mb-3">
          <div className="text-base font-bold text-[var(--text-primary)]">
            {durH ? durH : 'Duration unavailable'}
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className={isVerified ? 'text-emerald-500 font-bold' : 'text-amber-500'}>
              {isVerified ? '🟢' : '⚠️'} {verificationStatus}
            </span>
            <button
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors ml-1"
              onClick={e => { e.stopPropagation(); setExpanded(x => !x); }}
            >
              {expanded ? '▲' : '▼'}
            </button>
          </div>
        </div>

        {/* Collapsed: mode pills + key metrics */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-secondary)]">
          <span className="text-base">{modeSummary}</span>
          {journey.total_transfers != null && (
            <span>{journey.total_transfers === 0 ? 'Direct' : `${journey.total_transfers} transfer${journey.total_transfers > 1 ? 's' : ''}`}</span>
          )}
          {journey.fare != null && (
            <span className="font-bold text-emerald-500">₹{journey.fare}</span>
          )}
          {journey.departure_time_display && (
            <span>{journey.departure_time_display} → {journey.arrival_time_display || '—'}</span>
          )}
          {journey.is_overnight && (
            <span className="text-orange-500 font-bold text-[10px]">🌙 Overnight</span>
          )}
        </div>
      </div>

      {/* Expanded: full leg-by-leg timeline */}
      {expanded && legs.length > 0 && (
        <div className="border-t border-[var(--border-color)] px-4 py-4 space-y-1">
          {legs.map((leg, i) => (
            <LegRow
              key={i}
              leg={leg}
              connection={connections[i] || null}
            />
          ))}

          {/* Footer */}
          <div className="mt-4 pt-3 border-t border-[var(--border-color)] grid grid-cols-2 gap-2 text-[10px] text-[var(--text-muted)]">
            {journey.total_waiting_time_min != null && (
              <div><span className="font-bold text-[var(--text-secondary)]">Total Wait:</span> {Math.round(journey.total_waiting_time_min)} min</div>
            )}
            {journey.total_walking_distance_m != null && (
              <div><span className="font-bold text-[var(--text-secondary)]">Walking:</span> {(journey.total_walking_distance_m / 1000).toFixed(1)} km</div>
            )}
            {journey.fare != null ? (
              <div><span className="font-bold text-[var(--text-secondary)]">Fare:</span> <span className="text-emerald-500 font-bold">₹{journey.fare}</span></div>
            ) : (
              <div><span className="font-bold text-[var(--text-secondary)]">Fare:</span> Unavailable</div>
            )}
            {journey.distance_km && (
              <div><span className="font-bold text-[var(--text-secondary)]">Distance:</span> {journey.distance_km} km</div>
            )}
          </div>

          {/* Why this route */}
          {journey.why_this_route?.length > 0 && (
            <div className="mt-3 text-[10px] text-[var(--text-muted)] space-y-0.5">
              {journey.why_this_route.map((r, i) => <div key={i}>• {r}</div>)}
            </div>
          )}

          {/* Impossible connection warning */}
          {connections.some(c => c.status === 'RED') && (
            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-500 font-bold">
              ⚠️ One or more connections may be too tight. Verify schedules before booking.
            </div>
          )}
        </div>
      )}

      {expanded && legs.length === 0 && (
        <div className="border-t border-[var(--border-color)] px-4 py-3 text-xs text-[var(--text-muted)]">
          Detailed leg information unavailable from {journey.provider}.
        </div>
      )}
    </div>
  );
}
