import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  IconMapPin,
  IconClock,
  IconCoin,
  IconWalk,
  IconBus,

  IconTrain,
  IconCar,
  IconNavigation,
  IconAlertCircle,
  IconRoad,
} from '@tabler/icons-react';

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

const TYPE_ICONS = {
  walk: <IconWalk size={16} />,
  bus: <IconBus size={16} />,
  metro: <IconTrain size={16} />,
  train: <IconTrain size={16} />,
  auto: <IconCar size={16} />,
  taxi: <IconCar size={16} />,
};

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
          const coords = osrmRes.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
          setRouteLine(coords);
          
          const lats = coords.map(c => c[0]);
          const lons = coords.map(c => c[1]);
          setMapBounds([
            [Math.min(...lats), Math.min(...lons)],
            [Math.max(...lats), Math.max(...lons)]
          ]);
        } else {
          setMapBounds([ [fromLat, fromLon], [toLat, toLon] ]);
        }
      } else {
        const resCity = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(form.city)}&limit=1`).then(r => r.json());
        if (resCity[0]) setMapCenter([parseFloat(resCity[0].lat), parseFloat(resCity[0].lon)]);
      }

    } catch (err) { setError(err.message || 'Network error'); }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] gap-6">
      
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconRoad className="text-[var(--color-primary-600)]" size={32} /> Maps & Transit
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Navigate unfamiliar cities seamlessly with step-by-step guidance.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 flex-1 overflow-hidden">
        
        {/* Sidebar */}
        <div className="w-full lg:w-[400px] flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
          
          <form className="glass-card p-6 flex flex-col gap-4 bg-[var(--bg-card)]" onSubmit={handleSearch}>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">From Location</label>
              <input 
                className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" 
                value={form.from_location} 
                onChange={e => setForm(f => ({ ...f, from_location: e.target.value }))} 
                placeholder="e.g. Hotel Radisson" 
                required 
              />
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">To Destination</label>
              <input 
                className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" 
                value={form.to_location} 
                onChange={e => setForm(f => ({ ...f, to_location: e.target.value }))} 
                placeholder="e.g. India Gate" 
                required 
              />
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">City</label>
              <input 
                className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" 
                value={form.city} 
                onChange={e => setForm(f => ({ ...f, city: e.target.value }))} 
                placeholder="e.g. New Delhi" 
                required 
              />
            </div>
            <button 
              type="submit" 
              disabled={loading}
              className="btn btn-primary py-3 mt-2 text-sm font-semibold flex items-center justify-center gap-2 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
                  <span>Computing route...</span>
                </>
              ) : (
                <>
                  <IconNavigation size={18} />
                  <span>Get Directions</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-600 dark:text-red-400 text-sm font-semibold flex items-center gap-2">
              <IconAlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="glass-card p-6 flex flex-col bg-[var(--bg-card)] animate-fadeIn">
              <h3 className="text-base font-bold text-[var(--text-primary)] font-heading mb-3">Route Summary</h3>
              
              <div className="bg-blue-50/20 dark:bg-blue-950/5 border border-blue-200/50 dark:border-blue-900/10 p-4 rounded-xl mb-5">
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-4">{result.summary}</p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-2 rounded-lg">
                    <div className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center justify-center gap-1"><IconClock size={10} /> Time</div>
                    <div className="text-xs font-bold text-[var(--text-primary)] mt-0.5">{result.total_time}</div>
                  </div>
                  <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-2 rounded-lg">
                    <div className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center justify-center gap-1"><IconCoin size={10} /> Fare</div>
                    <div className="text-xs font-bold text-[var(--text-primary)] mt-0.5">{result.total_fare}</div>
                  </div>
                  <div className="bg-[var(--bg-card)] border border-[var(--border-color)] p-2 rounded-lg">
                    <div className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center justify-center gap-1"><IconWalk size={10} /> Walk</div>
                    <div className="text-xs font-bold text-[var(--text-primary)] mt-0.5">{result.walking_distance}</div>
                  </div>
                </div>
              </div>

              {result.steps && (
                <>
                  <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4">Route Steps</h3>
                  <div className="flex flex-col">
                    {result.steps.map((step, i) => (
                      <div key={i} className="flex gap-4 items-start">
                        <div className="flex flex-col items-center flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-950 text-[var(--color-primary-600)] dark:text-blue-400 flex items-center justify-center border border-blue-100 dark:border-blue-900">
                            {TYPE_ICONS[step.type] || <IconMapPin size={16} />}
                          </div>
                          {i < result.steps.length - 1 && (
                            <div className="w-0.5 bg-[var(--border-color)] h-12 my-1" />
                          )}
                        </div>
                        <div className="flex-1 pb-6 pt-1">
                          <div className="text-xs font-extrabold text-[var(--text-primary)] mb-1 font-heading">{step.instruction}</div>
                          {step.detail && <div className="text-xs text-[var(--text-muted)] leading-relaxed mb-2">{step.detail}</div>}
                          <div className="flex gap-2">
                            {step.duration && <span className="text-[9px] font-semibold bg-[var(--bg-app)] border border-[var(--border-color)] px-2 py-0.5 rounded-full text-[var(--text-muted)]">⏱️ {step.duration}</span>}
                            {step.fare && <span className="text-[9px] font-semibold bg-[var(--bg-app)] border border-[var(--border-color)] px-2 py-0.5 rounded-full text-[var(--text-muted)]">💰 {step.fare}</span>}
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

        {/* Map */}
        <div className="glass-card flex-1 p-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl overflow-hidden min-h-[300px] lg:min-h-0">
          <MapContainer center={mapCenter} zoom={13} style={{ width: '100%', height: '100%', borderRadius: '12px', zIndex: 1 }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
            <MapUpdater center={mapCenter} bounds={mapBounds} />
            
            {routeLine && <Polyline positions={routeLine} color="#2563EB" weight={5} opacity={0.8} />}
            
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
