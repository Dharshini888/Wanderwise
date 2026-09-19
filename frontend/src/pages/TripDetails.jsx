import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  IconArrowLeft, IconCalendar, IconMapPin, IconShare, IconSparkles,
  IconCopy, IconArchive, IconTrash, IconHeart, IconHeartFilled, IconWallet,
  IconMap, IconReceipt2, IconCloudCheck, IconSparkles as IconAi, IconChecklist, IconArrowRight
} from '@tabler/icons-react';
import { getChecklist } from '../api/checklist';

import TripStatusBadge from '../components/trips/TripStatusBadge';
import TripJourneyHeader from '../components/trips/TripJourneyHeader';
import TodayTimeline from '../components/trips/TodayTimeline';
import ActivityChecklist from '../components/trips/ActivityChecklist';
import SmartReplanningCard from '../components/trips/SmartReplanningCard';
import TripProgressCard from '../components/trips/TripProgressCard';
import CompletedTripMemoryView from '../components/trips/CompletedTripMemoryView';
import ItineraryEditor from '../components/trips/ItineraryEditor';
import OfflinePackageModal from '../components/trips/OfflinePackageModal';
import TripDocumentsWidget from '../components/trips/TripDocumentsWidget';
import TripItineraryMap from '../components/trips/TripItineraryMap';

import {
  getTripDetails, getTodayTripDetails, toggleFavoriteTrip, archiveTrip, restoreTrip,
  deleteTrip, duplicateTrip, shareTrip, generateItinerary,
  regenerateDay, toggleActivityLock, deleteActivity, addCustomActivity
} from '../api/trips';

function TripChecklistSummary({ tripId }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!tripId) return;
    getChecklist(tripId).then(setData).catch(() => {});
  }, [tripId]);

  if (!data?.summary) return null;
  const { readiness_percentage, completed, total, pending } = data.summary;

  return (
    <div className="glass-card p-5 rounded-2xl flex items-center justify-between gap-4 border border-[var(--border-color)]">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
          <IconChecklist size={22} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">Smart Checklist</h3>
            <span className="text-xs font-black text-blue-600 dark:text-blue-400 font-mono">{readiness_percentage}% Ready</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-medium">
            {completed} / {total} completed • {pending} tasks remaining
          </p>
        </div>
      </div>

      <button
        onClick={() => navigate(`/checklist?tripId=${tripId}`)}
        className="px-3.5 py-2 rounded-xl text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 transition-all flex items-center gap-1 shrink-0 cursor-pointer"
      >
        <span>View Checklist</span>
        <IconArrowRight size={14} />
      </button>
    </div>
  );
}

