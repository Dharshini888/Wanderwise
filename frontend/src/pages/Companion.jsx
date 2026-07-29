import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router-dom';
import MapComponent from '../components/MapComponent';
import {
  IconCalendar,
  IconUsers,
  IconClock,
  IconSend,
  IconAdjustments,
  IconCompass,
  IconMapPin,
  IconArrowRight,
  IconLoader,
} from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

export default function Companion() {
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replanText, setReplanText] = useState('');
  const [replanning, setReplanning] = useState(false);
  const token = localStorage.getItem('token');

  let userId = null;
  try { 
    const p = JSON.parse(atob(token.split('.')[1])); 
    userId = p.sub || p.user_id || p.id; 
  } catch (_) {}

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
    <div className="flex flex-col h-[calc(100vh-3rem)] gap-6">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconCompass className="text-[var(--color-primary-600)]" size={32} /> My Trips
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">View and modify your AI-generated travel itineraries.</p>
      </div>

      <div className="flex gap-6 flex-1 overflow-hidden">
        
        {/* Sidebar: Trip List */}
        <div className="w-[320px] flex flex-col gap-3 overflow-y-auto pr-2 custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center py-10 text-[var(--text-muted)]">
              <IconLoader className="animate-spin text-[var(--color-primary-500)] mr-2" size={20} />
              <span className="text-sm font-semibold">Loading trips...</span>
            </div>
          ) : trips.length === 0 ? (
            <div className="glass-card p-6 text-center">
              <div className="text-3xl mb-3">🗺️</div>
              <p className="text-sm text-[var(--text-muted)] mb-5 leading-relaxed">No itineraries planned yet. Let's build one!</p>
              <Link to="/dashboard" className="btn btn-primary px-4 py-2.5 text-xs font-semibold inline-flex items-center gap-1.5 shadow-md">
                Plan a Trip
                <IconArrowRight size={14} />
              </Link>
            </div>
          ) : (
            trips.map(trip => {
              const isSelected = selectedTrip?.id === trip.id;
              return (
                <div 
                  key={trip.id} 
                  onClick={() => setSelectedTrip(trip)}
                  className={`glass-card p-5 cursor-pointer transition-all border ${
                    isSelected 
                      ? 'border-[var(--color-primary-500)] bg-[var(--bg-card)] shadow-lg shadow-blue-500/5' 
                      : 'border-[var(--border-color)] bg-[var(--bg-card)] hover:border-[var(--text-muted)]/50'
                  }`}
                >
                  <h3 className="text-base font-bold text-[var(--text-primary)] mb-1.5 font-heading truncate">{trip.destination}</h3>
                  <div className="text-xs text-[var(--text-muted)] mb-3 flex items-center gap-1.5">
                    <IconCalendar size={14} />
                    <span>{trip.start_date} to {trip.end_date}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-blue-50 dark:bg-blue-950/20 text-[var(--color-primary-600)] dark:text-blue-400 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">{trip.travel_type}</span>
                    <span className="bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">${trip.budget?.toLocaleString()}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Main Content: Trip Details & Itinerary */}
        <div className="glass-card flex-1 p-6 sm:p-8 overflow-y-auto relative bg-[var(--bg-card)]">
          {selectedTrip ? (
            <div className="max-w-3xl mx-auto flex flex-col gap-6">
              
              {/* Trip Header Banner */}
              <div className="border-b border-[var(--border-color)] pb-6">
                <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-3">
                  {selectedTrip.destination}
                </h2>
                <div className="flex flex-wrap gap-4 text-xs font-semibold text-[var(--text-muted)]">
                  <span className="flex items-center gap-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg">
                    <IconCalendar size={14} className="text-blue-500" /> 
                    {selectedTrip.start_date} — {selectedTrip.end_date}
                  </span>
                  <span className="flex items-center gap-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg">
                    <IconClock size={14} className="text-amber-500" /> 
                    {getDays(selectedTrip)} Days
                  </span>
                  <span className="flex items-center gap-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] px-3 py-1.5 rounded-lg">
                    <IconUsers size={14} className="text-emerald-500" /> 
                    {selectedTrip.group_size} Travelers
                  </span>
                </div>
              </div>

              {/* Interactive Map */}
              <div>
                <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">Interactive Map</h3>
                <div className="border border-[var(--border-color)] rounded-2xl overflow-hidden shadow-sm h-[260px] bg-slate-100">
                  <MapComponent destination={selectedTrip.destination} />
                </div>
              </div>

              {/* Replanning Feature */}
              <div className="bg-blue-50/20 dark:bg-blue-950/5 border border-blue-200/50 dark:border-blue-900/10 p-5 rounded-2xl flex flex-col gap-3">
                <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
                  <IconAdjustments size={18} className="text-[var(--color-primary-600)]" /> Customize Itinerary
                </h3>
                <div className="flex gap-2">
                  <input 
                    value={replanText} 
                    onChange={(e) => setReplanText(e.target.value)} 
                    placeholder="e.g. Find vegan restaurants, add sightseeing destinations..." 
                    className="flex-1 px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/10"
                  />
                  <button 
                    onClick={handleReplan} 
                    disabled={replanning || !replanText.trim()}
                    className="btn btn-primary px-5 font-semibold flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                  >
                    {replanning ? (
                      <>
                        <IconLoader className="animate-spin" size={16} />
                        <span>Updating...</span>
                      </>
                    ) : (
                      <>
                        <IconSend size={16} />
                        <span>Replan</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Markdown Itinerary Render */}
              <div className="prose dark:prose-invert max-w-none text-[var(--text-primary)] leading-relaxed text-sm sm:text-base border-t border-[var(--border-color)] pt-6">
                <ReactMarkdown
                  components={{
                    h1: ({node, ...props}) => <h1 className="text-xl sm:text-2xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 border-b border-[var(--border-color)] pb-2 mt-8 mb-4 font-heading" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-lg sm:text-xl font-bold text-[var(--text-primary)] mt-6 mb-3 font-heading" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-sm sm:text-base font-bold text-[var(--text-secondary)] mt-4 mb-2 font-heading" {...props} />,
                    strong: ({node, ...props}) => <strong className="text-[var(--color-primary-600)] dark:text-blue-400 font-extrabold" {...props} />,
                    ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-4 space-y-1.5" {...props} />,
                    li: ({node, ...props}) => <li className="text-[var(--text-secondary)]" {...props} />,
                    p: ({node, ...props}) => <p className="mb-4 text-[var(--text-secondary)]" {...props} />,
                    a: ({node, ...props}) => <a className="text-[var(--color-primary-600)] dark:text-blue-400 font-bold hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                  }}
                >
                  {selectedTrip.itinerary || '*No itinerary generated yet.*'}
                </ReactMarkdown>
              </div>

            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-[var(--text-muted)] text-sm font-semibold flex-col gap-2">
              <span className="text-4xl">🗺️</span>
              <span>Select a trip to view its details</span>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
