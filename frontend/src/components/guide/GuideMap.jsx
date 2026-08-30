import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import VerificationBadge from '../ui/VerificationBadge';

// Fix default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom marker creator
const createMarkerIcon = (color, emoji = '📍') => {
  return L.divIcon({
    className: 'custom-guide-icon',
    html: `<div style="background-color: ${color}; width: 28px; height: 28px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; font-size: 13px;">${emoji}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
};

const destinationIcon = createMarkerIcon('#2563eb', '📍'); // Blue
const poiIcon = createMarkerIcon('#7c3aed', '✨'); // Purple
const routeStartIcon = createMarkerIcon('#059669', '🚶'); // Green
const routeDestIcon = createMarkerIcon('#dc2626', '🏁'); // Red

function MapBoundsUpdater({ center, places, routeGeometry }) {
  const map = useMap();

  useEffect(() => {
    if (routeGeometry && routeGeometry.length > 0) {
      const bounds = L.latLngBounds(routeGeometry);
      map.fitBounds(bounds, { padding: [40, 40] });
    } else if (places && places.length > 0) {
      const coords = places
        .filter((p) => p.latitude && p.longitude)
        .map((p) => [p.latitude, p.longitude]);
      if (center) coords.push(center);
      if (coords.length > 0) {
        const bounds = L.latLngBounds(coords);
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
      }
    } else if (center) {
      map.setView(center, 13);
    }
  }, [center, places, routeGeometry, map]);

  return null;
}

export default function GuideMap({
  centerLat,
  centerLon,
  places = [],
  activePlace = null,
  routeData = null,
  onSelectPlace,
  height = '450px',
}) {
  const center = useMemo(() => [centerLat || 13.0827, centerLon || 80.2707], [centerLat, centerLon]);

  const routePositions = useMemo(() => {
    if (routeData?.geometry && routeData.geometry.length > 0) {
      return routeData.geometry;
    }
    return [];
  }, [routeData]);

  return (
    <div
      className="relative w-full rounded-3xl overflow-hidden border border-[var(--border-color)] shadow-lg z-0"
      style={{ height }}
    >
      <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        <MapBoundsUpdater center={center} places={places} routeGeometry={routePositions} />

        {/* Destination Center Marker */}
        <Marker position={center} icon={destinationIcon}>
          <Popup>
            <div className="p-1 space-y-1">
              <strong className="text-xs text-[var(--text-primary)]">Destination Center</strong>
              <div className="text-[10px] text-[var(--text-muted)] font-mono">
                {center[0].toFixed(4)}, {center[1].toFixed(4)}
              </div>
            </div>
          </Popup>
        </Marker>

        {/* Nearby POI Markers */}
        {places.map((place) => {
          if (!place.latitude || !place.longitude) return null;
          const isSelected = activePlace && activePlace.id === place.id;

          return (
            <Marker
              key={place.id}
              position={[place.latitude, place.longitude]}
              icon={isSelected ? routeDestIcon : poiIcon}
            >
              <Popup>
                <div className="p-1 space-y-1.5 min-w-[160px]">
                  <div className="text-xs font-bold text-[var(--text-primary)]">{place.name}</div>
                  <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
                    {place.category}
                  </div>
                  {place.distance_m && (
                    <div className="text-[11px] font-semibold text-blue-600">
                      {place.distance_m >= 1000
                        ? `${(place.distance_m / 1000).toFixed(1)} km away`
                        : `${place.distance_m} m away`}
                    </div>
                  )}
                  <button
                    onClick={() => onSelectPlace && onSelectPlace(place)}
                    className="w-full mt-1 px-2 py-1 rounded bg-blue-600 text-white text-[10px] font-bold shadow-xs hover:bg-blue-700 cursor-pointer"
                  >
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* OSRM Route Polyline */}
        {routePositions.length > 0 && (
          <Polyline positions={routePositions} pathOptions={{ color: '#2563eb', weight: 5, opacity: 0.9 }} />
        )}
      </MapContainer>

      {/* Floating Truth-First Badge when route is active */}
      {routeData && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-[var(--bg-card)]/95 backdrop-blur-xs px-3.5 py-1.5 rounded-full shadow-lg border border-blue-500/40 z-[1000] flex items-center gap-2">
          <VerificationBadge status={routeData.verification_status || 'Route Calculated'} size="xs" />
          <span className="text-[11px] font-extrabold text-[var(--text-primary)]">
            {routeData.distance_km} km · {routeData.duration_minutes} min
          </span>
        </div>
      )}
    </div>
  );
}
