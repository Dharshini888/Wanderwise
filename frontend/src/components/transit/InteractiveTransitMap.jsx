import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Inline SVG pin marker generator to prevent Edge tracking warnings
const createPinIcon = (color = '#7c3aed') => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="28" height="28" style="filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.4));"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>`;
  return L.divIcon({
    className: 'custom-pin-icon',
    html: svg,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  });
};

const defaultPinIcon = createPinIcon('#7c3aed');

function MapUpdater({ bounds, center }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, 6);
    }
  }, [bounds, center, map]);
  return null;
}

export default function InteractiveTransitMap({ origin, destination, markers = [], routeLine = null }) {
  const defaultCenter = [20, 78]; // Default India center

  return (
    <div style={{ height: '400px', width: '100%', borderRadius: '16px', overflow: 'hidden', border: '1px solid rgba(167,139,250,0.3)' }}>
      <MapContainer center={defaultCenter} zoom={5} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {routeLine && (
          <Polyline positions={routeLine} color="#7c3aed" weight={4} opacity={0.8} dashArray="10, 10" />
        )}

        {markers.map((marker, idx) => (
          <Marker key={idx} position={marker.pos} icon={defaultPinIcon}>
            <Popup>{marker.label}</Popup>
          </Marker>
        ))}

        {routeLine && routeLine.length > 0 && (
          <MapUpdater bounds={L.latLngBounds(routeLine)} />
        )}
      </MapContainer>
    </div>
  );
}
