import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function MapUpdater({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 12);
    }
  }, [center, map]);
  return null;
}

export default function MapComponent({ destination, pois = [] }) {
  const [center, setCenter] = useState([51.505, -0.09]); // Default to London
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCoords = async () => {
      if (!destination) return;
      try {
        setLoading(true);
        // Simple Nominatim geocoding (OpenStreetMap)
        const q = encodeURIComponent(destination.split(',')[0]);
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${q}&limit=1`);
        const data = await res.json();
        if (data && data.length > 0) {
          setCenter([parseFloat(data[0].lat), parseFloat(data[0].lon)]);
        }
      } catch (err) {
        console.error("Geocoding error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCoords();
  }, [destination]);

  return (
    <div style={{ height: '400px', width: '100%', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(255,255,255,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontWeight: 600, color: '#185FA5' }}>Loading map...</span>
        </div>
      )}
      <MapContainer center={center} zoom={12} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={center} />
        
        {/* Main Destination Marker */}
        {!loading && (
          <Marker position={center}>
            <Popup>
              <strong>{destination}</strong>
            </Popup>
          </Marker>
        )}

        {/* POI Markers (if any with coordinates) */}
        {pois.map((poi, idx) => {
          if (poi.lat && poi.lon) {
            return (
              <Marker key={idx} position={[poi.lat, poi.lon]}>
                <Popup>
                  <strong>{poi.name}</strong><br/>
                  {poi.description}
                </Popup>
              </Marker>
            );
          }
          return null;
        })}
      </MapContainer>
    </div>
  );
}
