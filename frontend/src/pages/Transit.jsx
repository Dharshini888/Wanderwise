import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import {
  IconMapPin, IconRoute, IconSparkles, IconClock, IconSearch,
  IconShieldCheck, IconAlertTriangle, IconRefresh, IconCar,
  IconWalk, IconChevronDown, IconCheck, IconX, IconArrowRight, IconInfoCircle, IconPlane, IconTrain
} from '@tabler/icons-react';

import TransitMap from '../components/transit/TransitMap';
import JourneyCard from '../components/transit/JourneyCard';
import {
  OverviewTab,
  RoutesTab,
  StrategyTab,
  TimelineTab,
  WeatherSafetyTab,
  BudgetAnalyticsTab,
  NearbyTab,
  AIRouteGuidanceCard
} from '../components/transit/TransitComponentsV6';

const API = 'http://localhost:8000/api';
const STRATEGIES = ['fastest', 'cheapest', 'safest', 'greenest', 'least walking', 'fewest transfers', 'best overall'];

export default function Transit() {
  const { tripId } = useParams();
  const location = useLocation();

  const [form, setForm] = useState({
    origin: '',
    destination: '',
    origin_source: null,
    origin_lat: null,
    origin_lon: null,
    gps_accuracy: null,
    preferred_mode: 'fastest',
  });

  const [locationStatus, setLocationStatus] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [result, setResult] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const activeRequestId = useRef(null);

  useEffect(() => {
    handleGetLocation();
    if (tripId) {
      loadTripContext(tripId);
    }
  }, [tripId]);

  const loadTripContext = async (id) => {
    try {
      const res = await fetch(`${API}/trips/${id}`);
      if (res.ok) {
        const tripData = await res.json();
        const dest = tripData.destination || 'Meghalaya';
        const day1Acts = tripData.itinerary_days?.[0]?.activities || [];
        const firstSpot = day1Acts[0]?.place?.name || day1Acts[0]?.title || tripData.origin_city || 'Coimbatore';
        const lastSpot = day1Acts[day1Acts.length - 1]?.place?.name || day1Acts[day1Acts.length - 1]?.title || dest;

        const startQuery = `${firstSpot}, ${dest}`;
        const endQuery = `${lastSpot}, ${dest}`;

        setForm(prev => ({
          ...prev,
          origin: startQuery,
          destination: endQuery
        }));

        triggerSearch(startQuery, endQuery);
      }
    } catch (e) {
      console.error('Error fetching trip context for transit:', e);
    }
  };

  const triggerSearch = async (orig, dest) => {
    if (!orig || !dest) return;
    const requestId = `req_${Date.now()}`;
    activeRequestId.current = requestId;
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API}/transit/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: orig,
          destination: dest,
          preferred_mode: 'fastest',
          date: 'Tomorrow',
          request_id: requestId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
        if (data.recommended_route) {
          setSelectedRouteId(data.recommended_route.route_id);
        }
      }
    } catch (err) {
      setError('Unable to reach the WanderWise backend server.');
    } finally {
      setLoading(false);
    }
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation unavailable');
      return;
    }
    setLocationStatus('Locating…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const acc = Math.round(pos.coords.accuracy);
        console.log('[GPS TRACE 1]', {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: acc,
          timestamp: pos.timestamp
        });
        setForm(prev => {
          const updated = {
            ...prev,
            origin: 'Current GPS Location',
            origin_source: 'BROWSER_GPS',
            origin_lat: pos.coords.latitude,
            origin_lon: pos.coords.longitude,
            gps_accuracy: acc,
            origin_accuracy_m: acc,
          };
          console.log('[GPS TRACE 2 FORM STATE AFTER GPS]', updated);
          return updated;
        });
        setLocationStatus(`📍 Using current location (Accuracy: ${acc} m)`);
      },
      (err) => {
        setLocationStatus('Location permission denied. Enter origin manually.');
        setForm(prev => ({
          ...prev,
          origin: '',
          origin_source: null,
          origin_lat: null,
          origin_lon: null,
          gps_accuracy: null,
          origin_accuracy_m: null,
        }));
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

    const payload = {
      origin: form.origin,
      destination: form.destination,
      origin_source: form.origin_source || (form.origin_lat != null && form.origin_lon != null ? 'BROWSER_GPS' : 'GEOCODED_LOCATION'),
      origin_lat: form.origin_lat,
      origin_lon: form.origin_lon,
      gps_accuracy: form.gps_accuracy,
      origin_accuracy_m: form.gps_accuracy,
      preferred_mode: form.preferred_mode,
      date: 'Tomorrow',
      request_id: requestId,
    };
    console.log('[GPS TRACE 4 API REQUEST PAYLOAD]', payload);
    console.log('[GPS TRACE 4B API REQUEST COORDINATE TYPES]', {
      origin_lat_type: typeof payload.origin_lat,
      origin_lon_type: typeof payload.origin_lon,
      accuracy_type: typeof payload.origin_accuracy_m
    });

    try {
      const res = await fetch(`${API}/transit/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Server HTTP ${res.status}`);

      const data = await res.json();


      console.log('[GPS TRACE 12 FRONTEND RESPONSE]', {
        origin: data.origin,
        origin_source: data.origin_source,
        origin_coords: data.origin_coords,
        nearby_count: data.nearby?.length,
        nearby: data.nearby
      });
      console.log('[GPS TRACE 18 API RESPONSE RECEIVED]', data);

      // Discard response if request_id does not match activeRequestId
      if (data.request_id && data.request_id !== activeRequestId.current) {
        console.warn(`[Transit] Stale response discarded (${data.request_id} != ${activeRequestId.current})`);
        return;
      }

      setResult(data);
      if (data.recommended_route) {
        setSelectedRouteId(data.recommended_route.route_id);
      }
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
            Truth-First Multimodal Router — Transitous · RailRadar · OSRM · AI Route Guidance
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
                  const val = e.target.value;
                  setForm(prev => {
                    const updated = {
                      ...prev,
                      origin: val,
                      origin_source: val ? 'GEOCODED_LOCATION' : null,
                      origin_lat: null,
                      origin_lon: null,
                      gps_accuracy: null,
                      origin_accuracy_m: null,
                    };
                    console.log('[GPS TRACE 3 ORIGIN INPUT CHANGE]', updated);
                    return updated;
                  });
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
            /* Main Route Overview (Google Maps Style) */
            (() => {
              const activeRoute = result.route_options?.find(r => r.route_id === selectedRouteId) || result.recommended_route;
              return (
                <div className="space-y-6">
                  {/* Interactive Map */}
                  <TransitMap 
                    routeOptions={result.route_options}
                    selectedRouteId={selectedRouteId}
                    onRouteSelect={setSelectedRouteId}
                    originCoords={result.origin_coords}
                    destCoords={result.dest_coords}
                  />
                  
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Route Options (Left Panel) */}
                    <div className="lg:col-span-1 space-y-4">
                      <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">Journey Options</h3>
                      
                      {/* Journeys list (new) with fallback to route cards (legacy) */}
                      {result.journeys && result.journeys.length > 0 ? (
                        <div className="space-y-3">
                          {result.journeys.map((journey, idx) => (
                            <JourneyCard
                              key={journey.journey_id || idx}
                              journey={journey}
                              isSelected={(journey.route_id || journey.journey_id) === selectedRouteId}
                              isBestOverall={(journey.route_id || journey.journey_id) === result.best_overall_route?.route_id}
                              isFastest={(journey.route_id || journey.journey_id) === result.fastest_route?.route_id}
                              isCheapest={(journey.route_id || journey.journey_id) === result.cheapest_route?.route_id}
                              isSafest={(journey.route_id || journey.journey_id) === result.safest_route?.route_id}
                              isGreenest={(journey.route_id || journey.journey_id) === result.greenest_route?.route_id}
                              isFewestTransfers={(journey.route_id || journey.journey_id) === result.fewest_transfers_route?.route_id}
                              onSelect={setSelectedRouteId}
                            />
                          ))}
                        </div>
                      ) : result.route_options && result.route_options.length > 0 ? (
                        result.route_options.map((opt, idx) => {
                          const isRecommended = opt.route_id === result.recommended_route?.route_id;
                          const hasGeo = opt.geometry && opt.geometry.length > 0;
                          
                          // Determine mode string and icon
                          let modeStr = '🚆 Transit';
                          let modeIcon = <IconTrain size={16} />;
                          if (opt.provider === 'FlightProvider') { modeStr = '✈️ Flight'; modeIcon = <IconPlane size={16} />; }
                          else if (opt.provider === 'OSRM') { modeStr = '🚗 Driving'; modeIcon = <IconCar size={16} />; }

                          // Calculate hours/mins
                          const hrs = Math.floor(opt.duration_min / 60);
                          const mins = Math.floor(opt.duration_min % 60);
                          const durStr = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;

                          return (
                            <div 
                              key={idx}
                              onClick={() => setSelectedRouteId(opt.route_id)}
                              className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                                opt.route_id === activeRoute?.route_id 
                                  ? 'bg-purple-500/10 border-purple-500/50 ring-1 ring-purple-500/20 shadow-md' 
                                  : 'bg-[var(--bg-glass)] border-[var(--border-color)] hover:border-purple-500/30 hover:bg-[var(--bg-glass-hover)] shadow-sm'
                              }`}
                            >
                              {isRecommended && (
                                <div className="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                                  <IconSparkles size={12} /> ⭐ BEST OVERALL
                                </div>
                              )}
                              
                              <div className="flex justify-between items-start mb-3">
                                <div>
                                  <div className="font-bold text-[var(--text-primary)] text-sm flex items-center gap-1">
                                    {modeIcon} {opt.train_number ? `${opt.train_number} - ${opt.train_name}` : opt.provider}
                                  </div>
                                  <div className="text-[10px] text-[var(--text-muted)] uppercase">
                                    {opt.train_number ? opt.provider : modeStr}
                                  </div>
                                  {opt.departure_station && opt.arrival_station && (
                                    <div className="text-[10px] text-[var(--text-secondary)] mt-1 font-medium truncate max-w-[200px]">
                                      {opt.departure_station} → {opt.arrival_station}
                                    </div>
                                  )}
                                </div>
                                <div className="text-right">
                                  <div className="font-black text-lg text-purple-600 dark:text-purple-400 leading-none">{durStr}</div>
                                  <div className="text-xs text-[var(--text-secondary)] font-medium mt-1">{opt.distance_km} km</div>
                                </div>
                              </div>
                              
                              <div className="grid grid-cols-2 gap-2 text-xs mb-3 bg-[var(--bg-card)] p-2 rounded-xl border border-[var(--border-color)]">
                                <div>
                                  <span className="text-[10px] text-[var(--text-muted)] block">Departure</span>
                                  <span className="font-bold">{opt.departure_time_display || 'Unavailable'}</span>
                                </div>
                                <div>
                                  <span className="text-[10px] text-[var(--text-muted)] block">Arrival</span>
                                  <span className="font-bold">{opt.arrival_time_display || 'Unavailable'}</span>
                                </div>
                                <div>
                                  <span className="text-[10px] text-[var(--text-muted)] block">Transfers</span>
                                  <span className="font-bold">{opt.transfers !== null ? opt.transfers : '—'}</span>
                                </div>
                                <div>
                                  <span className="text-[10px] text-[var(--text-muted)] block">Fare</span>
                                  <span className="font-bold text-emerald-600 dark:text-emerald-400">{opt.fare ? `₹${opt.fare}` : 'Unavailable'}</span>
                                </div>
                                <div className="col-span-2">
                                  <span className="text-[10px] text-[var(--text-muted)] block">Walking Distance</span>
                                  <span className="font-bold">{opt.walking_distance_m ? `${(opt.walking_distance_m/1000).toFixed(1)} km` : '—'}</span>
                                </div>
                              </div>

                              <div className="space-y-1">
                                <div className="flex items-center gap-1 text-[10px]">
                                  {['Provider Verified', 'Schedule Verified', 'Transit Data Verified', 'VERIFIED'].includes(opt.verification_status) 
                                    ? <span className="text-emerald-500 font-bold">🟢 {opt.verification_status === 'VERIFIED' ? 'Verified itinerary' : opt.verification_status}</span> 
                                    : <span className="text-amber-500 font-bold">⚠️ {opt.verification_status || 'Estimated'}</span>}
                                </div>
                                <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                                  <span>🗺️ {hasGeo ? 'Exact geometry available' : 'Schematic geometry only'}</span>
                                </div>
                                <div className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                                  <span>⏱️ Source: {opt.duration_source || 'Unavailable'}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="text-xs text-[var(--text-muted)] p-4 text-center bg-[var(--bg-glass)] rounded-2xl border border-[var(--border-color)]">
                          No alternate routes available.
                        </div>
                      )}
                    </div>

                    <div className="lg:col-span-2 space-y-6">
                      <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] space-y-6">
                        {/* Journey Summary */}
                        {activeRoute && (
                          <div className="space-y-4">
                            <div className="flex justify-between items-start border-b border-[var(--border-color)] pb-4">
                              <div>
                                <h2 className="text-xl font-black text-[var(--text-primary)]">
                                  {result.origin} <span className="text-purple-500">→</span> {result.destination}
                                </h2>
                                <p className="text-sm font-bold text-[var(--text-muted)] mt-1 flex items-center gap-1">
                                  {activeRoute.provider === 'FlightProvider' ? '✈️' : activeRoute.provider === 'OSRM' ? '🚗' : '🚆'} {activeRoute.mode} · {activeRoute.provider}
                                </p>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-black text-purple-600 dark:text-purple-400">
                                  {Math.floor(activeRoute.duration_min / 60) > 0 ? `${Math.floor(activeRoute.duration_min / 60)}h ` : ''}
                                  {Math.floor(activeRoute.duration_min % 60)}m
                                </div>
                                <div className="text-sm text-[var(--text-muted)] font-bold">{activeRoute.distance_km} km</div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Departure</span> <span className="font-bold">{activeRoute.departure_time_display || 'Unavailable'}</span></div>
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Arrival</span> <span className="font-bold">{activeRoute.arrival_time_display || 'Unavailable'}</span></div>
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Transfers</span> <span className="font-bold">{activeRoute.transfers !== null ? activeRoute.transfers : '—'}</span></div>
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Fare</span> <span className="font-bold text-emerald-600">{activeRoute.fare ? `₹${activeRoute.fare}` : 'Unavailable'}</span></div>
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Distance Source</span> <span className="font-bold">{activeRoute.distance_source || 'Unavailable'}</span></div>
                              <div><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Duration Source</span> <span className="font-bold">{activeRoute.duration_source || 'Unavailable'}</span></div>
                              <div className="col-span-2"><span className="text-[10px] text-[var(--text-muted)] block uppercase font-bold">Verification</span> <span className={`font-bold ${ ['Provider Verified','Schedule Verified','VERIFIED'].includes(activeRoute.verification_status) ? 'text-emerald-500' : 'text-amber-500' }`}>{['Provider Verified','Schedule Verified','VERIFIED'].includes(activeRoute.verification_status) ? '🟢' : '⚠️'} {activeRoute.verification_status || 'Estimated'}</span></div>
                            </div>
                          </div>
                        )}
                        
                        {/* Tab Navigation */}
                        <div className="flex overflow-x-auto hide-scrollbar gap-2 border-b border-[var(--border-color)] pb-4">
                          {['overview', 'timeline', 'routes', 'strategy', 'weather', 'budget', 'nearby'].map((tab) => (
                            <button
                              key={tab}
                              onClick={() => setActiveTab(tab)}
                              className={`px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider whitespace-nowrap transition-all ${
                                activeTab === tab
                                  ? 'bg-purple-600 text-white shadow-md'
                                  : 'bg-[var(--bg-glass)] text-[var(--text-secondary)] hover:bg-[var(--bg-glass-hover)] border border-[var(--border-color)]'
                              }`}
                            >
                              {tab}
                            </button>
                          ))}
                        </div>
                        
                        {/* Tab Content */}
                        <div className="pt-2">
                          {activeTab === 'overview' && <OverviewTab routeData={result} activeRoute={activeRoute} />}
                          {activeTab === 'timeline' && <TimelineTab activeRoute={activeRoute} />}
                          {activeTab === 'routes' && <RoutesTab routeOptions={result.route_options} selectedRouteId={selectedRouteId} onSelect={setSelectedRouteId} />}
                          {activeTab === 'strategy' && <StrategyTab routeData={result} />}
                          {activeTab === 'weather' && <WeatherSafetyTab weatherObj={result.weather_obj} origin={result.origin} dest={result.destination} />}
                          {activeTab === 'budget' && <BudgetAnalyticsTab activeRoute={activeRoute} />}
                          {activeTab === 'nearby' && <NearbyTab nearby={result.nearby} provenance={result.nearby_provenance} />}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>
      )}
    </div>
  );
}
