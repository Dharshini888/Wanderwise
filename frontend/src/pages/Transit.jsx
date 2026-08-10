import React, { useState, useEffect, useRef } from 'react';
import {
  IconMapPin, IconRoute, IconSparkles, IconClock, IconSearch,
  IconShieldCheck, IconAlertTriangle, IconRefresh, IconCar,
  IconWalk, IconChevronDown, IconCheck, IconX, IconArrowRight, IconInfoCircle, IconPlane
} from '@tabler/icons-react';

import {
  OverviewTab,
  RouteOptionsTab,
  AIAnalysisTab,
  TimelineTab,
  WeatherSafetyTab,
  BudgetAnalyticsTab,
  NearbyTab,
  AIRouteGuidanceCard
} from '../components/transit/TransitComponentsV6';

const API = 'http://localhost:8000/api';
const STRATEGIES = ['fastest', 'cheapest', 'safest', 'greenest', 'least walking', 'most comfortable', 'best overall'];

export default function Transit() {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    origin_lat: null,
    origin_lon: null,
    gps_accuracy: null,
    preferred_mode: 'fastest',
  });

  const [locationStatus, setLocationStatus] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const activeRequestId = useRef(null);

  useEffect(() => {
    handleGetLocation();
  }, []);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation unavailable');
      return;
    }
    setLocationStatus('Locating…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const acc = Math.round(pos.coords.accuracy);
        setForm(prev => ({
          ...prev,
          origin: 'Current Location',
          origin_lat: pos.coords.latitude,
          origin_lon: pos.coords.longitude,
          gps_accuracy: acc,
        }));
        setLocationStatus(`📍 Using current location (Accuracy: ${acc} m)`);
      },
      (err) => {
        setLocationStatus('Location permission denied. Enter origin manually.');
        setForm(prev => ({ ...prev, origin: '', origin_lat: null, origin_lon: null, gps_accuracy: null }));
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!form.origin || !form.destination) return;

    const requestId = (typeof crypto !== 'undefined' && crypto.randomUUID)
      ? crypto.randomUUID()
      : `req_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;

    activeRequestId.current = requestId;
    setLoading(true);
    setError('');
    setResult(null); // Clear previous state immediately

    try {
      const res = await fetch(`${API}/transit/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: form.origin,
          destination: form.destination,
          origin_lat: form.origin_lat,
          origin_lon: form.origin_lon,
          gps_accuracy: form.gps_accuracy,
          preferred_mode: form.preferred_mode,
          date: 'Tomorrow',
          request_id: requestId,
        }),
      });

      if (!res.ok) throw new Error(`Server HTTP ${res.status}`);

      const data = await res.json();

      // Discard response if request_id does not match activeRequestId
      if (data.request_id && data.request_id !== activeRequestId.current) {
        console.warn(`[Transit] Stale response discarded (${data.request_id} != ${activeRequestId.current})`);
        return;
      }

      setResult(data);
      setActiveTab('overview');
    } catch (err) {
      setError('Unable to reach the WanderWise backend server.');
    } finally {
      setLoading(false);
    }
  };

  // ── Render SAME_LOCATION View ─────────────────────────────────────────
  const SameLocationView = ({ result }) => (
    <div className="glass-card p-6 rounded-3xl border border-indigo-500/40 bg-[var(--bg-card)] shadow-xl space-y-4">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-indigo-500/20 rounded-2xl text-indigo-500 dark:text-indigo-400">
          <IconMapPin size={32} />
        </div>
        <div>
          <span className="text-[10px] font-bold uppercase text-indigo-500 dark:text-indigo-400 tracking-widest block mb-0.5">
            📍 Same Location Detected
          </span>
          <h3 className="text-xl font-black text-[var(--text-primary)]">Already at Destination</h3>
        </div>
      </div>
      <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-glass)] p-4 rounded-xl border border-[var(--border-color)]">
        {result.message || 'Origin and destination coordinates are within 500 meters of each other. No long-distance transit or road navigation is required.'}
      </p>
    </div>
  );

  // ── Render Level 4: ALTERNATIVE_PROVIDER_UNAVAILABLE View ─────────────
  const AlternativeProviderUnavailableView = ({ result }) => {
    const failures = result?.provider_failures || [];

    return (
      <div className="glass-card p-6 rounded-3xl border border-amber-500/40 bg-[var(--bg-card)] shadow-xl space-y-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-amber-500/20 rounded-2xl text-amber-500 dark:text-amber-400 flex-shrink-0">
            <IconPlane size={32} />
          </div>
          <div className="flex-1">
            <div className="text-xs font-bold uppercase text-amber-500 dark:text-amber-400 mb-1 tracking-widest">
              Public Transit Unavailable · {result?.journey_scale || 'INTERCONTINENTAL'} Journey
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)] mb-2">
              {result?.origin} <span className="text-amber-500 dark:text-amber-400">→</span> {result?.destination}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] mb-4 leading-relaxed">
              Public transit could not be verified for this intercontinental journey. No verified flight provider is currently configured, so WanderWise will not display an impractical road driving route.
            </p>

            {/* Provider Failure Diagnostics */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs mb-4">
              {failures.map((f, idx) => (
                <div key={idx} className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <div className="font-bold text-[var(--text-primary)] mb-0.5">{f.provider}</div>
                  <div className="text-[10px] font-mono text-amber-500 dark:text-amber-400 uppercase">{f.status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ── Render Level 2: VERIFIED_ALTERNATIVE_AVAILABLE View ────────────────
  const VerifiedAlternativeView = ({ result }) => {
    const roadAlt = result?.road_alternative;

    return (
      <div className="glass-card p-6 rounded-3xl border border-indigo-500/30 bg-[var(--bg-card)] shadow-xl space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <span className="text-[10px] uppercase font-bold text-indigo-500 dark:text-indigo-400 tracking-wider block mb-1">
              🟢 Verified Alternative Option
            </span>
            <h3 className="text-lg font-black text-[var(--text-primary)] flex items-center gap-2">
              <IconCar className="text-indigo-500 dark:text-indigo-400" size={24} />
              Road Alternative — OSRM Driving
            </h3>
          </div>
          <span className="text-xs font-bold bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 px-3 py-1 rounded-xl">
            OSRM Driving
          </span>
        </div>

        {roadAlt && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Driving Distance</div>
              <div className="text-lg font-extrabold text-[var(--text-primary)] mt-0.5">{roadAlt.distance_km} km</div>
            </div>
            <div className="bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Est. Driving Time</div>
              <div className="text-lg font-extrabold text-[var(--text-primary)] mt-0.5">{roadAlt.duration_display}</div>
            </div>
            <div className="bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Route Type</div>
              <div className="text-lg font-extrabold text-indigo-600 dark:text-indigo-300 mt-0.5">Road Driving</div>
            </div>
            <div className="bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)]">
              <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold">Provider</div>
              <div className="text-lg font-extrabold text-emerald-600 dark:text-emerald-400 mt-0.5">OSRM Engine</div>
            </div>
          </div>
        )}

        <button
          onClick={() => window.open(
            `https://www.google.com/maps/dir/${result?.origin_coords?.lat},${result?.origin_coords?.lon}/${result?.dest_coords?.lat},${result?.dest_coords?.lon}`,
            '_blank'
          )}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg mt-2 cursor-pointer"
        >
          <IconCar size={16} /> Open Driving Navigation
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] space-y-8 animate-fadeIn">

      {/* Header */}
      <div className="glass-card p-6 rounded-3xl border border-purple-500/30 bg-[var(--bg-card)] shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-purple-100 dark:bg-purple-900/60 border border-purple-300 dark:border-purple-500/40 text-purple-700 dark:text-purple-300 text-[10px] font-bold px-3 py-1 rounded-full uppercase flex items-center gap-1">
              <IconSparkles size={12} className="text-amber-500 animate-pulse" /> Multimodal Navigation Platform
            </span>
            <span className="text-xs text-[var(--text-muted)] font-medium">V12.2</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-[var(--text-primary)] font-heading tracking-tight">
            Smart Transit Assistant
          </h1>
          <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-1">
            Truth-First Multimodal Router — Transitous · Navitia · RailRadar · OSRM · AI Route Guidance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold uppercase">Truth-First Mandate</div>
            <div className="text-xs text-[var(--text-muted)]">Truth &gt; Completeness · Zero AI Transit Facts</div>
          </div>
          <div className="p-3 bg-purple-100 dark:bg-purple-900/50 border border-purple-300 dark:border-purple-500/30 rounded-2xl text-purple-600 dark:text-purple-300">
            <IconShieldCheck size={28} />
          </div>
        </div>
      </div>

      {/* Search Form */}
      <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] space-y-4">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 items-end">

          {/* Origin */}
          <div className="lg:col-span-2">
            <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5 flex justify-between items-center">
              <span>Origin</span>
              {locationStatus && (
                <span className="text-[9px] text-purple-500 dark:text-purple-400 font-normal truncate max-w-[200px]">{locationStatus}</span>
              )}
            </label>
            <div className="relative">
              <IconMapPin
                className="absolute left-3 top-3 text-purple-500 dark:text-purple-400 cursor-pointer hover:opacity-80 transition-colors"
                size={18}
                onClick={handleGetLocation}
                title="Use my location"
              />
              <input
                type="text"
                placeholder="Origin city or tap 📍"
                className="w-full bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[var(--text-primary)] outline-none focus:border-purple-500 transition-colors"
                value={form.origin}
                onChange={(e) => {
                  setForm({ ...form, origin: e.target.value, origin_lat: null, origin_lon: null, gps_accuracy: null });
                  setLocationStatus('');
                }}
                required
              />
            </div>
          </div>

          {/* Destination */}
          <div className="lg:col-span-2">
            <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-1.5">
              Destination
            </label>
            <div className="relative">
              <IconMapPin className="absolute left-3 top-3 text-purple-500 dark:text-purple-400" size={18} />
              <input
                type="text"
                placeholder="e.g. Manchester, London, Paris, Chennai, Tokyo"
                className="w-full bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[var(--text-primary)] outline-none focus:border-purple-500 transition-colors"
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
                required
              />
            </div>
          </div>

          {/* Strategy */}
          <div>
            <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-1.5">
              Strategy
            </label>
            <select
              className="w-full bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl px-3 py-2.5 text-xs text-[var(--text-primary)] outline-none focus:border-purple-500 capitalize cursor-pointer"
              value={form.preferred_mode}
              onChange={(e) => setForm({ ...form, preferred_mode: e.target.value })}
            >
              {STRATEGIES.map((s) => (
                <option key={s} value={s} className="bg-[var(--bg-card)] text-[var(--text-primary)]">
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Search Button */}
          <div>
            <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-1.5 opacity-0">
              Go
            </label>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-2.5 rounded-xl text-xs shadow-lg transition-all flex items-center justify-center gap-2 h-10 border border-purple-400/30 cursor-pointer"
            >
              {loading ? <span>Routing…</span> : <><IconSearch size={16} /> Plan Journey</>}
            </button>
          </div>

        </form>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
            <IconAlertTriangle size={16} /> {error}
          </div>
        )}
      </div>

      {/* V12 Result Hierarchy Views */}
      {result && !loading && (
        <div className="space-y-6">

          {/* Level 0: SAME_LOCATION */}
          {result.status === 'SAME_LOCATION' ? (
            <SameLocationView result={result} />
          ) : result.status === 'ALTERNATIVE_PROVIDER_UNAVAILABLE' ? (
            /* Level 4: ALTERNATIVE_PROVIDER_UNAVAILABLE */
            <AlternativeProviderUnavailableView result={result} />
          ) : result.status === 'ROUTE_GUIDANCE_AVAILABLE' ? (
            /* Level 3: ROUTE_GUIDANCE_AVAILABLE */
            <AIRouteGuidanceCard routeGuidance={result.route_guidance} />
          ) : result.status === 'VERIFIED_ALTERNATIVE_AVAILABLE' ? (
            /* Level 2: VERIFIED_ALTERNATIVE_AVAILABLE */
            <VerifiedAlternativeView result={result} />
          ) : (
            /* Level 1: PUBLIC_TRANSIT_AVAILABLE */
            <>
              <div className="flex border-b border-[var(--border-color)] overflow-x-auto gap-2 scrollbar-none pb-2">
                {[
                  { id: 'overview',  label: '🗺️ Overview & Quality' },
                  { id: 'timeline',  label: '📍 Journey Timeline' },
                  { id: 'options',   label: '🔀 Route Options' },
                  { id: 'ai',        label: '🤖 Strategy Analysis' },
                  { id: 'weather',   label: '🌤️ Weather' },
                  { id: 'budget',    label: '💰 Budget' },
                  { id: 'nearby',    label: '🏥 Nearby' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-2.5 font-bold text-xs rounded-xl whitespace-nowrap transition-all cursor-pointer ${
                      activeTab === tab.id
                        ? 'bg-purple-600 text-white shadow-lg border border-purple-400/40'
                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-glass)]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="animate-fadeIn">
                {activeTab === 'overview'  && <OverviewTab      routeData={result} />}
                {activeTab === 'timeline'  && <TimelineTab      routeData={result} />}
                {activeTab === 'options'   && <RouteOptionsTab  routeData={result} />}
                {activeTab === 'ai'        && <AIAnalysisTab    routeData={result} />}
                {activeTab === 'weather'   && <WeatherSafetyTab routeData={result} />}
                {activeTab === 'budget'    && <BudgetAnalyticsTab routeData={result} />}
                {activeTab === 'nearby'    && <NearbyTab        routeData={result} />}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
