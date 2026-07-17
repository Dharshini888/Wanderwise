import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix leaflet marker icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const API = 'http://localhost:8000/api';

// Component to dynamically update map bounds
function MapUpdater({ bounds, center }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (center) {
      map.setView(center, 13);
    }
  }, [bounds, center, map]);
  return null;
}

const TYPE_ICONS = { walk: '🚶', bus: '🚌', metro: '🚇', train: '🚆', auto: '🛺', taxi: '🚕' };

export default function Transit() {
  const [form, setForm] = useState({ from_location: '', to_location: '', city: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapCenter, setMapCenter] = useState([51.505, -0.09]); // Default to London
  const [routeLine, setRouteLine] = useState(null);
  const [mapBounds, setMapBounds] = useState(null);
  const [markers, setMarkers] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setResult(null); setRouteLine(null); setMapBounds(null); setMarkers([]);
    const token = localStorage.getItem('token');
    
    try {
      // 1. Fetch AI step-by-step guidance from backend
      const res = await fetch(`${API}/transit/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok) setResult(data);
      else throw new Error(data.detail || 'Failed to get transit info');

      // 2. Fetch coordinates for map routing
      const qFrom = encodeURIComponent(`${form.from_location}, ${form.city}`);
      const qTo = encodeURIComponent(`${form.to_location}, ${form.city}`);
      
      const [resFrom, resTo] = await Promise.all([
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${qFrom}&limit=1`).then(r => r.json()),
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${qTo}&limit=1`).then(r => r.json())
      ]);

      if (resFrom[0] && resTo[0]) {
        const fromLat = parseFloat(resFrom[0].lat);
        const fromLon = parseFloat(resFrom[0].lon);
        const toLat = parseFloat(resTo[0].lat);
        const toLon = parseFloat(resTo[0].lon);
        
        setMarkers([
          { pos: [fromLat, fromLon], label: 'Start: ' + form.from_location },
          { pos: [toLat, toLon], label: 'End: ' + form.to_location }
        ]);

        // 3. Fetch OSRM route geometry
        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${fromLon},${fromLat};${toLon},${toLat}?overview=full&geometries=geojson`;
        const osrmRes = await fetch(osrmUrl).then(r => r.json());
        
        if (osrmRes.code === 'Ok' && osrmRes.routes.length > 0) {
          // OSRM returns [lon, lat], leaflet needs [lat, lon]
          const coords = osrmRes.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
          setRouteLine(coords);
          
          // Calculate bounding box
          const lats = coords.map(c => c[0]);
          const lons = coords.map(c => c[1]);
          setMapBounds([
            [Math.min(...lats), Math.min(...lons)],
            [Math.max(...lats), Math.max(...lons)]
          ]);
        } else {
          // Just center on the two points if no route found
          setMapBounds([ [fromLat, fromLon], [toLat, toLon] ]);
        }
      } else {
        // Fallback geocode just the city
        const resCity = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(form.city)}&limit=1`).then(r => r.json());
        if (resCity[0]) setMapCenter([parseFloat(resCity[0].lat), parseFloat(resCity[0].lon)]);
      }

    } catch (err) { setError(err.message || 'Network error'); }
    setLoading(false);
  };

  const inputStyle = { width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '13px', outline: 'none', boxSizing: 'border-box' };
  const labelStyle = { display: 'block', marginBottom: '6px', fontSize: '11px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 3rem)', gap: '1.5rem' }}>
      
      <div>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>📍 Maps & Transit</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Navigate unfamiliar cities with step-by-step guidance.</p>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', flex: 1, overflow: 'hidden' }}>
        
        {/* Sidebar: Search & Route Info */}
        <div style={{ width: '400px', display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '4px' }}>
          
          <form className="glass-card" onSubmit={handleSearch} style={{ padding: '20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={labelStyle}>From Location</label>
                <input style={inputStyle} value={form.from_location} onChange={e => setForm(f => ({ ...f, from_location: e.target.value }))} placeholder="e.g. Hotel Radisson" required />
              </div>
              <div>
                <label style={labelStyle}>To Destination</label>
                <input style={inputStyle} value={form.to_location} onChange={e => setForm(f => ({ ...f, to_location: e.target.value }))} placeholder="e.g. India Gate" required />
              </div>
              <div>
                <label style={labelStyle}>City</label>
                <input style={inputStyle} value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))} placeholder="e.g. New Delhi" required />
              </div>
            </div>
            <button type="submit" disabled={loading}
              style={{ marginTop: '16px', width: '100%', padding: '12px', background: '#185FA5', border: 'none', borderRadius: '8px', color: 'white', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Computing route...' : 'Get Directions'}
            </button>
          </form>

          {error && <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', color: '#dc2626', fontSize: '14px', fontWeight: 500 }}>⚠️ {error}</div>}

          {result && (
            <div className="glass-card" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
              
              <h3 className="text-primary-dark" style={{ margin: '0 0 12px', fontSize: '15px' }}>Route Summary</h3>
              <div style={{ background: 'rgba(24, 95, 165, 0.05)', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                <p className="text-secondary" style={{ margin: '0 0 12px', fontSize: '13px', lineHeight: 1.5 }}>{result.summary}</p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div><div className="label-text">Time</div><div className="text-primary-dark" style={{ fontWeight: 700, fontSize: '14px' }}>{result.total_time}</div></div>
                  <div><div className="label-text">Fare</div><div className="text-primary-dark" style={{ fontWeight: 700, fontSize: '14px' }}>{result.total_fare}</div></div>
                  <div><div className="label-text">Walk</div><div className="text-primary-dark" style={{ fontWeight: 700, fontSize: '14px' }}>{result.walking_distance}</div></div>
                </div>
              </div>

              {result.steps && (
                <>
                  <h3 className="text-primary-dark" style={{ margin: '0 0 12px', fontSize: '15px' }}>Steps</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
                    {result.steps.map((step, i) => (
                      <div key={i} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(24, 95, 165, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', color: '#185FA5' }}>
                            {TYPE_ICONS[step.type] || '📍'}
                          </div>
                          {i < result.steps.length - 1 && <div style={{ width: 2, background: 'rgba(200, 225, 245, 0.9)', flex: 1, minHeight: 30, margin: '4px 0' }} />}
                        </div>
                        <div style={{ flex: 1, paddingBottom: '16px', paddingTop: '4px' }}>
                          <div className="text-primary-dark" style={{ fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>{step.instruction}</div>
                          {step.detail && <div className="text-secondary" style={{ fontSize: '12px', marginBottom: '6px' }}>{step.detail}</div>}
                          <div style={{ display: 'flex', gap: '8px' }}>
                            {step.duration && <span style={{ background: 'rgba(255,255,255,0.8)', border: '1px solid #c8dff0', borderRadius: '12px', padding: '2px 8px', fontSize: '11px', color: '#5a7a9a' }}>⏱️ {step.duration}</span>}
                            {step.fare && <span style={{ background: 'rgba(255,255,255,0.8)', border: '1px solid #c8dff0', borderRadius: '12px', padding: '2px 8px', fontSize: '11px', color: '#5a7a9a' }}>💰 {step.fare}</span>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Full Map Area */}
        <div className="glass-card" style={{ flex: 1, padding: '8px', overflow: 'hidden', display: 'flex' }}>
          <MapContainer center={mapCenter} zoom={13} style={{ width: '100%', height: '100%', borderRadius: '12px', zIndex: 1 }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
            <MapUpdater center={mapCenter} bounds={mapBounds} />
            
            {routeLine && <Polyline positions={routeLine} color="#185FA5" weight={5} opacity={0.7} />}
            
            {markers.length > 0 ? (
              markers.map((m, i) => (
                <Marker key={i} position={m.pos}>
                  <Popup>{m.label}</Popup>
                </Marker>
              ))
            ) : (
              <Marker position={mapCenter}>
                <Popup>Map centered around {form.city || 'your destination'}</Popup>
              </Marker>
            )}
          </MapContainer>
        </div>

      </div>
    </div>
  );
}
