import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  IconCalendar, IconMapPin, IconHeart, IconHeartFilled,
  IconArchive, IconCopy, IconTrash, IconChevronRight,
  IconWallet, IconWalk, IconChecklist, IconBook, IconMap, IconSparkles
} from '@tabler/icons-react';
import TripStatusBadge from './TripStatusBadge';
import { formatCurrency, formatTripDate } from '../../utils/formatters';
import { touchTrip } from '../../api/trips';

const DEFAULT_FALLBACK_IMG = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1000&q=80';

const TripCard = React.memo(({ trip, onFavorite, onArchive, onDuplicate, onDelete }) => {
  const navigate = useNavigate();

  const initialImg = trip?.cover_image || trip?.image_url || DEFAULT_FALLBACK_IMG;
  const [imgSrc, setImgSrc] = useState(initialImg);
  const [imgLoaded, setImgLoaded] = useState(false);

  useEffect(() => {
    const nextImg = trip?.cover_image || trip?.image_url || DEFAULT_FALLBACK_IMG;
    setImgSrc(nextImg);
    setImgLoaded(false);
  }, [trip?.id, trip?.cover_image, trip?.image_url]);

  if (!trip) return null;

  const handleHover = () => {
    try {
      touchTrip(trip.id);
    } catch (_) {}
  };

  const isCompleted = trip.trip_status === 'Completed' || trip.status === 'Completed';
  const isActive = trip.trip_status === 'Active' || trip.status === 'Active' || trip.status === 'In Progress';
  const isUpcoming = trip.trip_status === 'Upcoming' || trip.status === 'Upcoming';

  const currCode = trip.currency || 'USD';
  const budgetSpent = trip.budget_spent ?? 0;
  const budgetTotal = trip.budget ?? 0;
  const budgetUsagePct = trip.budget_usage_percentage ?? (budgetTotal > 0 ? (budgetSpent / budgetTotal) * 100 : 0);
  const budgetHealth = trip.budget_health || (budgetUsagePct > 100 ? 'Exceeded' : budgetUsagePct >= 80 ? 'Warning' : 'Healthy');

  const healthBarColor = budgetHealth === 'Exceeded' ? 'bg-red-500' : budgetHealth === 'Warning' ? 'bg-amber-500' : 'bg-emerald-500';
  const healthTextColor = budgetHealth === 'Exceeded' ? 'text-red-500 dark:text-red-400' : budgetHealth === 'Warning' ? 'text-amber-500 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400';

  const calculateTripDuration = (start, end) => {
    if (!start || !end) return 1;
    const st = new Date(start);
    const en = new Date(end);
    if (isNaN(st) || isNaN(en)) return 1;
    const diffTime = Math.abs(en - st);
    return Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1);
  };
  
  const computedDuration = trip.start_date && trip.end_date 
    ? calculateTripDuration(trip.start_date, trip.end_date)
    : (trip.duration_days || trip.number_of_days || 1);

  const totalActs = trip.activities_total ?? 0;
  const quick = trip.quick_insights || {
    activities: totalActs,
    attractions: totalActs,
    walking_distance: totalActs > 0 ? `${(totalActs * 0.8).toFixed(1)} km` : '0 km',
    travel_time: totalActs > 0 ? `${Math.max(1, Math.floor((totalActs * 30) / 60))}h ${(totalActs * 30) % 60}m` : '0m'
  };

  return (
    <div
      onMouseEnter={handleHover}
      data-trip-card="true"
      className="travel-card travel-card-hover flex flex-col justify-between overflow-hidden group rounded-3xl border border-[var(--border-color)] transition-all duration-200"
    >
      {/* Cover Image Banner (Compact h-32 sm:h-36 ~140px) */}
      <div className="h-32 sm:h-36 w-full relative overflow-hidden bg-slate-800 shrink-0">
        {!imgLoaded && (
          <div className="absolute inset-0 bg-slate-800 animate-pulse flex items-center justify-center">
            <span className="text-[10px] text-[var(--text-muted)] font-semibold">Loading photo...</span>
          </div>
        )}

        <img
          key={`${trip.id}-${imgSrc}`}
          src={imgSrc}
          alt={trip.destination}
          loading="lazy"
          onLoad={() => setImgLoaded(true)}
          onError={(e) => {
            e.currentTarget.src = DEFAULT_FALLBACK_IMG;
            setImgSrc(DEFAULT_FALLBACK_IMG);
          }}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

        {/* Status Badges */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5 flex-wrap z-10">
          <TripStatusBadge status={trip.trip_status || trip.status} />
          {trip.countdown_days > 0 && isUpcoming && (
            <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-blue-900/80 text-blue-200 border border-blue-400/30 backdrop-blur-md">
              Starts in {trip.countdown_days}d
            </span>
          )}
          {isActive && (
            <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-emerald-900/80 text-emerald-200 border border-emerald-400/30 backdrop-blur-md">
              Day {trip.current_trip_day || 1} of {computedDuration}
            </span>
          )}
        </div>

        {/* Favorite Button */}
        <div className="absolute top-2 right-2 z-10">
          <button
            onClick={(e) => { e.stopPropagation(); onFavorite && onFavorite(trip.id); }}
            className="p-1 rounded-full bg-black/50 text-red-500 hover:scale-110 transition-transform backdrop-blur-md border border-white/10"
          >
            {trip.is_favorite ? <IconHeartFilled size={13} /> : <IconHeart size={13} />}
          </button>
        </div>

        {/* Cover Title Info */}
        <div className="absolute bottom-2 left-2.5 right-2.5 text-white z-10">
          <div className="flex items-center justify-between gap-1.5">
            <h3 className="text-sm font-extrabold font-heading tracking-tight drop-shadow-md text-white truncate">
              {trip.title || trip.destination}
            </h3>
            {trip.travel_style && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-white/20 backdrop-blur-md text-white border border-white/20 shrink-0">
                {trip.travel_style}
              </span>
            )}
          </div>
          <div className="flex items-center justify-between text-[10px] text-gray-200 mt-0.5">
            <span className="flex items-center gap-1 font-medium truncate">
              <IconMapPin size={11} className="text-blue-300 shrink-0" />
              {trip.destination}{trip.country ? `, ${trip.country}` : ''}
            </span>
            <span className="flex items-center gap-1 text-gray-300 font-medium shrink-0">
              <IconCalendar size={11} className="text-indigo-300" />
              {formatTripDate(trip.start_date, 'short')} • {computedDuration}d
            </span>
          </div>
        </div>
      </div>

      {/* Card Content Body (Compact ~120px) */}
      <div className="p-3 flex-1 flex flex-col justify-between gap-2.5">
        {/* Progress & Budget Summary Row */}
        <div className="grid grid-cols-2 gap-2 text-[10px] p-2 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)]">
          <div>
            <div className="flex justify-between text-[var(--text-muted)] font-semibold mb-0.5">
              <span>Progress</span>
              <span className="text-[var(--text-primary)] font-extrabold">{trip.trip_progress || 0}%</span>
            </div>
            <div className="w-full h-1 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-300"
                style={{ width: `${trip.trip_progress || 0}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-[var(--text-muted)] font-semibold mb-0.5">
              <span>Spent</span>
              <span className={`font-extrabold ${healthTextColor}`}>{formatCurrency(budgetSpent, currCode)}</span>
            </div>
            <div className="w-full h-1 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${healthBarColor} transition-all duration-300`}
                style={{ width: `${Math.min(100, budgetUsagePct)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Quick Insights Row */}
        <div className="flex items-center justify-between text-[10px] font-semibold text-[var(--text-secondary)] px-2 py-1 rounded-md bg-[var(--bg-app)]/50 border border-[var(--border-color)]">
          <div className="flex items-center gap-1 truncate">
            <IconWalk size={12} className="text-cyan-500 shrink-0" />
            <span className="truncate">Walk: {totalActs > 0 ? (quick.walking_distance || `${(totalActs * 0.8).toFixed(1)} km`) : '0 km'}</span>
          </div>
          <div className="flex items-center gap-1 truncate">
            <IconChecklist size={12} className="text-purple-500 shrink-0" />
            <span className="truncate">{quick.attractions || trip.activities_total || 0} Attractions</span>
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="pt-1.5 border-t border-[var(--border-color)] flex items-center justify-between gap-1">
          {/* Secondary Compact Icon Actions */}
          <div className="flex items-center gap-0.5">
            <Link
              to={`/expenses/${trip.id}`}
              title="Manage Expenses"
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 transition-colors"
            >
              <IconWallet size={14} />
            </Link>
            <Link
              to={`/journal?trip_id=${trip.id}`}
              title="Trip Journal"
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 transition-colors"
            >
              <IconBook size={14} />
            </Link>
            <button
              onClick={() => window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(trip.destination)}`, '_blank')}
              title="Open Maps"
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-purple-500/10 text-purple-600 dark:text-purple-400 transition-colors"
            >
              <IconMap size={14} />
            </button>
            <button
              onClick={() => onDuplicate && onDuplicate(trip.id)}
              title="Duplicate Trip"
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-blue-500/10 text-[var(--text-secondary)] transition-colors"
            >
              <IconCopy size={14} />
            </button>
            <button
              onClick={() => onArchive && onArchive(trip.id)}
              title={trip.is_archived ? 'Restore' : 'Archive'}
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-amber-500/10 text-[var(--text-secondary)] transition-colors"
            >
              <IconArchive size={14} />
            </button>
            <button
              onClick={() => onDelete && onDelete(trip.id)}
              title="Delete Trip"
              className="p-1 rounded-md bg-[var(--bg-app)] hover:bg-red-500/10 text-[var(--text-secondary)] hover:text-red-500 transition-colors"
            >
              <IconTrash size={14} />
            </button>
          </div>

          {/* Primary Action Button */}
          <button
            onClick={() => navigate(`/trips/${trip.id}`, { state: { initialTrip: trip } })}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-extrabold transition-all shadow-sm shrink-0 ${
              isActive
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20'
                : 'bg-[var(--color-primary-600)] hover:bg-blue-700 text-white shadow-blue-500/20'
            }`}
          >
            {isActive ? 'Resume' : 'View'} <IconChevronRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
});

export default TripCard;
