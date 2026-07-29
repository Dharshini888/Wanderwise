import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  IconCheck, IconMapPin, IconClock, IconSun, IconUmbrella,
  IconExternalLink, IconSparkles, IconWalk, IconFlame,
  IconArrowRight, IconShieldCheck, IconAlertTriangle, IconRefresh,
  IconBuildingStore, IconChecklist, IconCalendarEvent, IconRoute,
  IconStar, IconUsers, IconCloudRain, IconCircleCheck, IconX,

  IconCurrencyRupee, IconWallet, IconCompass, IconHourglassHigh
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

const API = 'http://localhost:8000/api';

export default function ActiveTripWorkspace({ widgetData, onRefresh }) {
  const token = localStorage.getItem('token');
  const activeTrip = widgetData?.active_trip || widgetData?.trip;

  const [activities, setActivities] = useState([]);
  const [updatingId, setUpdatingId] = useState(null);

  // Live Clock state (refreshes every 60s)
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      if (onRefresh) onRefresh();
    }, 60000);
    return () => clearInterval(timer);
  }, [onRefresh]);

  useEffect(() => {
    if (widgetData?.today_activities) {
      setActivities(widgetData.today_activities);
    }
  }, [widgetData]);

  if (!activeTrip) return null;

  // Format live clock details
  const dayName = currentTime.toLocaleDateString('en-US', { weekday: 'long' });
  const dateStr = currentTime.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
  const timeStr = currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  // Today Progress calculations
  const totalCount = activities.length;
  const completedCount = activities.filter(a => a.completed || a.activity_status === 'completed').length;
  const remainingCount = totalCount - completedCount;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const distanceKm = widgetData?.today_progress?.distance_travelled_today_km || (completedCount * 1.2).toFixed(1);
  const walkingMins = widgetData?.today_progress?.walking_minutes_today || (completedCount * 20);
  const moneySpent = widgetData?.today_progress?.money_spent_today || (completedCount * 250);
  const remainingBudget = widgetData?.today_progress?.remaining_budget || (widgetData?.budget_remaining || 2150);
  const currCode = widgetData?.currency || activeTrip.currency || 'USD';

  // Identify Current & Next Activity
  const currentActivity = activities.find(a => a.activity_status === 'current') || widgetData?.current_activity || activities.find(a => !a.completed);
  const nextActivity = activities.find(a => a.id !== currentActivity?.id && !a.completed) || widgetData?.next_activity;

  const toggleActivityCompletion = async (activityId, isCurrentlyCompleted) => {
    setUpdatingId(activityId);

    // Optimistic UI update
    setActivities(prev => prev.map(act => {
      if (act.id === activityId) {
        const newStatus = isCurrentlyCompleted ? 'upcoming' : 'completed';
        return { ...act, completed: !isCurrentlyCompleted, activity_status: newStatus };
      }
      return act;
    }));

    try {
      const endpoint = isCurrentlyCompleted ? `/activities/${activityId}/undo` : `/activities/${activityId}/complete`;
      let res = await fetch(`${API}${endpoint}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const fallbackEndpoint = isCurrentlyCompleted ? `/trips/activities/${activityId}/undo` : `/trips/activities/${activityId}/complete`;
        await fetch(`${API}${fallbackEndpoint}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          }
        });
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to toggle completion", err);
    } finally {
      setUpdatingId(null);
    }
  };

  const weather = widgetData?.weather || {};
  const currWeather = weather.current || {};
  const weatherSummary = widgetData?.weather_summary || {};
  const smartRec = widgetData?.smart_recommendation || {};

  return (
    <div className="space-y-6 animate-fadeIn">

      {/* 1. Dynamic Current Trip Header & Live Clock */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-indigo-500/30 p-6 md:p-8 shadow-2xl backdrop-blur-xl">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold uppercase tracking-wider mb-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              Currently Exploring {activeTrip.destination}
            </div>
            
            <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight flex items-center gap-3">
              <span>Day {widgetData?.current_trip_day || 3} of {widgetData?.total_days || activeTrip.duration_days || 11}</span>
            </h1>

            <p className="text-slate-400 text-sm mt-1.5 flex items-center gap-3 flex-wrap">
              <span className="text-slate-300 font-medium">{activeTrip.destination}, {activeTrip.country || 'India'}</span>
              <span>•</span>
              <span className="text-emerald-400 font-semibold">{activeTrip.travel_style || 'Solo'} Trip</span>
              <span>•</span>
              <span>{activeTrip.start_date} to {activeTrip.end_date}</span>
            </p>
          </div>

          {/* 2. Live Clock Box */}
          <div className="flex flex-col md:items-end bg-slate-800/60 border border-slate-700/80 p-4 rounded-2xl backdrop-blur-md min-w-[200px]">
            <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <IconClock className="w-3.5 h-3.5" />
              Live Companion Clock
            </span>
            <div className="text-2xl font-black text-white font-mono mt-0.5 tracking-wide">
              {timeStr}
            </div>
            <div className="text-xs text-slate-400 font-medium">
              {dayName}, {dateStr}
            </div>
          </div>
        </div>

        {/* Overall Trip Progress Line */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>Overall Trip Timeline Progress</span>
          <span className="text-emerald-400 font-bold">{progressPct}% Today Completed</span>
        </div>
        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-1.5">
          <div
            className="bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 h-full rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* 2. Next / Current Activity & Today's Progress Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* 5. Current / Next Activity Card (7 Cols) */}
        <div className="lg:col-span-7">
          {currentActivity ? (
            <div className="h-full rounded-3xl bg-slate-900/90 border border-teal-500/40 p-6 shadow-2xl relative overflow-hidden backdrop-blur-md flex flex-col justify-between">
              <div className="absolute top-0 right-0 -mr-16 -mt-16 w-56 h-56 rounded-full bg-teal-500/10 blur-2xl pointer-events-none" />

              <div>
                <div className="flex items-center justify-between border-b border-slate-800 pb-3.5 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-teal-400 animate-pulse" />
                    <span className="text-teal-400 text-xs font-extrabold uppercase tracking-wider">
                      {currentActivity.activity_status === 'current' ? 'Current Active Stop' : 'Next Scheduled Activity'}
                    </span>
                  </div>

                  <span className="px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-bold border border-teal-500/40 shadow-sm">
                    {currentActivity.countdown || `Starts at ${currentActivity.start_time || '09:00 AM'}`}
                  </span>
                </div>

                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-2xl font-black text-white tracking-tight">
                      {currentActivity.title}
                    </h3>
                    <p className="text-slate-400 text-sm mt-1 leading-relaxed line-clamp-2">
                      {currentActivity.description || 'Explore top-rated attraction and scenic viewpoints.'}
                    </p>
                  </div>

                  {/* Rating Badge */}
                  <div className="flex items-center gap-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 px-2.5 py-1 rounded-xl text-xs font-extrabold flex-shrink-0">
                    <IconStar className="w-3.5 h-3.5 fill-amber-400 stroke-none" />
                    <span>{currentActivity.place?.rating || '4.8'}</span>
                  </div>
                </div>

                {/* Badges Grid: Crowd, Weather, Hours, Distance, Cost */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mt-5">
                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Crowd Level</span>
                    <span className="font-bold text-emerald-400 flex items-center gap-1 mt-0.5">
                      <IconUsers className="w-3.5 h-3.5" />
                      {currentActivity.crowd_badge || 'Low'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Weather</span>
                    <span className="font-bold text-amber-300 flex items-center gap-1 mt-0.5">
                      {currentActivity.weather_badge || '☀️ Good Weather'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Operating Hours</span>
                    <span className="font-bold text-slate-200 mt-0.5 block">
                      Open until 7:00 PM
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Walking Transit</span>
                    <span className="font-bold text-teal-300 flex items-center gap-1 mt-0.5">
                      <IconWalk className="w-3.5 h-3.5" />
                      {currentActivity.transport_duration || '8 mins'} ({currentActivity.distance_km || '650 m'})
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Estimated Cost</span>
                    <span className="font-bold text-white mt-0.5 block">
                      {formatCurrency(currentActivity.ticket_price || 250, currCode)}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs">
                    <span className="text-slate-400 block text-[11px]">Time Slot</span>
                    <span className="font-bold text-slate-300 mt-0.5 block font-mono">
                      {currentActivity.start_time || '09:00'} - {currentActivity.end_time || '10:30'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
                {currentActivity.place?.google_maps_url ? (
                  <a
                    href={currentActivity.place.google_maps_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center gap-1.5"
                  >
                    <IconMapPin className="w-4 h-4 text-rose-400" />
                    <span>Open Maps</span>
                  </a>
                ) : (
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(currentActivity.title + ' ' + activeTrip.destination)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition flex items-center gap-1.5"
                  >
                    <IconMapPin className="w-4 h-4 text-rose-400" />
                    <span>Open Maps</span>
                  </a>
                )}

                <button
                  onClick={() => toggleActivityCompletion(currentActivity.id, currentActivity.completed)}
                  disabled={updatingId === currentActivity.id}
                  className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-black shadow-lg shadow-emerald-500/25 transition flex items-center gap-2"
                >
                  <IconCheck className="w-4 h-4 stroke-[3]" />
                  <span>{currentActivity.completed ? 'Mark Incomplete' : 'Mark Complete'}</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full rounded-3xl bg-slate-900/80 border border-slate-800 p-8 text-center flex flex-col justify-center items-center">
              <IconCircleCheck className="w-12 h-12 text-emerald-400 mb-3" />
              <h3 className="text-xl font-bold text-white">All Activities Completed Today!</h3>

              <p className="text-slate-400 text-sm mt-1">Enjoy your evening in {activeTrip.destination}.</p>
            </div>
          )}
        </div>

        {/* 6. Today's Progress Widget (5 Cols) */}
        <div className="lg:col-span-5">
          <div className="h-full rounded-3xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <IconChecklist className="w-5 h-5 text-emerald-400" />
                  <span>Today's Progress</span>
                </h3>
                <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/30">
                  {progressPct}% Done
                </span>
              </div>

              {/* Progress Stats Grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3.5 rounded-2xl bg-slate-800/50 border border-slate-700/60">
                  <span className="text-xs text-slate-400 font-medium">Activities</span>
                  <div className="text-xl font-black text-white mt-1">
                    {completedCount} <span className="text-xs text-slate-400 font-normal">/ {totalCount}</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-800/50 border border-slate-700/60">
                  <span className="text-xs text-slate-400 font-medium">Distance Travelled</span>
                  <div className="text-xl font-black text-teal-300 mt-1">
                    {distanceKm} <span className="text-xs font-normal">km</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-800/50 border border-slate-700/60">
                  <span className="text-xs text-slate-400 font-medium">Walking Time</span>
                  <div className="text-xl font-black text-cyan-300 mt-1">
                    {walkingMins} <span className="text-xs font-normal">mins</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-800/50 border border-slate-700/60">
                  <span className="text-xs text-slate-400 font-medium">Money Spent</span>
                  <div className="text-xl font-black text-amber-300 mt-1">
                    {formatCurrency(moneySpent, currCode)}
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs">
                <span className="text-emerald-300 font-medium">Remaining Budget</span>
                <span className="text-emerald-400 font-extrabold text-sm">{formatCurrency(remainingBudget, currCode)}</span>
              </div>
            </div>

            {/* Progress Bar */}
            <div>
              <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden p-0.5 border border-slate-700">
                <div
                  className="bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 h-full rounded-full transition-all duration-500 shadow-md shadow-emerald-500/40"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* 3. Today's Journey Timeline & Statuses */}
      <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 md:p-8 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-2.5">
              <IconRoute className="w-6 h-6 text-teal-400" />
              <span>Today's Journey Timeline</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Real-time activity status tracker (Completed ✔ • Current 🟢 • Upcoming ○ • Missed 🔴)
            </p>
          </div>

          <span className="text-xs font-mono px-3 py-1 rounded-xl bg-slate-800 text-slate-300 border border-slate-700">
            {completedCount} of {totalCount} Done
          </span>
        </div>

        {activities.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm">
            No activities scheduled for today. View full trip details to manage itinerary.
          </div>
        ) : (
          <div className="relative border-l-2 border-slate-800 ml-4 space-y-6 pl-6 my-4">
            {activities.map((act, idx) => {
              const status = act.activity_status || (act.completed ? 'completed' : 'upcoming');
              const isCompleted = status === 'completed';
              const isCurrent = status === 'current';
              const isMissed = status === 'missed';

              return (
                <div key={act.id || idx} className="relative group">
                  {/* Status Indicator Bullet */}
                  <span
                    className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 transition-all ${
                      isCompleted
                        ? 'bg-emerald-500 border-emerald-400 text-slate-950 shadow-md shadow-emerald-500/50'
                        : isCurrent
                        ? 'bg-teal-400 border-white ring-4 ring-teal-500/40 animate-pulse'
                        : isMissed
                        ? 'bg-rose-500 border-rose-400'
                        : 'bg-slate-900 border-slate-700'
                    }`}
                  />

                  <div className={`p-4 rounded-2xl border transition-all duration-200 ${
                    isCurrent
                      ? 'bg-slate-800/90 border-teal-500/50 ring-1 ring-teal-500/30'
                      : isCompleted
                      ? 'bg-slate-950/40 border-slate-800/60 opacity-75'
                      : 'bg-slate-800/40 border-slate-700/60 hover:border-slate-600'
                  }`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-start gap-3.5">
                        <button
                          onClick={() => toggleActivityCompletion(act.id, act.completed)}
                          disabled={updatingId === act.id}
                          className={`mt-0.5 w-6 h-6 rounded-lg border flex items-center justify-center transition-all ${
                            isCompleted
                              ? 'bg-emerald-500 border-emerald-400 text-slate-950 font-bold'
                              : 'border-slate-600 bg-slate-900/60 hover:border-emerald-400 text-transparent'
                          }`}
                        >
                          <IconCheck className="w-4 h-4 stroke-[3]" />
                        </button>

                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs text-slate-400 font-semibold">
                              {act.start_time || '09:00'} - {act.end_time || '10:30'}
                            </span>

                            <h4 className={`text-base font-extrabold ${isCompleted ? 'line-through text-slate-500' : isCurrent ? 'text-teal-300' : 'text-slate-100'}`}>
                              {act.title}
                            </h4>

                            {/* Status Badge */}
                            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${
                              isCompleted ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
                              isCurrent ? 'bg-teal-500/20 text-teal-300 border-teal-500/40' :
                              isMissed ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' :
                              'bg-slate-800 text-slate-400 border-slate-700'
                            }`}>
                              {act.status_badge || status}
                            </span>
                          </div>

                          <div className="flex items-center gap-3 text-xs text-slate-400 mt-1.5 flex-wrap">
                            <span className="flex items-center gap-1 text-amber-300 font-medium">
                              {act.weather_badge || '☀️ Good Weather'}
                            </span>
                            <span>•</span>
                            <span className="text-emerald-400 font-medium">
                              Crowd: {act.crowd_badge || 'Low'}
                            </span>
                            <span>•</span>
                            <span>{act.duration_minutes || 90} mins</span>
                            {act.place?.name && (
                              <>
                                <span>•</span>
                                <span className="text-slate-300">{act.place.name}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-end sm:self-center">
                        {act.place?.google_maps_url ? (
                          <a
                            href={act.place.google_maps_url}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition flex items-center gap-1"
                          >
                            <IconMapPin className="w-3.5 h-3.5 text-rose-400" />
                            <span>Maps</span>
                          </a>
                        ) : (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(act.title + ' ' + activeTrip.destination)}`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition flex items-center gap-1"
                          >
                            <IconMapPin className="w-3.5 h-3.5 text-rose-400" />
                            <span>Maps</span>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Weather & Smart Recommendation Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* 7. Dynamic Weather Card (6 Cols) */}
        <div className="lg:col-span-6">
          <div className="h-full rounded-3xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-3.5 mb-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <IconSun className="w-5 h-5 text-amber-400" />
                  <span>Dynamic Weather & Activity Advisor</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">{weather.city || activeTrip.destination}</span>
              </div>

              <div className="flex items-center justify-between bg-slate-800/50 p-4 rounded-2xl border border-slate-700/60 mb-4">
                <div>
                  <div className="text-3xl font-black text-white">
                    {currWeather.temperature !== undefined ? `${currWeather.temperature}°C` : '19°C'}
                  </div>
                  <p className="text-xs text-slate-300 mt-1 font-semibold">
                    {currWeather.description || 'Thunderstorm'}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Rain Probability</span>
                  <span className="text-lg font-black text-cyan-300 mt-0.5 block">
                    {weatherSummary.rain_prob || 100}%
                  </span>
                </div>
              </div>

              {/* Travel Recommendation Banner */}
              <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 mb-4">
                <span className="text-xs text-amber-300 font-bold block mb-0.5">Travel Recommendation</span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {weatherSummary.summary || 'Heavy rain expected until 2 PM. Indoor activities recommended.'}
                </p>
              </div>

              {/* Recommended & Avoid Lists */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                  <span className="font-bold text-emerald-400 block mb-1.5">Recommended</span>
                  <div className="space-y-1 text-slate-200">
                    {(weatherSummary.recommended || ['✓ Museum', '✓ Cafe', '✓ Shopping Arcade']).map((item, i) => (
                      <div key={i} className="flex items-center gap-1 font-medium">
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30">
                  <span className="font-bold text-rose-400 block mb-1.5">Avoid</span>
                  <div className="space-y-1 text-slate-300">
                    {(weatherSummary.avoid || ['✗ Beach Walk', '✗ Cliff Viewpoint', '✗ Outdoor Hiking']).map((item, i) => (
                      <div key={i} className="flex items-center gap-1 font-medium">
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 8. Smart Recommendation Card (6 Cols) */}
        <div className="lg:col-span-6">
          <div className="h-full rounded-3xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-3.5 mb-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <IconShieldCheck className="w-5 h-5 text-emerald-400" />
                  <span>Smart Recommendation Engine</span>
                </h3>
                <span className="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Rule Recommendation Service
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                    <IconAlertTriangle className="w-4 h-4" />
                    {smartRec.title || 'Smart Rain Advisory'}
                  </span>
                  <span className="text-[11px] font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                    Saved {smartRec.estimated_travel_saved || '22 mins'}
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed mb-3">
                  {smartRec.reasoning || 'Reordering indoor attractions to earlier hours avoids heavy rain while preserving scenic views.'}
                </p>

                <div className="space-y-1.5 border-t border-slate-700/60 pt-3 text-xs">
                  <span className="text-slate-300 font-bold block mb-1">Suggested Schedule Re-alignment:</span>
                  {(smartRec.suggested_changes || [
                    'Move Museum to Morning (09:45 AM)',
                    'Move Cliff Walk to Evening (05:00 PM)',
                    'Lunch at Café Del Mar remains unchanged'
                  ]).map((change, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-slate-300 font-medium">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{change}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reserved AI Module Modular Swap Notice */}
              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-purple-950/30 via-indigo-950/30 to-purple-950/30 border border-purple-500/30 text-xs">
                <div className="flex items-center gap-2 font-bold text-purple-300 mb-1">
                  <IconSparkles className="w-4 h-4 text-purple-400" />
                  <span>Modular AI Engine Ready</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Architecture decoupled: <code className="text-purple-300">RuleRecommendationService</code> will seamlessly swap with <code className="text-purple-300">AIRecommendationService</code> in Phase 2 for live crowd predictions and LLM itinerary optimization.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
