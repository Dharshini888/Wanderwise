import React from 'react';
import PlaceCard from './PlaceCard';
import { IconMapPin, IconCompass } from '@tabler/icons-react';

export default function NearbyPlaces({
  places = [],
  loading = false,
  onViewDetails,
  onAddToItinerary,
  onSaveWishlist,
  savedMap = {},
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <div
            key={n}
            className="p-5 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] animate-pulse space-y-3"
          >
            <div className="h-4 bg-[var(--bg-subtle)] rounded w-3/4" />
            <div className="h-3 bg-[var(--bg-subtle)] rounded w-1/2" />
            <div className="h-3 bg-[var(--bg-subtle)] rounded w-full" />
            <div className="h-8 bg-[var(--bg-subtle)] rounded-xl mt-4" />
          </div>
        ))}
      </div>
    );
  }

  if (places.length === 0) {
    return (
      <div className="p-8 text-center bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] space-y-3">
        <IconCompass size={36} className="mx-auto text-[var(--text-muted)] opacity-50" />
        <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">No places found</h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-sm mx-auto leading-relaxed">
          No matching places were returned by the configured provider for this category. Try selecting another category or expanding your search.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {places.map((place) => (
        <PlaceCard
          key={place.id}
          place={place}
          onViewDetails={onViewDetails}
          onAddToItinerary={onAddToItinerary}
          onSaveWishlist={onSaveWishlist}
          isSaved={!!savedMap[place.id]}
        />
      ))}
    </div>
  );
}
