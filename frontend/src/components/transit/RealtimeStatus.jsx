import React from 'react';
import { IconShieldCheck, IconAlertTriangle, IconClock, IconRefresh, IconInfoCircle } from '@tabler/icons-react';

/**
 * RealtimeStatus.jsx — WanderWise Canonical Real-Time Status & Freshness Badge Component
 *
 * Truth-First Principles:
 * 1. Categorizes telemetry freshness strictly from provider timestamps:
 *    - 0-60s: 🟢 LIVE
 *    - 60-120s: 🟡 RECENT
 *    - 120-300s: 🟠 AGING
 *    - >300s: 🔴 STALE
 * 2. Distinguishes REALTIME_VERIFIED from SCHEDULE_VERIFIED and PROVIDER_CALCULATED.
 * 3. Never renders fake live claims when telemetry is missing.
 */

export default function RealtimeStatus({ verification, realtime, provider, lastUpdated, ageSeconds, showDetails = false }) {
  const isRealtime = verification === 'REALTIME_VERIFIED' || (realtime && realtime.available && realtime.status !== 'unavailable');
  const isStale = verification === 'STALE_REALTIME' || (realtime && realtime.status === 'stale') || (ageSeconds != null && ageSeconds > 300);
  const isScheduled = verification === 'SCHEDULE_VERIFIED' || ['Provider Verified', 'Schedule Verified', 'VERIFIED'].includes(verification);
  const isCalculated = verification === 'PROVIDER_CALCULATED' || verification === 'Provider Calculated';

  const age = ageSeconds != null ? ageSeconds : (realtime?.age_seconds ?? null);

  let badgeColor = 'bg-gray-500/10 border-gray-500/30 text-[var(--text-muted)]';
  let badgeLabel = 'UNAVAILABLE';
  let badgeIcon = '⚪';

  if (isRealtime && !isStale) {
    if (age != null && age <= 60) {
      badgeColor = 'bg-emerald-500/20 border-emerald-500/40 text-emerald-600 dark:text-emerald-400';
      badgeLabel = '🟢 LIVE';
      badgeIcon = '🟢';
    } else if (age != null && age <= 120) {
      badgeColor = 'bg-amber-500/20 border-amber-500/40 text-amber-600 dark:text-amber-400';
      badgeLabel = '🟡 RECENT';
      badgeIcon = '🟡';
    } else {
      badgeColor = 'bg-orange-500/20 border-orange-500/40 text-orange-600 dark:text-orange-400';
      badgeLabel = '🟠 AGING';
      badgeIcon = '🟠';
    }
  } else if (isStale) {
    badgeColor = 'bg-rose-500/20 border-rose-500/40 text-rose-600 dark:text-rose-400';
    badgeLabel = '🔴 STALE REALTIME';
    badgeIcon = '🔴';
  } else if (isScheduled) {
    badgeColor = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400';
    badgeLabel = '🟢 SCHEDULE VERIFIED';
    badgeIcon = '🟢';
  } else if (isCalculated) {
    badgeColor = 'bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400';
    badgeLabel = '⚠️ PROVIDER CALCULATED';
    badgeIcon = '⚠️';
  }

  const updatedTime = lastUpdated || realtime?.last_updated;
  const updatedStr = updatedTime ? new Date(updatedTime).toLocaleTimeString() : null;

  return (
    <div className="inline-flex flex-col gap-1">
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm ${badgeColor}`}>
        <span className="text-xs">{badgeIcon}</span>
        <span>{badgeLabel}</span>
      </div>

      {showDetails && (
        <div className="text-[10px] text-[var(--text-muted)] space-y-0.5">
          {updatedStr && <div>Updated: {updatedStr} ({age != null ? `${Math.round(age)}s ago` : 'just now'})</div>}
          {provider && <div>Provider: {provider}</div>}
          {realtime?.delay_min != null && realtime.delay_min > 0 && (
            <div className="text-rose-500 font-bold">Delay: +{realtime.delay_min} min</div>
          )}
        </div>
      )}
    </div>
  );
}

export function DataProvenanceCard({ route }) {
  if (!route) return null;

  const sources = route.source || route.sources || {};
  const verif = route.verification_status || route.verification || 'SCHEDULE_VERIFIED';

  return (
    <div className="bg-[var(--bg-glass)] p-4 rounded-2xl border border-[var(--border-color)] space-y-3">
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border-color)] pb-2">
        <IconInfoCircle size={16} className="text-purple-500" /> Data Sources & Provenance
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Schedule</div>
          <div className="font-bold text-[var(--text-primary)]">{sources.schedule || route.provider || 'Unavailable'}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Realtime Telemetry</div>
          <div className="font-bold text-[var(--text-primary)]">{sources.realtime || (route.realtime?.available ? route.provider : 'Unavailable')}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Duration Source</div>
          <div className="font-bold text-[var(--text-primary)]">{sources.duration || route.duration_source || route.provider}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Distance Source</div>
          <div className="font-bold text-[var(--text-primary)]">{sources.distance || route.distance_source || route.provider}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Fare Source</div>
          <div className="font-bold text-emerald-600 dark:text-emerald-400">{sources.fare || route.fare_source || 'Unavailable'}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Verification Level</div>
          <div className="font-bold text-purple-600 dark:text-purple-400">{verif?.level || verif}</div>
        </div>
      </div>
    </div>
  );
}
