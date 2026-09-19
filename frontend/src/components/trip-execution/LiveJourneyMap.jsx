import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Inline SVG pin marker generator to prevent Edge tracking warnings
const createPinIcon = (color) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="28" height="28" style="filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.4));"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>`;
  return L.divIcon({
    className: 'custom-pin-icon',
    html: svg,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  });
};

const createDotIcon = (color) => {
  return L.divIcon({
    className: 'custom-dot-marker',
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
  });
};

const completedIcon = createDotIcon('#22c55e'); // Green
const currentIcon = createPinIcon('#a855f7'); // Purple
const upcomingIcon = createDotIcon('#64748b'); // Slate

function MapUpdater({ bounds, center }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, 12);
    }
  }, [bounds, center, map]);
  return null;
}

const poiIcon = createDotIcon('#ef4444'); // Red for POIs/Hospitals

export default function LiveJourneyMap({ markers = [], routeLine = null, nearbyPois = [] }) {
  const firstPos = markers[0]?.pos || [11.0168, 76.9558];
  
  const getIconForStatus = (status) => {
    if (status === 'completed') return completedIcon;
    if (status === 'current') return currentIcon;
    if (status === 'poi') return poiIcon;
    return upcomingIcon;
  };

  const allPoints = [
    ...(routeLine || []),
    ...markers.map(m => m.pos),
    ...nearbyPois.filter(p => p.lat && p.lon).map(p => [p.lat, p.lon])
  ];

  return (
    <div className="h-[320px] w-full rounded-2xl overflow-hidden border border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.15)] mb-6">
      <MapContainer center={firstPos} zoom={10} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {routeLine && routeLine.length > 0 && (
          <Polyline positions={routeLine} color="#a855f7" weight={4} opacity={0.8} />
        )}

        {markers.map((marker, idx) => (
          <Marker key={idx} position={marker.pos} icon={getIconForStatus(marker.status)}>
            <Popup><span className="font-bold">{marker.label}</span></Popup>
          </Marker>
        ))}

        {nearbyPois.map((poi, idx) => (
          poi.lat && poi.lon && (
            <Marker key={`poi-${idx}`} position={[poi.lat, poi.lon]} icon={poiIcon}>
              <Popup>
                <div>
                  <div className="font-bold text-xs">{poi.name}</div>
                  <div className="text-[10px] text-gray-600">{poi.type} • {poi.distance_km} km</div>
                </div>
              </Popup>
            </Marker>
          )
        ))}

        {allPoints.length > 0 && (
          <MapUpdater bounds={L.latLngBounds(allPoints)} />
        )}
      </MapContainer>
    </div>
  );
}
