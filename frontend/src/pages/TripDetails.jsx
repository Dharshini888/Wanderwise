import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import api from '../api/axios';
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
import { formatTripDate } from '../utils/formatters';

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
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);
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
      const res = await api.post(`/api/trips/${tripId}/activities/${activityId}/toggle-complete`);
      if (res.status === 200 || res.status === 204) {
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
            <div className={`p-4 rounded-2xl glass-card border flex items-center gap-3 ${
              (trip?.activities_total === 0)
                ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                : 'border-blue-500/30 bg-blue-500/10 text-blue-300'
            }`}>
              <IconCalendar size={22} className={`shrink-0 ${(trip?.activities_total === 0) ? 'text-amber-400' : 'text-blue-400'}`} />
              <p className="text-xs sm:text-sm font-semibold">
                {trip?.activities_total === 0
                  ? `Trip scheduled for ${trip.start_date || 'your travel date'}. No activities have been scheduled yet.`
                  : (todayData?.upcoming_notice || `Your trip begins on ${trip.start_date || 'the start date'}. Your itinerary is ready and will become active on the start date.`)}
              </p>
            </div>
          )}

          {/* Destination Experience Adaptation Banner */}
          {trip?.compatibility_notes && trip.compatibility_notes.length > 0 && (
            <div className="p-4 rounded-2xl glass-card border border-amber-500/30 bg-amber-500/10 flex items-start gap-3 text-amber-200">
              <IconSparkles size={22} className="text-amber-400 shrink-0 mt-0.5" />
              <div className="text-xs sm:text-sm">
                <span className="font-extrabold text-amber-300 block mb-0.5">Destination Experience Adaptation:</span>
                {trip.compatibility_notes.map((note, idx) => (
                  <p key={idx} className="font-medium text-amber-100/90">{note.message}</p>
                ))}
              </div>
            </div>
          )}

          {/* Door-to-Door Financial Plan Card */}
          {trip?.budget_plan && (
            <div className="glass-card p-5 rounded-2xl border border-gray-200/20 space-y-3">
              <div className="flex justify-between items-center flex-wrap gap-2">
                <div>
                  <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
                    Door-to-Door Financial Plan ({trip.budget_plan.tier_name || 'Smart Allocation'})
                  </h3>
                  <p className="text-[11px] text-[var(--text-muted)]">
                    Total Budget: {trip.budget_plan.formatted_user_budget || `${trip.currency_symbol || '$'} ${Number(trip.budget_plan.total_user_budget || 0).toLocaleString()}`} • Est. Total Cost: {trip.budget_plan.formatted_total_estimated_cost || `${trip.currency_symbol || '$'} ${Number(trip.budget_plan.total_estimated_trip_cost || 0).toLocaleString()}`}
                  </p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border ${
                  trip.budget_plan.is_feasible
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                }`}>
                  {trip.budget_plan.is_feasible
                    ? 'Budget Feasible'
                    : `Over Budget (${trip.budget_plan.formatted_shortfall || 'Shortfall'} / +${trip.budget_plan.shortfall_percentage || 0}%)`}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {(Array.isArray(trip.budget_plan.categories) ? trip.budget_plan.categories : []).map((cat, idx) => {
                  const isShortfall = cat.estimated_cost && cat.allocated_amount && cat.estimated_cost > cat.allocated_amount;
                  return (
                    <div key={cat.key || idx} className={`p-2.5 rounded-xl border ${
                      isShortfall ? 'bg-amber-500/5 border-amber-500/20' : 'bg-white/5 border-white/10'
                    }`}>
                      <span className="text-[10px] text-[var(--text-muted)] block font-semibold truncate">{cat.label} ({cat.percentage}%)</span>
                      <div className="flex items-baseline justify-between gap-1 mt-1">
                        <div>
                          <span className="text-[9px] text-gray-400 block uppercase font-mono">Allocated</span>
                          <span className="font-bold text-[var(--text-primary)] text-[11px]">{cat.formatted || cat.formatted_allocated || `${trip.currency_symbol || '$'} ${cat.amount}`}</span>
                        </div>
                        {cat.formatted_estimated && (
                          <div className="text-right">
                            <span className="text-[9px] text-gray-400 block uppercase font-mono">Est. Cost</span>
                            <span className={`font-bold text-[11px] ${isShortfall ? 'text-amber-400' : 'text-emerald-400'}`}>
                              {cat.formatted_estimated}
                            </span>
                          </div>
                        )}
                      </div>
                      {cat.unit_rate && (
                        <div className="mt-1 pt-1 border-t border-white/5 flex items-center justify-between text-[9px] text-gray-400">
                          <span className="truncate" title={cat.pricing_basis}>{cat.pricing_basis || 'Unit Basis'}</span>
                          <span className="font-mono text-gray-300 shrink-0">{cat.unit_rate}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Category Reconciliation & Planning Assumptions */}
              {trip.budget_plan.category_reconciliation?.assumptions && (
                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-200 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[11px] uppercase tracking-wider text-blue-300">Planning Assumptions</span>
                    <span className="text-[10px] font-mono text-blue-300">{trip.budget_plan.category_reconciliation.assumptions.comfort_tier} Tier</span>
                  </div>
                  <p className="text-[11px] text-blue-100 leading-snug">
                    {trip.budget_plan.category_reconciliation.assumptions.basis_description}
                  </p>
                </div>
              )}

              {/* Shortfall Categories Breakdown (if any category exceeds allocated) */}
              {trip.budget_plan.category_reconciliation?.shortfall_categories?.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[11px] uppercase tracking-wider text-amber-300">
                      Category Shortfall Breakdown ({trip.budget_plan.category_reconciliation.shortfall_categories.length} categories exceed baseline allocation)
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {trip.budget_plan.category_reconciliation.shortfall_categories.map((sc) => (
                      <div key={sc.key} className="flex items-center justify-between text-[11px] py-1 border-b border-amber-500/10 last:border-b-0 flex-wrap gap-1">
                        <span className="font-semibold">{sc.label}:</span>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">Allocated: {sc.formatted_allocated}</span>
                          <span>→</span>
                          <span className="text-amber-300 font-bold">Est: {sc.formatted_estimated}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold">
                            +{sc.formatted_shortfall}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Total Categories Allocation Parity Banner */}
              <div className="flex items-center justify-between text-[11px] p-2.5 rounded-xl bg-white/5 border border-white/10 font-medium text-gray-300">
                <span>Total Allocated Across 8 Categories:</span>
                <span className="font-extrabold text-white text-xs font-mono">
                  {trip.budget_plan.formatted_user_budget || `${trip.currency_symbol || '₹'} ${trip.budget}`} (100.0% Allocation)
                </span>
              </div>

              {/* Over Budget Advisory Notice */}
              {!trip.budget_plan.is_feasible && trip.budget_plan.feasibility_notes?.length > 0 && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  <span className="font-bold block mb-0.5">Budget Advisory Notice:</span>
                  {trip.budget_plan.feasibility_notes[0]}
                </div>
              )}

              {/* Contingency vs Surplus Buffer Explanation */}
              {trip.budget_plan.contingency_explanation && (
                <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-200 text-[11px] leading-relaxed">
                  <span className="font-bold text-purple-300 block mb-0.5">Contingency Reserve & Surplus Buffer Explanation:</span>
                  {trip.budget_plan.contingency_explanation}
                </div>
              )}

              {/* Bottom-Up Estimation, Buffer & Provenance */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/10 text-[11px] text-[var(--text-muted)]">
                <div className="flex items-center gap-3 flex-wrap">
                  {(trip.budget_plan.remaining_surplus_buffer !== undefined || trip.budget_plan.remaining_budget !== undefined) && (
                    <span>
                      Surplus Buffer: <strong className="text-emerald-400 font-extrabold">
                        {trip.budget_plan.formatted_remaining_surplus || trip.budget_plan.formatted_remaining_budget || `${trip.currency_symbol || '₹'} ${trip.budget_plan.remaining_surplus_buffer ?? trip.budget_plan.remaining_budget}`}
                      </strong> ({trip.budget_plan.surplus_buffer_percentage}% reserve)
                    </span>
                  )}
                  {trip.budget_plan.uncertainty_range && (
                    <span>
                      Uncertainty Range: <strong className="text-blue-300 font-semibold">
                        {trip.budget_plan.formatted_uncertainty_range || trip.budget_plan.uncertainty_range.formatted_range || `${trip.currency_symbol || '₹'} ${trip.budget_plan.uncertainty_range.min_cost ?? trip.budget_plan.uncertainty_range.min ?? 0} – ${trip.currency_symbol || '₹'} ${trip.budget_plan.uncertainty_range.max_cost ?? trip.budget_plan.uncertainty_range.max ?? 0}`}
                      </strong>
                    </span>
                  )}
                </div>
                {(trip.budget_plan.pricing_source || typeof trip.budget_plan.cost_provenance === 'string') && (
                  <span className="text-[10px] text-gray-400 italic">
                    Provenance: {typeof trip.budget_plan.cost_provenance === 'string'
                      ? trip.budget_plan.cost_provenance
                      : (trip.budget_plan.pricing_source || 'Verified Municipal & Market Benchmarks')}
                  </span>
                )}
              </div>

              {/* Sourced Cost Provenance Transparency Breakdown */}
              {trip.budget_plan.cost_provenance && typeof trip.budget_plan.cost_provenance === 'object' && (
                <div className="pt-2 border-t border-white/5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-400">
                      Cost Provenance & Transparency
                    </span>
                    <span className="text-[9px] text-gray-400 italic">
                      {trip.budget_plan.pricing_source || 'WanderWise Central Budget Engine'}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1.5 text-[10px]">
                    {Object.entries(trip.budget_plan.cost_provenance).map(([catKey, item]) => {
                      const entry = typeof item === 'object' && item !== null ? item : { source: String(item) };
                      return (
                        <div key={catKey} className="p-1.5 rounded-lg bg-white/5 border border-white/5 flex flex-col justify-between">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-gray-300 capitalize">{catKey.replace('_', ' ')}</span>
                            {entry.status && (
                              <span className="text-[9px] px-1 rounded bg-blue-500/20 text-blue-300 font-mono">
                                {entry.status}
                              </span>
                            )}
                          </div>
                          <span className="text-[9px] text-gray-400 truncate mt-0.5" title={entry.notes || entry.source}>
                            {entry.source || 'Standard Benchmark'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Smart Weather Replanning Card */}
          {todayData?.smart_recommendation && !todayData?.is_upcoming_trip && (
            <SmartReplanningCard recommendation={todayData.smart_recommendation} />
          )}

          {/* Execution Progress & Metrics Card */}
          {(todayData?.progress || (trip?.itinerary_days && trip.itinerary_days.length > 0)) && (
            <TripProgressCard
              progress={todayData?.progress || {
                completed_count: (trip.itinerary_days[0]?.activities || []).filter(a => a.is_completed).length,
                total_count: (trip.itinerary_days[0]?.activities || []).length,
                percentage: 0
              }}
              currency={trip.currency || 'USD'}
              isUpcoming={todayData?.is_upcoming_trip || (trip?.start_date && new Date().toISOString().split('T')[0] < String(trip.start_date).split('T')[0])}
              startDateFormatted={formatTripDate(trip?.start_date, 'full')}
            />
          )}

          {/* Multi-Day Itinerary Tabs Navigation */}
          {trip?.itinerary_days && trip.itinerary_days.length > 0 && (
            <div className="glass-card p-3 rounded-2xl flex items-center gap-2 overflow-x-auto custom-scrollbar">
              {trip.itinerary_days.map((d, idx) => {
                const isSelected = selectedDayIdx === idx;
                const actCount = (d.activities || []).length;
                return (
                  <button
                    key={d.id || idx}
                    onClick={() => setSelectedDayIdx(idx)}
                    className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-1.5 cursor-pointer ${
                      isSelected
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10'
                    }`}
                  >
                    <span>Day {d.day_number}</span>
                    <span className="opacity-80 font-normal text-[11px]">({formatTripDate(d.date, 'short')})</span>
                    {actCount > 0 && (
                      <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-white/20 text-white' : 'bg-white/10 text-gray-400'}`}>
                        {actCount}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Day Journey Timeline View */}
          {(() => {
            const itDays = trip?.itinerary_days || [];
            const activeDay = itDays[selectedDayIdx] || itDays[0] || null;
            const currentActivities = (activeDay?.activities && activeDay.activities.length > 0)
              ? activeDay.activities
              : (todayData?.activities || []);

            const isUpcomingTrip = Boolean(
              todayData?.is_upcoming_trip ||
              (trip?.start_date && new Date().toISOString().split('T')[0] < String(trip.start_date).split('T')[0])
            );

            const timelineTitle = activeDay?.title
              ? `${activeDay.title} • Day ${activeDay.day_number} (${formatTripDate(activeDay.date, 'weekday')})`
              : (isUpcomingTrip ? "Day 1 Journey Timeline (Upcoming Preview)" : "Today's Journey Timeline");

            return (
              <>
                <div ref={timelineRef}>
                  <TodayTimeline
                    activities={currentActivities}
                    onToggleComplete={handleToggleComplete}
                    titleLabel={timelineTitle}
                    isUpcoming={isUpcomingTrip}
                    startDateFormatted={formatTripDate(activeDay?.date || trip?.start_date, 'full')}
                  />
                </div>

                {/* Actionable Activity Checklist */}
                <ActivityChecklist
                  activities={currentActivities}
                  onToggleComplete={handleToggleComplete}
                />

                {/* Day's Interactive Route & Map Preview */}
                <TripItineraryMap
                  stops={
                    (activeDay?.route_summary?.stops && activeDay.route_summary.stops.length > 0)
                      ? activeDay.route_summary.stops
                      : (todayData?.route_summary?.stops && todayData.route_summary.stops.length > 0)
                      ? todayData.route_summary.stops
                      : (currentActivities || [])
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
                  destination={trip.destination}
                  routeGeometry={activeDay?.route_summary?.route_geometry || todayData?.route_summary?.route_geometry || []}
                  totalDistanceKm={activeDay?.route_summary?.total_distance_km || todayData?.route_summary?.total_distance_km || 0}
                  totalDurationMins={activeDay?.route_summary?.total_duration_minutes || todayData?.route_summary?.total_duration_minutes || 0}
                  verificationStatus={activeDay?.route_summary?.verification_status || todayData?.route_summary?.verification_status || 'Verified Routes & Coordinates'}
                  onOpenTransit={() => {
                    const stops = (currentActivities || []).filter(a => a.place?.latitude && a.place?.longitude);
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
            );
          })()}
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
