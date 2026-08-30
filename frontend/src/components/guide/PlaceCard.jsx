import React, { useState } from 'react';
import VerificationBadge from '../ui/VerificationBadge';
import {
  IconMapPin,
  IconClock,
  IconPhone,
  IconGlobe,
  IconHeart,
  IconHeartFilled,
  IconPlus,
  IconBuildingMonument,
  IconChefHat,
  IconCoffee,
  IconHotelService,
  IconBus,
  IconBuildingHospital,
  IconPill,
  IconShoppingBag,
  IconCreditCard,
  IconShield,
} from '@tabler/icons-react';

const CATEGORY_ICONS = {
  ATTRACTIONS: IconBuildingMonument,
  RESTAURANTS: IconChefHat,
  CAFES: IconCoffee,
  HOTELS: IconHotelService,
  TRANSPORT: IconBus,
  HOSPITALS: IconBuildingHospital,
  PHARMACIES: IconPill,
  SHOPPING: IconShoppingBag,
  ATMS: IconCreditCard,
  EMERGENCY: IconShield,
};

export default function PlaceCard({ place, onViewDetails, onAddToItinerary, onSaveWishlist, isSaved }) {
  const [saved, setSaved] = useState(isSaved || false);
  const [saving, setSaving] = useState(false);

  const CatIcon = CATEGORY_ICONS[place.category] || IconBuildingMonument;

  const handleWishlistToggle = async (e) => {
    e.stopPropagation();
    if (saved) return; // already saved
    setSaving(true);
    try {
      if (onSaveWishlist) {
        await onSaveWishlist(place);
      }
      setSaved(true);
    } catch (err) {
      console.error('[PlaceCard] Wishlist error:', err);
    } finally {
      setSaving(false);
    }
  };

  const formattedDistance =
    place.distance_m !== undefined && place.distance_m !== null
      ? place.distance_m >= 1000
        ? `${(place.distance_m / 1000).toFixed(1)} km away`
        : `${place.distance_m} m away`
      : place.distance_km !== undefined
      ? `${place.distance_km} km away`
      : null;

  return (
    <div
      onClick={() => onViewDetails && onViewDetails(place)}
      className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-blue-500/40 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between gap-4 cursor-pointer group"
    >
      <div className="space-y-3">
        {/* HEADER: Icon, Name & Category */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 shrink-0 group-hover:scale-105 transition-transform">
              <CatIcon size={20} />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading tracking-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
                {place.name}
              </h3>
              <span className="text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider block mt-0.5">
                {place.category}
              </span>
            </div>
          </div>

          <button
            onClick={handleWishlistToggle}
            disabled={saving}
            className={`p-2 rounded-xl transition-all cursor-pointer border shrink-0 ${
              saved
                ? 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                : 'bg-[var(--bg-subtle)] text-[var(--text-muted)] hover:text-rose-500 border-[var(--border-color)] hover:border-rose-500/30'
            }`}
            title={saved ? 'Saved to Wishlist' : 'Save to Wishlist'}
          >
            {saved ? <IconHeartFilled size={18} /> : <IconHeart size={18} />}
          </button>
        </div>

        {/* DETAILS LIST */}
        <div className="space-y-1.5 text-xs text-[var(--text-secondary)] font-medium">
          {formattedDistance && (
            <div className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-bold">
              <IconMapPin size={14} className="shrink-0" />
              <span>{formattedDistance}</span>
            </div>
          )}

          <div className="flex items-start gap-1.5">
            <span className="text-[var(--text-muted)] shrink-0">📌</span>
            <span className="truncate">{place.address || 'Provider supplied address'}</span>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)] pt-1">
            <span className="flex items-center gap-1">
              <IconClock size={13} />
              <span>{place.opening_hours || 'Hours: Unavailable'}</span>
            </span>

            {place.rating !== null && place.rating !== undefined ? (
              <span className="font-bold text-amber-500">★ {place.rating}</span>
            ) : (
              <span>Rating: Unavailable</span>
            )}
          </div>
        </div>
      </div>

      {/* FOOTER: Truth-First Verification Badge & Actions */}
      <div className="pt-3 border-t border-[var(--border-color)] flex items-center justify-between gap-2 flex-wrap">
        <VerificationBadge status={place.verification_status || 'Provider Verified'} size="xs" />

        <div className="flex items-center gap-1.5">
          {onAddToItinerary && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddToItinerary(place);
              }}
              className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 transition-all flex items-center gap-1 cursor-pointer"
            >
              <IconPlus size={12} />
              <span>Itinerary</span>
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              if (onViewDetails) onViewDetails(place);
            }}
            className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-[var(--text-primary)] bg-[var(--bg-subtle)] hover:bg-[var(--bg-panel)] border border-[var(--border-color)] transition-all cursor-pointer"
          >
            Details
          </button>
        </div>
      </div>
    </div>
  );
}
