import React, { useState, useEffect } from 'react';
import VerificationBadge from '../ui/VerificationBadge';
import GuideMap from './GuideMap';
import { getPlaceRoute } from '../../api/local_guide';
import api from '../../api/axios';
import { useAuth } from '../../context/AuthContext';
import {
  IconX,
  IconMapPin,
  IconClock,
  IconPhone,
  IconGlobe,
  IconRoute,
  IconPlus,
  IconHeart,
  IconHeartFilled,
  IconWalk,
  IconCar,
  IconCheck,
  IconAlertCircle,
} from '@tabler/icons-react';

export default function PlaceDetailsModal({
  place,
  originLat,
  originLon,
  onClose,
  onSaveWishlist,
  isSaved = false,
}) {
  const { user } = useAuth();
  const [routeInfo, setRouteInfo] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [travelMode, setTravelMode] = useState('walking');

  // Itinerary Integration State
  const [showItineraryModal, setShowItineraryModal] = useState(false);
  const [userTrips, setUserTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState('');
  const [selectedDay, setSelectedDay] = useState(1);
  const [addingItinerary, setAddingItinerary] = useState(false);
  const [itineraryAdded, setItineraryAdded] = useState(false);

  // Wishlist State
  const [saved, setSaved] = useState(isSaved);
  const [savingWishlist, setSavingWishlist] = useState(false);

  useEffect(() => {
    if (showItineraryModal && user?.id) {
      api
        .get(`/api/trips/user/${user.id}`)
        .then((res) => {
          const trips = res.data?.trips || res.data || [];
          setUserTrips(trips);
          if (trips.length > 0) {
            setSelectedTripId(trips[0].id);
          }
        })
        .catch((err) => console.error('[PlaceDetailsModal] Error loading user trips:', err));
    }
  }, [showItineraryModal, user]);

  if (!place) return null;

  const handleCalculateRoute = async (mode = travelMode) => {
    setTravelMode(mode);
    setLoadingRoute(true);
    try {
      const oLat = originLat || 13.0827;
      const oLon = originLon || 80.2707;
      const pLat = place.latitude || 13.0827;
      const pLon = place.longitude || 80.2707;

      const res = await getPlaceRoute({
        originLat: oLat,
        originLon: oLon,
        destLat: pLat,
        destLon: pLon,
        mode,
      });
      setRouteInfo(res);
    } catch (err) {
      console.error('[PlaceDetailsModal] Route error:', err);
    } finally {
      setLoadingRoute(false);
    }
  };

  const handleSaveWishlist = async () => {
    if (saved) return;
    setSavingWishlist(true);
    try {
      if (onSaveWishlist) {
        await onSaveWishlist(place);
      } else if (user?.id) {
        await api.post('/api/wishlist/add', {
          user_id: user.id,
          destination: place.name,
          country: place.address || 'Local Destination',
          notes: `Added from Local Travel Guide (${place.category})`,
          estimated_budget: 5000,
          priority: 'someday',
        });
      }
      setSaved(true);
    } catch (err) {
      console.error('[PlaceDetailsModal] Save wishlist error:', err);
    } finally {
      setSavingWishlist(false);
    }
  };

  const handleAddToItinerarySubmit = async () => {
    if (!selectedTripId) return;
    setAddingItinerary(true);
    try {
      await api.post(`/api/trips/${selectedTripId}/activities`, {
        day: Number(selectedDay),
        time: '10:00 AM',
        activity: `Visit ${place.name}`,
        location: place.address || place.name,
        notes: `Category: ${place.category}`,
      });
      setItineraryAdded(true);
      setTimeout(() => {
        setShowItineraryModal(false);
        setItineraryAdded(false);
      }, 1500);
    } catch (err) {
      console.error('[PlaceDetailsModal] Add itinerary error:', err);
    } finally {
      setAddingItinerary(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs overflow-y-auto">
      <div className="relative w-full max-w-2xl rounded-3xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-2xl overflow-hidden my-8">
        {/* HEADER */}
        <div className="p-6 pb-4 border-b border-[var(--border-color)] flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                {place.category}
              </span>
              <VerificationBadge status={place.verification_status || 'Provider Verified'} size="xs" />
            </div>
            <h2 className="text-xl font-extrabold text-[var(--text-primary)] font-heading tracking-tight">
              {place.name}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] transition-colors cursor-pointer"
          >
            <IconX size={20} />
          </button>
        </div>

        {/* BODY */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto custom-scrollbar">
          {/* MAP */}
          <div className="w-full">
            <GuideMap
              centerLat={place.latitude}
              centerLon={place.longitude}
              places={[place]}
              activePlace={place}
              routeData={routeInfo}
              height="240px"
            />
          </div>

          {/* ROUTE INFO BANNER IF CALCULATED */}
          {routeInfo && (
            <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-400">
                  <IconRoute size={16} />
                  <span>Route to {place.name} ({travelMode})</span>
                </div>
                <div className="text-sm font-extrabold text-[var(--text-primary)]">
                  {routeInfo.distance_km} km · {routeInfo.duration_minutes} min
                </div>
              </div>
              <VerificationBadge status="Route Calculated" size="sm" />
            </div>
          )}

          {/* METADATA GRID */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Address</span>
              <div className="font-semibold text-[var(--text-primary)] flex items-start gap-1.5">
                <IconMapPin size={15} className="text-blue-500 shrink-0 mt-0.5" />
                <span>{place.address || 'Provider supplied address'}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Coordinates</span>
              <div className="font-semibold text-[var(--text-primary)] font-mono text-[11px]">
                {place.latitude?.toFixed(4)}, {place.longitude?.toFixed(4)}
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Opening Hours</span>
              <div className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                <IconClock size={15} className="text-blue-500 shrink-0" />
                <span>{place.opening_hours || 'Unavailable'}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Contact</span>
              <div className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                <IconPhone size={15} className="text-blue-500 shrink-0" />
                <span>{place.phone || 'Unavailable'}</span>
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Website</span>
              <div className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5 truncate">
                <IconGlobe size={15} className="text-blue-500 shrink-0" />
                {place.website ? (
                  <a
                    href={place.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline truncate"
                  >
                    {place.website}
                  </a>
                ) : (
                  <span>Unavailable</span>
                )}
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Provider</span>
              <div className="font-semibold text-[var(--text-primary)]">
                {place.provider || 'OpenStreetMap'}
              </div>
            </div>
          </div>
        </div>

        {/* ACTIONS FOOTER */}
        <div className="p-6 pt-4 border-t border-[var(--border-color)] flex items-center justify-between gap-3 flex-wrap bg-[var(--bg-subtle)]/50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleCalculateRoute('walking')}
              disabled={loadingRoute}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              <IconWalk size={16} />
              <span>{loadingRoute && travelMode === 'walking' ? 'Calculating...' : 'Directions (Walk)'}</span>
            </button>

            <button
              onClick={() => handleCalculateRoute('driving')}
              disabled={loadingRoute}
              className="px-4 py-2.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] hover:bg-[var(--bg-panel)] text-[var(--text-primary)] text-xs font-bold flex items-center gap-1.5 cursor-pointer"
            >
              <IconCar size={16} />
              <span>Drive</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowItineraryModal(true)}
              className="px-4 py-2.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] hover:bg-[var(--bg-panel)] text-[var(--text-primary)] text-xs font-bold flex items-center gap-1.5 cursor-pointer"
            >
              <IconPlus size={16} className="text-blue-500" />
              <span>Add to Itinerary</span>
            </button>

            <button
              onClick={handleSaveWishlist}
              disabled={savingWishlist}
              className={`px-4 py-2.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                saved
                  ? 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                  : 'bg-[var(--bg-card)] text-[var(--text-primary)] border-[var(--border-color)] hover:border-rose-500/30'
              }`}
            >
              {saved ? <IconHeartFilled size={16} /> : <IconHeart size={16} />}
              <span>{saved ? 'Saved' : 'Wishlist'}</span>
            </button>
          </div>
        </div>

        {/* NESTED ITINERARY MODAL */}
        {showItineraryModal && (
          <div className="absolute inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-6">
            <div className="w-full max-w-md p-6 rounded-3xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
                  Add {place.name} to Trip
                </h3>
                <button
                  onClick={() => setShowItineraryModal(false)}
                  className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  <IconX size={16} />
                </button>
              </div>

              {itineraryAdded ? (
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold flex items-center gap-2">
                  <IconCheck size={18} />
                  <span>Added to trip itinerary successfully!</span>
                </div>
              ) : (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block font-bold text-[var(--text-secondary)] mb-1">Select Trip</label>
                    <select
                      value={selectedTripId}
                      onChange={(e) => setSelectedTripId(e.target.value)}
                      className="w-full p-2.5 rounded-xl bg-[var(--bg-subtle)] border border-[var(--border-color)] font-medium text-[var(--text-primary)] focus:outline-none"
                    >
                      {userTrips.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.title || t.destination} ({t.start_date})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-bold text-[var(--text-secondary)] mb-1">Trip Day</label>
                    <input
                      type="number"
                      min={1}
                      max={30}
                      value={selectedDay}
                      onChange={(e) => setSelectedDay(e.target.value)}
                      className="w-full p-2.5 rounded-xl bg-[var(--bg-subtle)] border border-[var(--border-color)] font-medium text-[var(--text-primary)] focus:outline-none"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowItineraryModal(false)}
                      className="px-4 py-2 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-subtle)] font-bold"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleAddToItinerarySubmit}
                      disabled={addingItinerary || !selectedTripId}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold disabled:opacity-50"
                    >
                      {addingItinerary ? 'Adding...' : 'Confirm'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
