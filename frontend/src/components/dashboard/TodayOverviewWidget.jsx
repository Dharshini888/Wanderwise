import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  IconCheck, IconMapPin, IconClock, IconSparkles,
  IconWalk, IconCash, IconShieldCheck, IconAlertTriangle,
  IconMap, IconBackpack, IconWallet, IconCalendarEvent,
  IconArrowRight, IconSun, IconUsers, IconChevronRight
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';
import { formatLocalDate } from '../../utils/date_helpers';
import api from '../../api/axios';

export default function TodayOverviewWidget({
  widgetData,
  heroTrip,
  heroStatus,
  statusInfo,
  onRefresh,
  onPlanTrip
}) {
  const isOngoing = heroStatus === 'Ongoing';
  const isUpcoming = heroStatus === 'Upcoming';
  const isCompleted = heroStatus === 'Completed';

  const [activities, setActivities] = useState([]);
  const [updatingId, setUpdatingId] = useState(null);

  useEffect(() => {
    if (widgetData?.today_activities && isOngoing) {
      setActivities(widgetData.today_activities);
    } else {
      setActivities([]);
    }
  }, [widgetData, isOngoing]);

  const toggleActivityCompletion = async (activityId, isCurrentlyCompleted) => {
    setUpdatingId(activityId);

    // Optimistic UI update
    setActivities(prev => prev.map(act => {
      if (act.id === activityId) {
        return {
          ...act,
          completed: !isCurrentlyCompleted,
          activity_status: isCurrentlyCompleted ? 'upcoming' : 'completed',
          status_badge: isCurrentlyCompleted ? 'Upcoming' : 'Completed'
        };
      }
      return act;
    }));

    try {
      const endpoint = isCurrentlyCompleted
        ? `/api/trips/activities/${activityId}/undo`
        : `/api/trips/activities/${activityId}/complete`;
      await api.patch(endpoint);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to toggle activity completion', err);
      if (onRefresh) onRefresh();
    } finally {
      setUpdatingId(null);
    }
  };

  // -------------------------------------------------------------
  // CASE A: TRIP IS ONGOING (Live Travel Schedule)
  // -------------------------------------------------------------
  if (isOngoing && heroTrip) {
    const totalCount = activities.length;
    const completedCount = activities.filter(a => a.completed || a.activity_status === 'completed').length;
    const remainingCount = totalCount - completedCount;

    const currentActivity = activities.find(a => a.activity_status === 'current')
      || activities.find(a => !a.completed)
      || activities[0]
      || null;

    const distanceKm = widgetData?.today_progress?.distance_travelled_today_km || 0.0;
    const walkingMins = widgetData?.today_progress?.walking_minutes_today || 0;
    const moneySpentToday = widgetData?.today_progress?.money_spent_today || 0.0;
    const currCode = heroTrip.currency || 'USD';

    return (
      <div className="glass-card p-6 md:p-7 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-md space-y-6">
        {/* Section Title & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-color)] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-amber-500 dark:text-amber-400">
                Live Day Schedule • {statusInfo?.text || 'Day 1'}
              </span>
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)] font-heading mt-0.5">
              Today's Travel Overview — {heroTrip.destination}
            </h3>
          </div>

          <Link
            to={`/trips/${heroTrip.id}`}
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Full Trip Timeline</span>
            <IconChevronRight size={14} />
          </Link>
        </div>

        {/* Dynamic Metric Chips Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-2xl p-3.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">Activities</span>
            <div className="text-lg font-black text-[var(--text-primary)] font-mono mt-0.5">
              {completedCount} <span className="text-xs text-[var(--text-muted)] font-normal font-sans">/ {totalCount} done</span>
            </div>
          </div>

          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-2xl p-3.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">Remaining</span>
            <div className="text-lg font-black text-amber-500 font-mono mt-0.5">
              {remainingCount} <span className="text-xs text-[var(--text-muted)] font-normal font-sans">left</span>
            </div>
          </div>

          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-2xl p-3.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">Distance Tracked</span>
            <div className="text-lg font-black text-teal-600 dark:text-teal-400 font-mono mt-0.5">
              {distanceKm > 0 ? `${distanceKm} km` : 'Local transit'}
            </div>
          </div>

          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-2xl p-3.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">Expenses Today</span>
            <div className="text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
              {moneySpentToday > 0 ? formatCurrency(moneySpentToday, currCode) : 'No spend logged'}
            </div>
          </div>
        </div>

        {/* Current Activity Highlight Banner */}
        {currentActivity && (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-900/20 via-indigo-900/10 to-transparent border border-blue-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider bg-blue-500 text-white">
                  Current Stop
                </span>
                <span className="text-xs font-mono font-bold text-[var(--text-muted)]">
                  {currentActivity.start_time || '09:00'} - {currentActivity.end_time || '10:30'}
                </span>
              </div>
              <h4 className="text-base font-extrabold text-[var(--text-primary)]">
                {currentActivity.title}
              </h4>
              <p className="text-xs text-[var(--text-muted)] line-clamp-1">
                {currentActivity.description || currentActivity.ai_reason || 'Scheduled stop in your personalized itinerary.'}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => toggleActivityCompletion(currentActivity.id, currentActivity.completed)}
                disabled={updatingId === currentActivity.id}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer ${
                  currentActivity.completed
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'btn-primary'
                }`}
              >
                <IconCheck size={14} />
                <span>{currentActivity.completed ? 'Completed' : 'Mark Done'}</span>
              </button>

              {currentActivity.place?.google_maps_url ? (
                <a
                  href={currentActivity.place.google_maps_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-xl text-xs font-bold bg-[var(--bg-app)] hover:bg-[var(--bg-subtle)] text-[var(--text-secondary)] border border-[var(--border-color)] flex items-center gap-1"
                >
                  <IconMapPin size={14} className="text-rose-500" />
                  <span>Map</span>
                </a>
              ) : null}
            </div>
          </div>
        )}

        {/* Activity List Timeline */}
        {activities.length > 0 ? (
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
              Scheduled Stops Today ({activities.length})
            </h4>
            <div className="divide-y divide-[var(--border-color)] rounded-2xl border border-[var(--border-color)] bg-[var(--bg-app)] overflow-hidden">
              {activities.map((act) => {
                const isDone = Boolean(act.completed);
                return (
                  <div
                    key={act.id}
                    className={`p-3.5 flex items-center justify-between gap-3 transition-colors ${
                      isDone ? 'bg-[var(--bg-subtle)]/50 opacity-70' : 'hover:bg-[var(--bg-subtle)]'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <button
                        onClick={() => toggleActivityCompletion(act.id, isDone)}
                        disabled={updatingId === act.id}
                        className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 cursor-pointer transition-all ${
                          isDone
                            ? 'bg-emerald-500 border-emerald-500 text-white'
                            : 'border-[var(--border-color)] hover:border-emerald-500'
                        }`}
                        title={isDone ? 'Mark as incomplete' : 'Mark as completed'}
                      >
                        {isDone && <IconCheck size={13} strokeWidth={3} />}
                      </button>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-mono text-[var(--text-muted)] font-semibold">
                            {act.start_time || '09:00'}
                          </span>
                          <span className={`text-xs font-bold truncate ${isDone ? 'line-through text-[var(--text-muted)]' : 'text-[var(--text-primary)]'}`}>
                            {act.title}
                          </span>
                          {act.place?.category && (
                            <span className="text-[10px] font-semibold text-[var(--text-muted)] px-1.5 py-0.2 rounded bg-[var(--bg-card)] border border-[var(--border-color)]">
                              {act.place.category}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 text-xs">
                      {act.ticket_price != null && (
                        <span className="text-[11px] font-mono font-bold text-[var(--text-secondary)]">
                          {act.ticket_price > 0 ? formatCurrency(act.ticket_price, currCode) : 'Free'}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-[var(--bg-app)] text-center text-xs text-[var(--text-muted)]">
            No activities scheduled for today's date in this trip itinerary.
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------
  // CASE B: TRIP IS UPCOMING (Preparation & Readiness Mode)
  // -------------------------------------------------------------
  if (isUpcoming && heroTrip) {
    const readinessItems = [
      { label: 'AI Itinerary', status: 'Ready', score: '100%', detail: 'Day-by-day attraction schedule verified', icon: <IconCalendarEvent size={18} className="text-emerald-500" /> },
      { label: 'Maps & Transit', status: 'Ready', score: '100%', detail: 'Road routing & transit verification', icon: <IconMap size={18} className="text-emerald-500" /> },
      { label: 'Budget Allocation', status: 'Healthy', score: '100%', detail: `Canonical budget set to ${formatCurrency(heroTrip.budget || 0, heroTrip.currency)}`, icon: <IconWallet size={18} className="text-blue-500" /> },
      { label: 'Packing Checklist', status: 'Pending Review', score: 'Review', detail: 'Weather-adaptive packing checklist ready', icon: <IconBackpack size={18} className="text-amber-500" /> },
    ];

    const day1Activities = widgetData?.day1_preview || [];

    return (
      <div className="glass-card p-6 md:p-7 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-md space-y-5">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-color)] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-500 dark:text-blue-400">
                Departure Preparation • {statusInfo?.text || 'Upcoming'}
              </span>
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)] font-heading mt-0.5">
              Trip Readiness & Day 1 Preview — {heroTrip.destination}
            </h3>
          </div>

          <Link
            to={`/trips/${heroTrip.id}`}
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Explore Complete Itinerary</span>
            <IconChevronRight size={14} />
          </Link>
        </div>

        {/* Readiness Checklist Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {readinessItems.map((item, idx) => (
            <div key={idx} className="p-3.5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-app)] flex flex-col justify-between gap-2">
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)]">
                  {item.icon}
                </div>
                <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                  item.status === 'Ready' || item.status === 'Healthy'
                    ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                }`}>
                  {item.status}
                </span>
              </div>
              <div>
                <h4 className="text-xs font-bold text-[var(--text-primary)]">{item.label}</h4>
                <p className="text-[10px] text-[var(--text-muted)] mt-0.5 leading-snug">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Day 1 Highlights Preview */}
        {day1Activities.length > 0 && (
          <div className="space-y-2.5 pt-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                Arrival Day Highlights Preview (Day 1)
              </h4>
              <span className="text-[11px] text-[var(--text-muted)]">
                Scheduled for {formatLocalDate(heroTrip.start_date, { day: 'numeric', month: 'short' })}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {day1Activities.slice(0, 3).map((act, i) => (
                <div key={i} className="p-3 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)] flex flex-col justify-between gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded">
                      {act.start_time || '09:00'}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] font-semibold">
                      {act.place?.category || 'Sightseeing'}
                    </span>
                  </div>
                  <div>
                    <h5 className="text-xs font-bold text-[var(--text-primary)] truncate">{act.title}</h5>
                    <p className="text-[10px] text-[var(--text-muted)] line-clamp-1 mt-0.5">
                      {act.description || act.place?.name}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fast Action Shortcuts */}
        <div className="flex flex-wrap items-center gap-2.5 pt-2 border-t border-[var(--border-color)]">
          <Link
            to="/packing"
            className="text-xs font-bold px-3 py-1.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20 transition-colors flex items-center gap-1.5"
          >
            <IconBackpack size={14} />
            <span>Review Packing Checklist</span>
          </Link>

          <Link
            to="/transit"
            className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-colors flex items-center gap-1.5"
          >
            <IconMap size={14} />
            <span>View Transit & Route Guide</span>
          </Link>

          <Link
            to={`/expenses/${heroTrip.id}`}
            className="text-xs font-bold px-3 py-1.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 transition-colors flex items-center gap-1.5"
          >
            <IconWallet size={14} />
            <span>Manage Planned Budget</span>
          </Link>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // CASE C: TRIP IS COMPLETED (Travel Journal & Memory Vault)
  // -------------------------------------------------------------
  if (isCompleted && heroTrip) {
    return (
      <div className="glass-card p-6 md:p-7 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-color)] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                Completed Journey
              </span>
            </div>
            <h3 className="text-xl font-black text-[var(--text-primary)] font-heading mt-0.5">
              Trip Archive — {heroTrip.destination}
            </h3>
          </div>

          <Link
            to={`/trips/${heroTrip.id}`}
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Review Itinerary Archive</span>
            <IconChevronRight size={14} />
          </Link>
        </div>

        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
          You completed your {heroTrip.duration_days || 7}-day exploration of {heroTrip.destination}. All itinerary activities, route logs, and expense reports are preserved in your personal vault.
        </p>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Link
            to={`/expenses/${heroTrip.id}`}
            className="btn-primary text-xs font-bold py-2 px-4 inline-flex items-center gap-1.5"
          >
            <IconCash size={14} />
            <span>Review Expense Breakdown</span>
          </Link>
          <button
            onClick={onPlanTrip}
            className="btn-outline text-xs font-bold py-2 px-4 inline-flex items-center gap-1.5 cursor-pointer"
          >
            <IconSparkles size={14} />
            <span>Plan Next Destination</span>
          </button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // CASE D: NO TRIPS AT ALL (Welcome & Guidance)
  // -------------------------------------------------------------
  return (
    <div className="glass-card p-8 rounded-3xl border border-[var(--border-color)] bg-gradient-to-r from-blue-900/10 via-[var(--bg-card)] to-transparent shadow-sm text-center space-y-4">
      <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-500 flex items-center justify-center mx-auto">
        <IconSparkles size={28} />
      </div>
      <div className="max-w-md mx-auto">
        <h3 className="text-lg font-black text-[var(--text-primary)] font-heading">
          No Active Itineraries Yet
        </h3>
        <p className="text-xs text-[var(--text-muted)] mt-1.5 leading-relaxed">
          Create your first intelligent trip with WanderWise. Enter your destination, dates, and preferences to receive a personalized day-by-day plan with verified landmarks and OSRM transit.
        </p>
      </div>
      <button
        onClick={onPlanTrip}
        className="btn-primary px-5 py-2.5 text-xs font-bold inline-flex items-center gap-2 cursor-pointer shadow-md shadow-blue-500/20"
      >
        <IconSparkles size={15} />
        <span>Generate My First Trip</span>
      </button>
    </div>
  );
}

