import React from 'react';
import { Link } from 'react-router-dom';
import {
  IconMapPin, IconCalendar, IconUsers, IconWallet,
  IconSparkles, IconClock, IconPlus, IconCompass
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';
import { formatLocalDate, calculateTripDuration } from '../../utils/date_helpers';

const FALLBACK_HERO_IMAGES = {
  tokyo: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1400&q=80',
  kyoto: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1400&q=80',
  paris: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1400&q=80',
  rome: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1400&q=80',
  london: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1400&q=80',
  istanbul: 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1400&q=80',
  bali: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1400&q=80',
  singapore: 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=1400&q=80',
  dubai: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1400&q=80',
  cairo: 'https://images.unsplash.com/photo-1572252009286-268acec5ca0a?auto=format&fit=crop&w=1400&q=80',
  queenstown: 'https://images.unsplash.com/photo-1589802829985-817e51171b92?auto=format&fit=crop&w=1400&q=80',
  default: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1400&q=80'
};

function getHeroImage(trip) {
  if (trip?.image_url && typeof trip.image_url === 'string' && trip.image_url.startsWith('http')) {
    return trip.image_url;
  }
  if (trip?.cover_image && typeof trip.cover_image === 'string' && trip.cover_image.startsWith('http')) {
    return trip.cover_image;
  }
  const destKey = (trip?.destination || '').toLowerCase().replace(/[^a-z]/g, '');
  for (const [key, url] of Object.entries(FALLBACK_HERO_IMAGES)) {
    if (destKey.includes(key)) return url;
  }
  return FALLBACK_HERO_IMAGES.default;
}

export default function HeroTripBanner({ trip, statusInfo, onPlanTrip }) {
  if (!trip) {
    return (
      <div className="relative overflow-hidden rounded-3xl border border-[var(--border-color)] bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 p-8 shadow-xl text-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/30 mb-3">
              <IconCompass size={14} className="animate-spin" />
              <span>AI Travel Command Center</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black font-heading tracking-tight text-white">
              Ready for your next journey?
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-xl">
              Create a personalized, tempo-aware travel itinerary with verified attractions, door-to-door transit assistance, and canonical budget allocation in seconds.
            </p>
          </div>
          <button
            onClick={onPlanTrip}
            className="btn-primary flex items-center gap-2 px-6 py-3 text-xs font-bold shrink-0 cursor-pointer shadow-lg shadow-blue-500/20"
          >
            <IconPlus size={16} />
            <span>Plan My Trip</span>
          </button>
        </div>
      </div>
    );
  }

  const duration = calculateTripDuration(trip.start_date, trip.end_date);
  const startFormatted = formatLocalDate(trip.start_date, { day: 'numeric', month: 'short', year: 'numeric' });
  const endFormatted = formatLocalDate(trip.end_date, { day: 'numeric', month: 'short', year: 'numeric' });
  const formattedBudget = formatCurrency(trip.budget || 0, trip.currency || 'USD');
  const heroImage = getHeroImage(trip);

  const travelersCount = trip.group_size || 1;
  const adults = trip.adults || travelersCount;
  const children = trip.children || 0;
  const travelersLabel = children > 0
    ? `${adults} Adult${adults > 1 ? 's' : ''}, ${children} Child${children > 1 ? 'ren' : ''}`
    : `${travelersCount} Traveler${travelersCount > 1 ? 's' : ''}`;

  const isOngoing = statusInfo?.status === 'Ongoing';
  const isUpcoming = statusInfo?.status === 'Upcoming';
  const isCompleted = statusInfo?.status === 'Completed';

  const badgeTitle = isOngoing
    ? 'Ongoing Trip • Live'
    : isUpcoming
    ? 'Next Upcoming Adventure'
    : 'Recent Completed Adventure';

  const progressLabel = isOngoing
    ? `${statusInfo.text} (${statusInfo.progressPct}%)`
    : isUpcoming
    ? `0% Complete • ${statusInfo.text}`
    : '100% Completed';

  return (
    <div className="relative overflow-hidden rounded-3xl border border-[var(--border-color)] shadow-2xl bg-slate-950 text-white min-h-[220px] flex flex-col justify-between">
      {/* Background Image Layer with Vignette & Gradients */}
      <div className="absolute inset-0 z-0">
        <img
          src={heroImage}
          alt={trip.destination}
          className="w-full h-full object-cover opacity-35 filter brightness-90 transition-transform duration-700 hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-slate-950/40" />
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/70 to-transparent" />
      </div>

      {/* Hero Content Layer */}
      <div className="relative z-10 p-6 md:p-8 flex flex-col justify-between flex-1 gap-6">
        {/* Top Header Row: Status Badge & Trip Type */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className={`inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-3.5 py-1.5 rounded-full shadow-md backdrop-blur-md ${statusInfo?.badgeClass || 'bg-blue-500/20 text-blue-300'}`}>
              <span className={`w-2 h-2 rounded-full ${statusInfo?.dotColor || 'bg-blue-400'}`} />
              <span>{badgeTitle}</span>
            </span>

            {trip.travel_style && (
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/80 backdrop-blur-sm">
                {trip.travel_style}
              </span>
            )}
          </div>

          {/* Quick Countdown / Elapsed Pill */}
          <div className="bg-slate-900/90 border border-slate-700/90 px-3.5 py-1 rounded-xl backdrop-blur-md text-xs font-mono font-bold text-slate-200 flex items-center gap-2">
            <IconClock size={14} className="text-blue-400" />
            <span>{statusInfo?.text}</span>
          </div>
        </div>

        {/* Middle Main Content: Destination Title & Metadata Chips */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <h2 className="text-2xl sm:text-4xl font-black font-heading tracking-tight text-white flex items-center gap-2.5 drop-shadow-md">
              <IconMapPin size={28} className="text-blue-400 shrink-0" />
              <span>{trip.destination}</span>
              {trip.country && (
                <span className="text-sm sm:text-base font-semibold text-slate-400 font-sans">
                  ({trip.country})
                </span>
              )}
            </h2>

            {/* Travel Specs Ribbon */}
            <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs font-medium text-slate-300 pt-1">
              <div className="flex items-center gap-1.5 bg-slate-900/70 border border-slate-800/80 px-2.5 py-1 rounded-lg">
                <IconCalendar size={14} className="text-blue-400" />
                <span>{startFormatted} → {endFormatted} ({duration} Days)</span>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-900/70 border border-slate-800/80 px-2.5 py-1 rounded-lg">
                <IconUsers size={14} className="text-emerald-400" />
                <span>{travelersLabel}</span>
              </div>

              <div className="flex items-center gap-1.5 bg-slate-900/70 border border-slate-800/80 px-2.5 py-1 rounded-lg">
                <IconWallet size={14} className="text-amber-400" />
                <span>Budget: <strong className="text-white font-mono">{formattedBudget}</strong></span>
              </div>
            </div>
          </div>

          {/* Primary View Trip Action Button */}
          <div className="shrink-0">
            <Link
              to={`/trips/${trip.id}`}
              state={{ initialTrip: trip }}
              className="btn-primary inline-flex items-center gap-2 px-6 py-3 text-xs font-extrabold uppercase tracking-wider rounded-xl shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all cursor-pointer"
            >
              <IconSparkles size={16} />
              <span>View Itinerary</span>
            </Link>
          </div>
        </div>

        {/* Bottom Progress Bar Strip */}
        <div className="pt-4 border-t border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400">
            <span>Trip Timeline Progress</span>
            <span className="text-blue-300 font-mono">{progressLabel}</span>
          </div>
          <div className="w-full bg-slate-800/80 h-2 rounded-full overflow-hidden border border-slate-700/50">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                isCompleted
                  ? 'bg-emerald-500'
                  : isOngoing
                  ? 'bg-gradient-to-r from-amber-500 via-teal-400 to-blue-500'
                  : 'bg-blue-500'
              }`}
              style={{ width: `${statusInfo?.progressPct || 0}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

