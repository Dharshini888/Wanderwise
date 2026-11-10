import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import VerificationBadge from '../ui/VerificationBadge';
import { IconMap, IconNavigation, IconExternalLink } from '@tabler/icons-react';

// Fix default icons for Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Numbered Stop Icon Creator
const createNumberedIcon = (number, color = '#2563eb') => {
  return L.divIcon({
    className: 'custom-stop-icon',
    html: `<div style="background-color: ${color}; color: white; width: 26px; height: 26px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 12px; font-family: system-ui, sans-serif;">${number}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

function MapBoundsUpdater({ stops, routeGeometry }) {
  const map = useMap();

  useEffect(() => {
    if (routeGeometry && routeGeometry.length > 0) {
      const bounds = L.latLngBounds(routeGeometry);
      map.fitBounds(bounds, { padding: [35, 35] });
    } else if (stops && stops.length > 0) {
      const coords = stops
        .filter((s) => s.latitude && s.longitude)
        .map((s) => [s.latitude, s.longitude]);
      if (coords.length > 0) {
        const bounds = L.latLngBounds(coords);
        map.fitBounds(bounds, { padding: [35, 35], maxZoom: 14 });
      }
    }
  }, [stops, routeGeometry, map]);

  return null;
}

const CITY_CENTERS = {
  agra: [27.1767, 78.0081],
  tbilisi: [41.6938, 44.8015],
  georgia: [41.6938, 44.8015],
  hanoi: [21.0285, 105.8542],
  florence: [43.7696, 11.2558],
  reykjavik: [64.1466, -21.9426],
  bangkok: [13.7563, 100.5018],
  kuala_lumpur: [3.1390, 101.6869],
  'kuala lumpur': [3.1390, 101.6869],
  coimbatore: [11.0168, 76.9558],
  delhi: [28.6139, 77.2090],
  mumbai: [19.0760, 72.8777],
  bolivia: [-16.5000, -68.1500],
  rome: [41.9028, 12.4964],
  paris: [48.8566, 2.3522],
  london: [51.5074, -0.1278],
  tokyo: [35.6762, 139.6503],
  singapore: [1.3521, 103.8198],
};

export default function TripItineraryMap({
  stops = [],
  routeGeometry = [],
  totalDistanceKm = 0,
  totalDurationMins = 0,
  verificationStatus = 'Route Calculated',
  destination = '',
  onOpenTransit,
  height = '320px',
}) {
  const destLower = (destination || '').toLowerCase();
  const defaultCityCoord = Object.entries(CITY_CENTERS).find(([k]) => destLower.includes(k))?.[1] || [41.6938, 44.8015];

  // Resolve valid stops with coordinates truthfully; never fabricate coordinates with offsets
  const validStops = useMemo(() => {
    return (stops || []).filter((s) => s && s.latitude && s.longitude);
  }, [stops]);

  const center = useMemo(() => {
    if (validStops.length > 0) {
      return [validStops[0].latitude, validStops[0].longitude];
    }
    return defaultCityCoord;
  }, [validStops, defaultCityCoord]);

  // Compute polyline coordinates if routeGeometry is missing
  const polylineCoords = useMemo(() => {
    if (routeGeometry && routeGeometry.length > 0) {
      return routeGeometry;
    }
    return validStops.map((s) => [s.latitude, s.longitude]);
  }, [routeGeometry, validStops]);

  if (validStops.length === 0 && (!stops || stops.length === 0)) {
    return (
      <div className="glass-card p-5 rounded-2xl space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
            <IconMap size={18} className="text-purple-500" />
            Day's Route & Map Preview
          </h3>
          <span className="text-xs text-[var(--text-muted)] font-semibold">
            Overview Ready
          </span>
        </div>
        <div className="h-44 rounded-xl bg-slate-900/80 border border-[var(--border-color)] flex flex-col items-center justify-center text-center p-4">
          <IconNavigation size={28} className="text-purple-400 mb-2" />
          <p className="text-xs font-bold text-[var(--text-primary)]">Interactive Map Ready</p>
          <p className="text-[11px] text-[var(--text-muted)] mt-1 max-w-sm mb-3">
            Select a day from the timeline or workspace to view verified route lines and stops.
          </p>
          {onOpenTransit && (
            <button
              onClick={onOpenTransit}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
            >
              <IconMap size={14} /> Open AI Transit Map
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-5 rounded-2xl space-y-3">
      {/* Header Bar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold font-heading text-[var(--text-primary)] flex items-center gap-2">
            <IconMap size={18} className="text-purple-500" />
            Today's Route & Map Preview
          </h3>
          <VerificationBadge status={verificationStatus} size="xs" />
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--text-muted)] font-semibold">
            {validStops.length} Stops {totalDistanceKm > 0 ? `• ~${totalDistanceKm} km` : ''} {totalDurationMins > 0 ? `• ~${totalDurationMins} mins` : ''}
          </span>
          {onOpenTransit && (
            <button
              onClick={onOpenTransit}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
            >
              <IconMap size={14} /> Transit Assistant
            </button>
          )}
        </div>
      </div>

      {/* Leaflet Map Preview Container */}
      <div
        className="relative w-full rounded-xl overflow-hidden border border-[var(--border-color)] shadow-inner z-0"
        style={{ height }}
      >
        <MapContainer
          center={center}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapBoundsUpdater stops={validStops} routeGeometry={polylineCoords} />

          {/* Numbered Stop Markers */}
          {validStops.map((stop, idx) => (
            <Marker
              key={stop.id || idx}
              position={[stop.latitude, stop.longitude]}
              icon={createNumberedIcon(idx + 1, idx === 0 ? '#059669' : idx === validStops.length - 1 ? '#dc2626' : '#2563eb')}
            >
              <Popup>
                <div className="p-1 space-y-1 min-w-[150px]">
                  <div className="text-[10px] font-extrabold text-blue-600 uppercase tracking-wider">
                    Stop #{idx + 1}
                  </div>
                  <div className="text-xs font-bold text-[var(--text-primary)]">
                    {stop.place_name || stop.title}
                  </div>
                  {stop.address && (
                    <div className="text-[10px] text-[var(--text-muted)] line-clamp-2">
                      📍 {stop.address}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Route Line Polyline */}
          {polylineCoords.length > 1 && (
            <Polyline
              positions={polylineCoords}
              pathOptions={{ color: '#2563eb', weight: 4.5, opacity: 0.85, dashArray: '8, 8' }}
            />
          )}
        </MapContainer>

        {/* Floating Route Info Badge */}
        <div className="absolute bottom-3 left-3 bg-[var(--bg-card)]/95 backdrop-blur-xs px-3 py-1.5 rounded-xl shadow-md border border-[var(--border-color)] z-[1000] flex items-center gap-2 text-xs font-bold text-[var(--text-primary)]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span>{validStops.length} Geocoded Stops Connected</span>
        </div>
      </div>
    </div>
  );
}
