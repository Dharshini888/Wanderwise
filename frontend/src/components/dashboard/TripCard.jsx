import { useState } from 'react';
import { Link } from 'react-router-dom';
import { IconTrash, IconChevronRight, IconWallet, IconCalendar, IconMapPin } from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';
import { formatLocalDate, calculateTripDuration, getTripStatusInfo } from '../../utils/date_helpers';

const FALLBACK_DESTINATION_IMAGES = {
  tokyo: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80',
  kyoto: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=800&q=80',
  paris: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80',
  rome: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80',
  london: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80',
  istanbul: 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=80',
  bali: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=800&q=80',
  singapore: 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=800&q=80',
  dubai: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=800&q=80',
  newyork: 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=800&q=80',
  queenstown: 'https://images.unsplash.com/photo-1589802829985-817e51171b92?auto=format&fit=crop&w=800&q=80',
  cairo: 'https://images.unsplash.com/photo-1572252009286-268acec5ca0a?auto=format&fit=crop&w=800&q=80',
  jaipur: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=800&q=80',
  default: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80'
};

function getTripImage(trip) {
  if (trip.image_url && typeof trip.image_url === 'string' && trip.image_url.startsWith('http')) {
    return trip.image_url;
  }
  if (trip.cover_image && typeof trip.cover_image === 'string' && trip.cover_image.startsWith('http')) {
    return trip.cover_image;
  }
  const destKey = (trip.destination || '').toLowerCase().replace(/[^a-z]/g, '');
  for (const [key, url] of Object.entries(FALLBACK_DESTINATION_IMAGES)) {
    if (destKey.includes(key)) return url;
  }
  return FALLBACK_DESTINATION_IMAGES.default;
}

export default function TripCard({ trip, onDelete }) {
  const [imgSrc, setImgSrc] = useState(() => getTripImage(trip));
  const statusInfo = getTripStatusInfo(trip.start_date, trip.end_date);
  const duration = calculateTripDuration(trip.start_date, trip.end_date);
  const formattedBudget = formatCurrency(trip.budget || 0, trip.currency || 'USD');

  const startFormatted = formatLocalDate(trip.start_date, { day: 'numeric', month: 'short' });
  const endFormatted = formatLocalDate(trip.end_date, { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="travel-card travel-card-hover flex flex-col overflow-hidden group rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] transition-all duration-200">
      {/* Cover Image Header */}
      <div className="h-40 w-full relative overflow-hidden bg-slate-900">
        <img
          src={imgSrc}
          alt={trip.destination}
          onError={() => setImgSrc(FALLBACK_DESTINATION_IMAGES.default)}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/30 to-transparent" />

        {/* Dynamic Status Badge (Top-Right) */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5">
          <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full shadow-sm backdrop-blur-md ${statusInfo.badgeClass}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${statusInfo.dotColor}`} />
            {statusInfo.label}
          </span>
        </div>

        {/* Travel Style Badge (Top-Left) */}
        {trip.travel_style && (
          <div className="absolute top-3 left-3 bg-black/40 backdrop-blur-md text-white/90 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border border-white/10">
            {trip.travel_style}
          </div>
        )}

        {/* Destination & Dates in Bottom Overlay */}
        <div className="absolute bottom-3 left-3.5 right-3.5 text-white">
          <h3 className="text-base font-black tracking-tight font-heading truncate drop-shadow-md flex items-center gap-1.5">
            <IconMapPin size={16} className="text-blue-400 shrink-0" />
            <span className="truncate">{trip.destination}</span>
          </h3>
          <div className="text-[11px] font-medium text-slate-300 flex items-center gap-2 mt-0.5 opacity-90">
            <span>{startFormatted} → {endFormatted}</span>
            <span>•</span>
            <span className="font-semibold text-blue-300">{duration} Days</span>
          </div>
        </div>
      </div>

      {/* Card Content & Footer */}
      <div className="p-4 flex flex-col flex-1 justify-between gap-3 bg-[var(--bg-card)]">
        {/* Status Text & Countdown */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-[11px] font-medium text-[var(--text-muted)] flex items-center gap-1">
            <IconCalendar size={13} className="text-blue-500 shrink-0" />
            <span>{statusInfo.text}</span>
          </span>
          <div className="text-right">
            <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] tracking-wider block">Budget</span>
            <span className="text-xs font-black text-blue-600 dark:text-blue-400 font-mono">
              {formattedBudget}
            </span>
          </div>
        </div>

        {/* Actions Row */}
        <div className="flex items-center justify-between gap-2 pt-2 border-t border-[var(--border-color)]">
          {onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (window.confirm(`Delete itinerary for ${trip.destination}?`)) {
                  onDelete(trip.id);
                }
              }}
              className="p-1.5 text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
              title="Delete Trip"
              aria-label="Delete Trip"
            >
              <IconTrash size={15} />
            </button>
          )}

          <div className="flex items-center gap-2 ml-auto">
            <Link
              to={`/expenses/${trip.id}`}
              className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-colors"
              title="Expenses"
            >
              <IconWallet size={13} />
              <span>Expenses</span>
            </Link>

            <Link
              to={`/trips/${trip.id}`}
              state={{ initialTrip: trip }}
              className="text-[11px] font-bold text-white bg-blue-600 hover:bg-blue-500 px-3 py-1.5 rounded-lg flex items-center gap-1 shadow-sm transition-colors"
            >
              <span>View Details</span>
              <IconChevronRight size={13} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
