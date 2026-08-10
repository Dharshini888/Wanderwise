import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  IconArrowLeft, IconCalendar, IconMapPin, IconShare, IconSparkles,
  IconCopy, IconArchive, IconTrash, IconHeart, IconHeartFilled, IconWallet,
  IconMap, IconReceipt2, IconSparkles as IconAi
} from '@tabler/icons-react';

import TripStatusBadge from '../components/trips/TripStatusBadge';
import TripJourneyHeader from '../components/trips/TripJourneyHeader';
import TodayTimeline from '../components/trips/TodayTimeline';
import ActivityChecklist from '../components/trips/ActivityChecklist';
import SmartReplanningCard from '../components/trips/SmartReplanningCard';
import TripProgressCard from '../components/trips/TripProgressCard';
import CompletedTripMemoryView from '../components/trips/CompletedTripMemoryView';
import ItineraryEditor from '../components/trips/ItineraryEditor';

import {
  getTripDetails, toggleFavoriteTrip, archiveTrip, restoreTrip,
  deleteTrip, duplicateTrip, shareTrip, generateItinerary,
  regenerateDay, toggleActivityLock, deleteActivity, addCustomActivity
} from '../api/trips';

const API_BASE = 'http://localhost:8000/api';

export default function TripDetails() {
  const { tripId } = useParams();
  const navigate = useNavigate();

  const [trip, setTrip] = useState(null);
  const [todayData, setTodayData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const timelineRef = useRef(null);

  const token = localStorage.getItem('token');

  const loadTripData = async () => {
    try {
      const data = await getTripDetails(tripId);
      setTrip(data);

      // Fetch today's execution itinerary from /api/trips/{trip_id}/today
      const res = await fetch(`${API_BASE}/trips/${tripId}/today`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const todayJson = await res.json();
        setTodayData(todayJson);
      }
    } catch (_) {}
    setLoading(false);
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
    } catch (_) {}
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
    } catch (_) {}
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
      <div className="flex items-center justify-between gap-3">
        <Link
          to="/trips"
          className="inline-flex items-center gap-1.5 text-xs font-extrabold text-[var(--text-muted)] hover:text-[var(--color-primary-600)] transition-colors"
        >
          <IconArrowLeft size={16} /> Back to My Trips
        </Link>

        <div className="flex items-center gap-2">
          <Link
            to={`/trips/${tripId}/live`}
            state={{ origin: "Home City", destination: trip.destination, budget: trip.budget_limit || 50000 }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-extrabold shadow-sm transition-all"
          >
            <IconMap size={16} /> Start Trip Session
          </Link>
          <Link
            to={`/expenses/${tripId}`}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold shadow-sm transition-all"
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

          {/* Map Preview Placeholder Card */}
          <div className="glass-card p-5 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
                <IconMap size={18} className="text-purple-500" />
                Today's Route & Map Preview
              </h3>
              <span className="text-xs text-[var(--text-muted)] font-semibold">
                {todayData?.activities?.length || 5} Stops • ~12 km distance
              </span>
            </div>

            <div className="h-44 rounded-xl bg-slate-900/80 border border-[var(--border-color)] flex flex-col items-center justify-center text-center p-4 relative overflow-hidden group">
              <div className="w-12 h-12 rounded-full bg-purple-500/10 text-purple-400 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                <IconMap size={28} />
              </div>
              <p className="text-xs font-bold text-[var(--text-primary)]">AI Smart Transit Assistant</p>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5 max-w-sm mb-3">
                Live maps, delay predictions, multimodal comparisons, and AI routing optimization
              </p>
              <button 
                onClick={() => navigate(`/trips/${tripId}/transit`)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 transition-colors shadow-lg shadow-purple-500/20"
              >
                <IconMap size={14} /> Open AI Transit Map
              </button>
            </div>
          </div>
        </>
      )}

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
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--color-primary-600)] hover:bg-blue-700 text-white font-extrabold text-xs shadow-md transition-all disabled:opacity-50"
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

      {/* Collapsed Future AI Feature Placeholders */}
      <details className="glass-card p-4 rounded-2xl text-xs text-[var(--text-muted)] cursor-pointer group">
        <summary className="font-bold text-[var(--text-primary)] flex items-center gap-2 list-none">
          <IconAi className="text-amber-400" size={18} />
          <span>Upcoming AI Enhancements & Predictive Tools</span>
        </summary>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 mt-2 border-t border-[var(--border-color)]">
          <div className="p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-center">
            <span className="text-lg">🔮</span>
            <div className="font-extrabold text-[var(--text-primary)] mt-1">Crowd Prediction</div>
            <div className="text-[10px] text-[var(--text-muted)]">Real-time venue occupancy forecast</div>
          </div>
          <div className="p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-center">
            <span className="text-lg">🗺️</span>
            <div className="font-extrabold text-[var(--text-primary)] mt-1">Route Optimizer</div>
            <div className="text-[10px] text-[var(--text-muted)]">AI multi-stop transit ordering</div>
          </div>
          <div className="p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-center">
            <span className="text-lg">🧳</span>
            <div className="font-extrabold text-[var(--text-primary)] mt-1">Smart Packing</div>
            <div className="text-[10px] text-[var(--text-muted)]">Weather-matched item list</div>
          </div>
          <div className="p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-center">
            <span className="text-lg">⏱️</span>
            <div className="font-extrabold text-[var(--text-primary)] mt-1">Delay Forecaster</div>
            <div className="text-[10px] text-[var(--text-muted)]">Traffic & flight alert predictor</div>
          </div>
        </div>
      </details>
    </div>
  );
}
