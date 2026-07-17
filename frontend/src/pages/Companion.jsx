import { useState, useEffect } from 'react'; // Trigger Vite HMR
import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router-dom';
import MapComponent from '../components/MapComponent';

const API = 'http://localhost:8000/api';

export default function Companion() {
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replanText, setReplanText] = useState('');
  const [replanning, setReplanning] = useState(false);
  const token = localStorage.getItem('token');

  let userId = null;
  try { const p = JSON.parse(atob(token.split('.')[1])); userId = p.sub || p.user_id || p.id; } catch (_) {}

  const fetchTrips = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setTrips(data);
        if (data.length > 0) setSelectedTrip(data[0]);
      }
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { fetchTrips(); }, [userId, token]);

  const handleReplan = async () => {
    if (!replanText.trim() || !selectedTrip) return;
    setReplanning(true);
    try {
      const res = await fetch(`${API}/trips/${selectedTrip.id}/replan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ modification_request: replanText }),
      });
      if (res.ok) {
        const updatedTrip = await res.json();
        setSelectedTrip(updatedTrip);
        setTrips(trips.map(t => t.id === updatedTrip.id ? updatedTrip : t));
        setReplanText('');
      }
    } catch (_) {}
    setReplanning(false);
  };

  const getDays = (t) => Math.round((new Date(t.end_date) - new Date(t.start_date)) / 86400000) + 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 3rem)', gap: '1.5rem' }}>
      
      <div>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>📍 My Trips</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>View your AI-generated itineraries and trip details.</p>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', flex: 1, overflow: 'hidden' }}>
        
        {/* Sidebar: Trip List */}
        <div style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px' }}>
          {loading ? (
            <div className="text-secondary">Loading trips...</div>
          ) : trips.length === 0 ? (
            <div className="glass-card" style={{ padding: '24px', textAlign: 'center' }}>
              <p className="text-secondary" style={{ margin: '0 0 16px' }}>No trips planned yet.</p>
              <Link to="/dashboard" style={{ background: '#185FA5', color: 'white', padding: '10px 16px', borderRadius: '8px', textDecoration: 'none', fontSize: '13px', fontWeight: 600 }}>Plan a Trip</Link>
            </div>
          ) : (
            trips.map(trip => (
              <div key={trip.id} onClick={() => setSelectedTrip(trip)}
                className="glass-card"
                style={{ 
                  padding: '16px', cursor: 'pointer', transition: 'all 0.2s',
                  border: selectedTrip?.id === trip.id ? '2px solid #185FA5' : '1px solid rgba(200, 225, 245, 0.9)',
                  background: selectedTrip?.id === trip.id ? 'rgba(255,255,255,1)' : 'rgba(255,255,255,0.7)',
                  boxShadow: selectedTrip?.id === trip.id ? '0 4px 14px rgba(24, 95, 165, 0.15)' : 'none'
                }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 8px', fontSize: '15px' }}>{trip.destination}</h3>
                <div className="text-secondary" style={{ fontSize: '12px', marginBottom: '8px' }}>
                  {trip.start_date} to {trip.end_date}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span style={{ background: 'rgba(24, 95, 165, 0.1)', color: '#185FA5', padding: '2px 8px', borderRadius: '10px', fontSize: '10px', fontWeight: 700, textTransform: 'uppercase' }}>{trip.travel_type}</span>
                  <span style={{ background: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', padding: '2px 8px', borderRadius: '10px', fontSize: '10px', fontWeight: 700 }}>${trip.budget?.toLocaleString()}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Main Content: Trip Details & Itinerary */}
        <div className="glass-card" style={{ flex: 1, padding: '32px', overflowY: 'auto', position: 'relative' }}>
          {selectedTrip ? (
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              <div style={{ marginBottom: '32px', borderBottom: '1px solid rgba(200, 225, 245, 0.9)', paddingBottom: '24px' }}>
                <h2 className="text-primary-dark" style={{ margin: '0 0 8px', fontSize: '2.5rem', letterSpacing: '-1px' }}>{selectedTrip.destination}</h2>
                <div style={{ display: 'flex', gap: '24px', color: '#5a7a9a', fontSize: '14px', fontWeight: 500 }}>
                  <span>📅 {selectedTrip.start_date} — {selectedTrip.end_date}</span>
                  <span>⏱️ {getDays(selectedTrip)} Days</span>
                  <span>👥 {selectedTrip.group_size} Travelers</span>
                </div>
              </div>

              {/* Interactive Map */}
              <div style={{ marginBottom: '32px' }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '1.2rem' }}>Interactive Map</h3>
                <MapComponent destination={selectedTrip.destination} />
              </div>

              {/* Replanning Feature */}
              <div style={{ marginBottom: '32px', background: 'rgba(24, 95, 165, 0.05)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(24, 95, 165, 0.2)' }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 12px', fontSize: '1.1rem' }}>🔄 Modify Itinerary</h3>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <input 
                    value={replanText} 
                    onChange={(e) => setReplanText(e.target.value)} 
                    placeholder="e.g. The Louvre is closed tomorrow, what should we do instead?" 
                    style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid #c8dff0', outline: 'none', fontSize: '13px' }}
                  />
                  <button 
                    onClick={handleReplan} 
                    disabled={replanning || !replanText.trim()}
                    style={{ background: '#185FA5', color: 'white', border: 'none', padding: '0 20px', borderRadius: '8px', fontWeight: 600, cursor: replanning || !replanText.trim() ? 'not-allowed' : 'pointer', opacity: replanning || !replanText.trim() ? 0.7 : 1 }}
                  >
                    {replanning ? 'Updating...' : 'Replan'}
                  </button>
                </div>
              </div>

              <div className="itinerary-content" style={{ color: '#1a2a3a', lineHeight: 1.6, fontSize: '15px' }}>
                <ReactMarkdown
                  components={{
                    h1: ({node, ...props}) => <h1 style={{ color: '#185FA5', borderBottom: '2px solid rgba(24, 95, 165, 0.1)', paddingBottom: '8px', marginTop: '32px', fontSize: '1.8rem' }} {...props} />,
                    h2: ({node, ...props}) => <h2 style={{ color: '#1a2a3a', marginTop: '24px', fontSize: '1.4rem' }} {...props} />,
                    h3: ({node, ...props}) => <h3 style={{ color: '#4a6080', marginTop: '20px', fontSize: '1.2rem' }} {...props} />,
                    strong: ({node, ...props}) => <strong style={{ color: '#185FA5', fontWeight: 700 }} {...props} />,
                    ul: ({node, ...props}) => <ul style={{ paddingLeft: '24px', marginBottom: '16px' }} {...props} />,
                    li: ({node, ...props}) => <li style={{ marginBottom: '8px' }} {...props} />,
                  }}
                >
                  {selectedTrip.itinerary || '*No itinerary generated yet.*'}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#5a7a9a' }}>
              Select a trip to view details.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