export default function TripDetails() {
  const { tripId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const initialTrip = location.state?.initialTrip || null;
  const [trip, setTrip] = useState(initialTrip);
  const [todayData, setTodayData] = useState(null);
  const [loading, setLoading] = useState(!initialTrip);
  const [generating, setGenerating] = useState(false);
  const [showOfflineModal, setShowOfflineModal] = useState(false);
  const timelineRef = useRef(null);

  const loadTripData = async () => {
    const startTime = performance.now();
    try {
      const data = await getTripDetails(tripId);
      setTrip(data);
      setLoading(false); // Priority 1 rendering unblocked
      console.log(`[TripDetails] Core trip details loaded for Trip ${tripId} in ${Math.round(performance.now() - startTime)}ms`);

      // Asynchronously load today's execution itinerary without blocking core page
      getTodayTripDetails(tripId)
        .then((todayJson) => {
          if (todayJson) setTodayData(todayJson);
        })
        .catch(() => {});
    } catch (_) {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTripData();
  }, [tripId]);

  const handleToggleComplete = async (activityId) => {
    try {
      const res = await fetch(`${API_BASE}/trips/${tripId}/activities/${activityId}/toggle-complete`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        loadTripData();
      }
    } catch (_) {}
  };

  const handleFavorite = async () => {
    if (!trip) return;
    setTrip({ ...trip, is_favorite: !trip.is_favorite });
    await toggleFavoriteTrip(tripId);
    loadTripData();
  };

  const handleShare = async () => {
    try {
      const res = await shareTrip(tripId);
      navigator.clipboard.writeText(res.share_url);
      alert('Share link copied to clipboard!');
    } catch (_) {}
  };

  const handleGenerateFull = async () => {
    setGenerating(true);
    try {
      await generateItinerary(tripId);
      loadTripData();
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to generate itinerary");
    }
    setGenerating(false);
  };

  const handleLockToggle = async (dayNumber, activityId) => {
    try {
      await toggleActivityLock(tripId, activityId);
      loadTripData();
    } catch (_) {}
  };

  const handleDeleteActivity = async (dayNumber, activityId) => {
    try {
      await deleteActivity(tripId, activityId);
      loadTripData();
    } catch (_) {}
  };

  const handleRegenerateDay = async (dayNumber) => {
    try {
      await regenerateDay(tripId, dayNumber);
      loadTripData();
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to regenerate day");
    }
  };

  const handleAddActivity = async (dayNumber, activityData) => {
    try {
      await addCustomActivity(tripId, dayNumber, activityData);
      loadTripData();
    } catch (_) {}
  };

  const scrollToTimeline = () => {
    if (timelineRef.current) {
      timelineRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-6 pb-12 animate-pulse">
        <div className="h-40 glass-card rounded-2xl" />
        <div className="h-64 glass-card rounded-2xl" />
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="glass-card p-12 text-center space-y-4 rounded-2xl my-8">
        <h2 className="text-xl font-bold font-heading text-[var(--text-primary)]">Trip Not Found</h2>
        <Link to="/trips" className="btn btn-primary px-5 py-2.5 text-xs font-bold inline-flex items-center gap-1.5">
          <IconArrowLeft size={16} /> Back to My Trips
        </Link>
      </div>
    );
  }

  const isCompleted = trip.status === 'Completed' || (todayData && todayData.trip_status === 'Completed');

  return (
    <div className="flex flex-col gap-6 pb-12">
      {/* Top Navigation & Action Toolbar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <Link
          to="/trips"
          className="inline-flex items-center gap-1.5 text-xs font-extrabold text-[var(--text-muted)] hover:text-[var(--color-primary-600)] transition-colors"
        >
          <IconArrowLeft size={16} /> Back to My Trips
        </Link>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowOfflineModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold shadow-sm transition-all cursor-pointer"
            title="Download Trip for Offline Use"
          >
            <IconCloudCheck size={16} /> Offline Package
          </button>
          <Link
            to={`/trips/${tripId}/live`}
            state={{ origin: "Home City", destination: trip.destination, budget: trip.budget_limit || 50000 }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-extrabold shadow-sm transition-all"
          >
            <IconMap size={16} /> Start Trip Session
          </Link>
          <Link
            to={`/expenses/${tripId}`}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold shadow-sm transition-all"
          >
            <IconWallet size={16} /> Manage Expenses
          </Link>
          <button
            onClick={handleFavorite}
            className="p-2 rounded-xl glass-card text-red-500 hover:scale-105 transition-transform"
          >
            {trip.is_favorite ? <IconHeartFilled size={18} /> : <IconHeart size={18} />}
          </button>
          <button
            onClick={handleShare}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl glass-card text-xs font-bold text-[var(--text-primary)] hover:bg-[var(--bg-card)] transition-colors"
          >
            <IconShare size={16} /> Share
          </button>
        </div>
      </div>

      {/* COMPLETED TRIP MEMORY VIEW */}
      {isCompleted ? (
        <CompletedTripMemoryView trip={trip} onShare={handleShare} />
      ) : (
        /* ACTIVE & UPCOMING JOURNEY DASHBOARD */
        <>
          {/* Active Trip Journey Hero Header */}
          <TripJourneyHeader
            todayData={todayData}
            trip={trip}
            onResumeClick={scrollToTimeline}
          />

          {/* Upcoming Trip Notice Banner */}
          {(todayData?.is_upcoming_trip || (trip?.start_date && new Date().toISOString().split('T')[0] < String(trip.start_date).split('T')[0])) && (
            <div className="p-4 rounded-2xl glass-card border border-blue-500/30 bg-blue-500/10 flex items-center gap-3 text-blue-300">
              <IconCalendar size={22} className="text-blue-400 shrink-0" />
              <p className="text-xs sm:text-sm font-semibold">
                {todayData?.upcoming_notice || `Your trip begins on ${trip.start_date || 'the start date'}. Your itinerary is ready and will become active on the start date.`}
              </p>
            </div>
          )}

          {/* Smart Weather Replanning Card */}
          {todayData?.smart_recommendation && !todayData?.is_upcoming_trip && (
            <SmartReplanningCard recommendation={todayData.smart_recommendation} />
          )}

          {/* Execution Progress & Metrics Card */}
          {todayData?.progress && (
            <TripProgressCard progress={todayData.progress} currency={trip.currency || 'USD'} />
          )}

          {/* Today's Timeline View */}
          <div ref={timelineRef}>
            <TodayTimeline
              activities={todayData?.activities || []}
              onToggleComplete={handleToggleComplete}
            />
          </div>

          {/* Actionable Activity Checklist */}
          <ActivityChecklist
            activities={todayData?.activities || []}
            onToggleComplete={handleToggleComplete}
          />

          {/* Today's Interactive Route & Map Preview */}
          <TripItineraryMap
            stops={
              (todayData?.route_summary?.stops && todayData.route_summary.stops.length > 0)
                ? todayData.route_summary.stops
                : (trip?.itinerary_days?.[0]?.route_summary?.stops && trip.itinerary_days[0].route_summary.stops.length > 0)
                ? trip.itinerary_days[0].route_summary.stops
                : (todayData?.activities || trip?.itinerary_days?.[0]?.activities || [])
                    .map((a, idx) => ({
                      id: a.id,
                      title: a.title,
                      place_name: a.place?.name || a.title,
                      latitude: a.place?.latitude,
                      longitude: a.place?.longitude,
                      address: a.place?.address,
                      order_index: idx + 1
                    }))
                    .filter(s => s.latitude && s.longitude)
            }
            routeGeometry={todayData?.route_summary?.route_geometry || trip?.itinerary_days?.[0]?.route_summary?.route_geometry || []}
            totalDistanceKm={todayData?.route_summary?.total_distance_km || trip?.itinerary_days?.[0]?.route_summary?.total_distance_km || 0}
            totalDurationMins={todayData?.route_summary?.total_duration_minutes || trip?.itinerary_days?.[0]?.route_summary?.total_duration_minutes || 0}
            verificationStatus={todayData?.route_summary?.verification_status || trip?.itinerary_days?.[0]?.route_summary?.verification_status || 'Route Calculated'}
            onOpenTransit={() => {
              const stops = (todayData?.activities || trip?.itinerary_days?.[0]?.activities || [])
                .filter(a => a.place?.latitude && a.place?.longitude);
              const first = stops[0];
              const last = stops[stops.length - 1];
              if (first && last && first !== last) {
                const fromName = first.place?.name || first.title;
                const toName = last.place?.name || last.title;
                navigate(`/transit?from=${encodeURIComponent(fromName)}&to=${encodeURIComponent(toName)}&from_lat=${first.place.latitude}&from_lon=${first.place.longitude}&to_lat=${last.place.latitude}&to_lon=${last.place.longitude}&dest_lat=${last.place.latitude}&dest_lon=${last.place.longitude}&auto_route=true&trip_id=${tripId}`);
              } else {
                navigate(`/trips/${tripId}/transit`);
              }
            }}
          />
        </>
      )}

      {/* Smart Travel Checklist Summary Section */}
      <TripChecklistSummary tripId={trip.id} />

      {/* Trip Documents & Tickets Section */}
      <TripDocumentsWidget tripId={trip.id} tripTitle={trip.destination || trip.title} />

      {/* Daily Itinerary Workspace Editor */}
      <div className="glass-card p-5 sm:p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h2 className="text-lg font-extrabold text-[var(--text-primary)] font-heading">
              Full Itinerary Workspace
            </h2>
            <p className="text-xs text-[var(--text-muted)]">Edit, reorder, or lock specific day activities.</p>
          </div>

          <button
            onClick={handleGenerateFull}
            disabled={generating}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--color-primary-600)] hover:bg-blue-700 text-white font-extrabold text-xs shadow-md transition-all disabled:opacity-50 cursor-pointer"
          >
            <IconSparkles size={16} className={generating ? 'animate-spin' : ''} />
            {generating ? 'Regenerating...' : 'Regenerate Full AI Itinerary'}
          </button>
        </div>

        <ItineraryEditor
          trip={trip}
          onLockToggle={handleLockToggle}
          onDeleteActivity={handleDeleteActivity}
          onRegenerateDay={handleRegenerateDay}
          onAddActivity={handleAddActivity}
        />
      </div>

      {/* Offline Toolkit Modal */}
      <OfflinePackageModal
        trip={trip}
        isOpen={showOfflineModal}
        onClose={() => setShowOfflineModal(false)}
      />
    </div>
  );
}
