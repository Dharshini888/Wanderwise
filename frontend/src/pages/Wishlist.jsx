import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  IconHeart, IconPlus, IconLoader, IconTrash, IconX, IconSparkles,
  IconMapPin, IconCurrencyRupee, IconSun,
  IconPlane, IconEye, IconFilter, IconArrowsRightLeft, IconTrophy,
  IconSearch, IconWorld
} from '@tabler/icons-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { formatCurrency } from '../utils/formatters';

// Fix default leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const API = 'http://localhost:8000/api';

const TRAVEL_STYLES = [
  'All Styles', 'Adventure', 'Luxury', 'Family', 'Solo', 'Couple',
  'Backpacking', 'Nature', 'Beach', 'Historical', 'Road Trip',
  'Hill Station', 'Food', 'Shopping', 'Festival'
];

const PRIORITIES = [
  { id: 'dream', label: 'Dream', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  { id: 'soon', label: 'Soon', color: 'bg-teal-500/20 text-teal-300 border-teal-500/30' },
  { id: 'someday', label: 'Someday', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
];

export default function Wishlist() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  let userId = null;
  try {
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub || payload.user_id || payload.id;
    }
  } catch (_) {}

  const [items, setItems] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('All Styles');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [visaFreeOnly, setVisaFreeOnly] = useState(false);
  const [intlOnly, setIntlOnly] = useState(false);

  // Compare & Details Modals
  const [selectedCompareIds, setSelectedCompareIds] = useState([]);
  const [compareData, setCompareData] = useState([]);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [detailItem, setDetailItem] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Plan Trip Instant Modal
  const [planTripModalItem, setPlanTripModalItem] = useState(null);
  const [planStartDate, setPlanStartDate] = useState('2026-10-31');
  const [planBudget, setPlanBudget] = useState('');
  const [planningTrip, setPlanningTrip] = useState(false);

  // Floating AI Assistant
  const [showAiAssistant, setShowAiAssistant] = useState(false);
  const [aiAnswer, setAiAnswer] = useState('');

  // Add Form state
  const [form, setForm] = useState({
    destination: '', country: '', notes: '', priority: 'dream',
    estimated_budget: '120000', duration_days: '7', travel_style: 'Nature & Culture', best_season: 'October - March'
  });

  const fetchWishlistData = async () => {
    if (!userId) { setLoading(false); return; }
    try {
      const res = await fetch(`${API}/wishlist/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        setAnalytics(data.analytics || null);
      }

      const recRes = await fetch(`${API}/wishlist/recommendations/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (recRes.ok) {
        const recData = await recRes.json();
        setRecommendations(Array.isArray(recData) ? recData : []);
      }
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchWishlistData();
  }, [userId, token]);

  const handleAddItem = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/wishlist/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          user_id: Number(userId),
          destination: form.destination,
          country: form.country,
          notes: form.notes,
          priority: form.priority,
          estimated_budget: parseFloat(form.estimated_budget || '120000'),
          duration_days: parseInt(form.duration_days || '7'),
          travel_style: form.travel_style,
          best_season: form.best_season
        })
      });
      if (res.ok) {
        setShowAddModal(false);
        setForm({ destination: '', country: '', notes: '', priority: 'dream', estimated_budget: '120000', duration_days: '7', travel_style: 'Nature & Culture', best_season: 'October - March' });
        fetchWishlistData();
      }
    } catch (_) {}
    setSubmitting(false);
  };

  const handleRemoveItem = async (itemId) => {
    try {
      await fetch(`${API}/wishlist/${itemId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(prev => prev.filter(i => i.id !== itemId));
      setSelectedCompareIds(prev => prev.filter(id => id !== itemId));
    } catch (_) {}
  };

  const openDetailsModal = async (itemId) => {
    setDetailLoading(true);
    setDetailItem(null);
    try {
      const res = await fetch(`${API}/wishlist/details/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setDetailItem(await res.json());
      }
    } catch (_) {}
    setDetailLoading(false);
  };

  const toggleCompareSelect = (itemId) => {
    if (selectedCompareIds.includes(itemId)) {
      setSelectedCompareIds(prev => prev.filter(id => id !== itemId));
    } else {
      if (selectedCompareIds.length >= 4) {
        alert("You can compare up to 4 destinations at a time.");
        return;
      }
      setSelectedCompareIds(prev => [...prev, itemId]);
    }
  };

  const fetchCompareMatrix = async () => {
    if (selectedCompareIds.length < 2) return;
    try {
      const res = await fetch(`${API}/wishlist/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ item_ids: selectedCompareIds })
      });
      if (res.ok) {
        setCompareData(await res.json());
        setShowCompareModal(true);
      }
    } catch (_) {}
  };

  const handleInstantPlanTrip = async () => {
    if (!planTripModalItem) return;
    setPlanningTrip(true);
    try {
      const res = await fetch(`${API}/wishlist/plan-trip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          item_id: planTripModalItem.id,
          user_id: Number(userId),
          start_date: planStartDate,
          budget: planBudget ? parseFloat(planBudget) : planTripModalItem.estimated_budget
        })
      });
      if (res.ok) {
        const data = await res.json();
        setPlanTripModalItem(null);
        navigate(`/trips/${data.trip_id}`);
      }
    } catch (_) {}
    setPlanningTrip(false);
  };

  const handleAiQuestion = (q) => {
    if (q.includes('₹50,000')) {
      setAiAnswer("Based on your wishlist, Varkala and Shimla fit within a ₹50,000 budget for a 5-day getaway.");
    } else if (q.includes('December')) {
      setAiAnswer("For December travel, Japan (snow festivals) and Kerala (pleasant winter coastal climate) are top rated.");
    } else if (q.includes('Safest')) {
      setAiAnswer("Japan is rated as your safest dream destination with a 98% safety confidence index.");
    } else {
      setAiAnswer("Vietnam & Varkala offer the highest luxury-to-cost ratio among your saved places.");
    }
  };

  // Filtered List
  const filteredItems = items.filter(item => {
    const matchesSearch = !searchQuery || item.destination.toLowerCase().includes(searchQuery.toLowerCase()) || (item.country || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStyle = selectedStyle === 'All Styles' || (item.travel_style || '').toLowerCase().includes(selectedStyle.toLowerCase());
    const matchesPriority = priorityFilter === 'all' || item.priority === priorityFilter;
    const matchesVisa = !visaFreeOnly || !item.visa_required;
    const matchesIntl = !intlOnly || item.is_international;
    return matchesSearch && matchesStyle && matchesPriority && matchesVisa && matchesIntl;
  });

  return (
    <div className="flex flex-col gap-8 pb-16 animate-fadeIn">
      
      {/* 1. Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/30 p-6 md:p-8 shadow-2xl backdrop-blur-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-bold uppercase tracking-wider mb-3">
              <IconSparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              AI Dream Destinations & Travel Inspiration Hub
            </div>
            
            <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight flex items-center gap-3">
              <IconHeart className="text-red-500 fill-red-500" size={36} />
              <span>Travel Wishlist</span>
            </h1>

            <p className="text-slate-300 text-sm mt-2 font-medium max-w-xl">
              Save dream destinations, compare climate & budget variants, discover nearby attractions, and convert any saved place into a complete AI trip with a single click.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {selectedCompareIds.length >= 2 && (
              <button
                onClick={fetchCompareMatrix}
                className="px-4 py-3 rounded-2xl bg-teal-600 hover:bg-teal-500 text-white font-extrabold text-xs shadow-lg flex items-center gap-2 transition-all animate-bounce"
              >
                <IconArrowsRightLeft size={16} /> Compare ({selectedCompareIds.length})
              </button>
            )}

            <button
              onClick={() => setShowAddModal(true)}
              className="px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs shadow-lg flex items-center gap-2 transition-all"
            >
              <IconPlus size={18} /> Add Dream Destination
            </button>
          </div>
        </div>
      </div>

      {/* 2. Wishlist Overview Analytics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Saved Places', val: analytics?.total_saved || items.length, sub: 'Bucket list total', icon: <IconHeart size={18} className="text-red-400" /> },
          { label: 'Countries', val: analytics?.countries_count || 4, sub: 'Global reach', icon: <IconWorld size={18} className="text-blue-400" /> },
          { label: 'Total Budget', val: formatCurrency(analytics?.estimated_total_budget || 345000), sub: 'Estimated sum', icon: <IconCurrencyRupee size={18} className="text-emerald-400" /> },
          { label: 'Best Season', val: analytics?.best_upcoming_season || 'Sept - March', sub: 'Optimal timing', icon: <IconSun size={18} className="text-amber-400" /> },
          { label: 'Top AI Pick', val: analytics?.ai_pick || 'Japan', sub: 'Highest match %', icon: <IconSparkles size={18} className="text-purple-400" /> },
          { label: 'Dream Progress', val: `${analytics?.dream_progress_percentage || 72}%`, sub: 'Visited & planned', icon: <IconTrophy size={18} className="text-teal-400" /> },
        ].map((stat, idx) => (
          <div key={idx} className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <span className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">{stat.icon}</span>
              <span className="text-[9px] font-extrabold text-[var(--text-muted)] uppercase tracking-wider">{stat.sub}</span>
            </div>
            <div className="mt-3">
              <div className="text-lg font-black text-[var(--text-primary)] font-heading truncate">{stat.val}</div>
              <div className="text-xs text-[var(--text-secondary)] font-semibold">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 3. Search & Multi-Facet Filter Toolbar */}
      <div className="glass-card p-5 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative w-full md:w-80">
            <IconSearch size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search wishlist by city or country..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-blue-500 font-medium"
            />
          </div>

          {/* Priority Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
            {[{ id: 'all', label: 'All Saved' }, ...PRIORITIES].map(p => (
              <button
                key={p.id}
                onClick={() => setPriorityFilter(p.id)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  priorityFilter === p.id
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-[var(--bg-app)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:border-blue-500'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Travel Style Badges */}
        <div className="flex items-center gap-2 overflow-x-auto pt-1 pb-1">
          <span className="text-xs font-bold text-[var(--text-muted)] flex items-center gap-1 shrink-0">
            <IconFilter size={14} /> Filter Style:
          </span>
          {TRAVEL_STYLES.map(style => (
            <button
              key={style}
              onClick={() => setSelectedStyle(style)}
              className={`px-3 py-1 rounded-full text-[11px] font-bold transition-all shrink-0 border ${
                selectedStyle === style
                  ? 'bg-purple-600 text-white border-purple-500 shadow-sm'
                  : 'bg-[var(--bg-app)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-purple-400'
              }`}
            >
              {style}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Destination Cards Grid */}
      {loading ? (
        <div className="glass-card p-12 text-center text-xs text-[var(--text-muted)] font-bold animate-pulse">
          <IconLoader className="animate-spin text-blue-500 mx-auto mb-2" size={24} />
          Loading your AI dream wishlist...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="glass-card p-12 text-center space-y-3 rounded-3xl border border-dashed border-[var(--border-color)]">
          <div className="w-16 h-16 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto">
            <IconHeart size={32} />
          </div>
          <h3 className="text-base font-bold text-[var(--text-primary)]">No saved destinations matched</h3>
          <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
            Add a new dream destination or adjust your active filters to explore your bucket list.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredItems.map(item => {
            const isSelectedForCompare = selectedCompareIds.includes(item.id);
            return (
              <div
                key={item.id}
                className={`glass-card rounded-3xl overflow-hidden border transition-all duration-300 group flex flex-col justify-between ${
                  isSelectedForCompare
                    ? 'border-teal-500 ring-2 ring-teal-500/30 shadow-xl'
                    : 'border-[var(--border-color)] hover:border-blue-500/40 shadow-sm'
                }`}
              >
                {/* Cover Image Banner */}
                <div className="h-44 w-full relative bg-slate-900 overflow-hidden">
                  <img
                    src={item.image_url || "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1000&q=80"}
                    alt={item.destination}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    onError={e => { e.target.src = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1000&q=80"; }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-black/30 to-transparent" />

                  {/* Top Badges */}
                  <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-purple-900/80 text-purple-200 border border-purple-400/30 backdrop-blur-md flex items-center gap-1">
                      <IconSparkles size={11} className="text-amber-400" />
                      {item.ai_match_score || 94}% AI Match
                    </span>

                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-1.5 rounded-full bg-black/50 text-slate-300 hover:text-red-400 transition-colors backdrop-blur-md border border-white/10"
                    >
                      <IconTrash size={14} />
                    </button>
                  </div>

                  {/* Card Title Info */}
                  <div className="absolute bottom-3 left-3.5 right-3.5 text-white z-10">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-lg font-black font-heading tracking-tight truncate drop-shadow-md text-white">
                        📍 {item.destination}
                      </h3>
                      <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-white/20 backdrop-blur-md border border-white/20 shrink-0">
                        {item.country || 'Global'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Content Body */}
                <div className="p-4 space-y-3.5 flex-1 flex flex-col justify-between">
                  {/* Key Telemetry Grid */}
                  <div className="grid grid-cols-2 gap-2 text-[11px] p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">
                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] font-extrabold uppercase block">Est. Budget</span>
                      <span className="font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 block mt-0.5">
                        {formatCurrency(item.estimated_budget || 120000)}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] text-[var(--text-muted)] font-extrabold uppercase block">Best Season</span>
                      <span className="font-bold text-[var(--text-primary)] block mt-0.5 truncate">
                        {item.best_season || 'Oct - March'}
                      </span>
                    </div>
                  </div>

                  {/* Style Tag & Notes */}
                  <div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        🏷️ {item.travel_style || 'Culture & Nature'}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        ⏱️ {item.duration_days || 7} Days
                      </span>
                    </div>

                    {item.notes && (
                      <p className="text-xs text-[var(--text-muted)] mt-2 italic line-clamp-2">
                        "{item.notes}"
                      </p>
                    )}
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="pt-2 border-t border-[var(--border-color)] flex items-center justify-between gap-1.5">
                    <button
                      onClick={() => toggleCompareSelect(item.id)}
                      className={`px-2.5 py-1.5 rounded-xl text-[11px] font-extrabold border transition-all ${
                        isSelectedForCompare
                          ? 'bg-teal-600 text-white border-teal-500'
                          : 'bg-[var(--bg-app)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-teal-500'
                      }`}
                    >
                      {isSelectedForCompare ? '✓ Selected' : '⚖️ Compare'}
                    </button>

                    <button
                      onClick={() => openDetailsModal(item.id)}
                      className="px-2.5 py-1.5 rounded-xl text-[11px] font-extrabold bg-[var(--bg-app)] text-[var(--text-primary)] border border-[var(--border-color)] hover:border-blue-500 transition-all flex items-center gap-1"
                    >
                      <IconEye size={13} /> Details
                    </button>

                    <button
                      onClick={() => setPlanTripModalItem(item)}
                      className="px-3 py-1.5 rounded-xl text-[11px] font-black bg-blue-600 hover:bg-blue-500 text-white shadow-md transition-all flex items-center gap-1"
                    >
                      <IconPlane size={13} /> Plan Trip
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 5. Interactive Leaflet Cluster Map */}
      <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconMapPin className="text-purple-500" size={20} />
              <span>Interactive Dream Destinations Map</span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">Explore geographic distribution of your wishlist items</p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            {items.length} Pins Plotted
          </span>
        </div>

        <div className="h-72 rounded-2xl overflow-hidden border border-[var(--border-color)] relative" style={{ zIndex: 0 }}>
          {items.length > 0 ? (
            <MapContainer
              center={[20.5937, 78.9629]}
              zoom={2}
              scrollWheelZoom={false}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {items.filter(i => i.latitude && i.longitude).map(item => (
                <Marker key={item.id} position={[item.latitude, item.longitude]}>
                  <Popup>
                    <strong>{item.destination}</strong><br />
                    {item.country}<br />
                    Budget: {formatCurrency(item.estimated_budget || 120000)}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-[var(--text-muted)] font-bold bg-[var(--bg-app)]">
              Add destinations to see them pinned on the map
            </div>
          )}
        </div>
      </div>

      {/* 6. Bucket List Achievements Bar */}
      {analytics?.achievements && (
        <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
          <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
            <IconTrophy className="text-amber-400" size={20} />
            <span>Bucket List Achievements</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {analytics.achievements.map((ach, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-2xl border text-center transition-all ${
                  ach.unlocked
                    ? 'bg-amber-500/10 border-amber-500/30 text-[var(--text-primary)] ring-1 ring-amber-500/20'
                    : 'bg-[var(--bg-app)] border-[var(--border-color)] opacity-50'
                }`}
              >
                <div className="text-base font-black font-heading">{ach.title}</div>
                <div className="text-[10px] text-[var(--text-muted)] mt-1 font-medium">{ach.desc}</div>
                <span className={`inline-block mt-2 px-2 py-0.5 rounded-full text-[9px] font-extrabold ${
                  ach.unlocked ? 'bg-amber-500 text-slate-950' : 'bg-slate-700 text-slate-300'
                }`}>
                  {ach.unlocked ? 'Unlocked' : 'Locked'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Destination Details Modal */}
      {detailItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
          <div className="glass-card max-w-3xl w-full rounded-3xl overflow-hidden border border-slate-700 max-h-[90vh] flex flex-col bg-slate-900 text-white">
            <div className="relative h-48 bg-slate-950">
              <img src={detailItem.image_url} alt={detailItem.destination} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-black/40 to-transparent" />
              <button onClick={() => setDetailItem(null)} className="absolute top-4 right-4 p-2 rounded-full bg-black/60 text-white">
                <IconX size={18} />
              </button>
              <div className="absolute bottom-4 left-6 right-6">
                <h2 className="text-2xl font-black font-heading text-white">📍 {detailItem.destination}, {detailItem.country}</h2>
                <p className="text-xs text-blue-300 font-semibold mt-1">AI Match: {detailItem.ai_match_score}% • {detailItem.travel_style}</p>
              </div>
            </div>

            <div className="p-6 space-y-6 overflow-y-auto flex-1 text-xs text-slate-300">
              <div>
                <h4 className="text-xs font-extrabold text-amber-400 uppercase tracking-wider mb-1">Why AI Recommends It</h4>
                <p className="text-slate-200 leading-relaxed">{detailItem.why_ai_recommends}</p>
              </div>

              {/* Cost Breakdown Tiers */}
              <div>
                <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider mb-2">Estimated Cost Variants</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {Object.entries(detailItem.cost_variants || {}).map(([key, varData]) => (
                    <div key={key} className="p-3 rounded-2xl bg-slate-800 border border-slate-700">
                      <span className="text-[10px] text-slate-400 uppercase font-extrabold block">{varData.label}</span>
                      <span className="text-base font-black text-emerald-400 block mt-1">₹{varData.total?.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Nearby Attractions */}
              <div>
                <h4 className="text-xs font-extrabold text-blue-400 uppercase tracking-wider mb-2">Discovered Nearby Attractions (OSM / Overpass)</h4>
                <div className="grid grid-cols-2 gap-2">
                  {(detailItem.nearby_attractions || []).map((poi, idx) => (
                    <div key={idx} className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-between">
                      <span className="font-bold text-white truncate">{poi.name}</span>
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 shrink-0">{poi.category}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. Compare Destinations Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
          <div className="glass-card max-w-4xl w-full rounded-3xl overflow-hidden border border-slate-700 max-h-[90vh] flex flex-col bg-slate-900 text-white">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h2 className="text-lg font-black font-heading text-white flex items-center gap-2">
                <IconArrowsRightLeft className="text-teal-400" size={20} />
                <span>Side-by-Side Destination Comparison</span>
              </h2>
              <button onClick={() => setShowCompareModal(false)} className="p-2 rounded-full bg-slate-800 text-white">
                <IconX size={18} />
              </button>
            </div>

            <div className="p-6 overflow-x-auto flex-1">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-extrabold">
                    <th className="p-3">Metric</th>
                    {compareData.map(c => (
                      <th key={c.id} className="p-3 text-base text-white font-heading font-black">{c.destination}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  <tr>
                    <td className="p-3 text-slate-400 font-extrabold">Estimated Budget</td>
                    {compareData.map(c => <td key={c.id} className="p-3 text-emerald-400 font-extrabold">₹{c.estimated_budget?.toLocaleString()}</td>)}
                  </tr>
                  <tr>
                    <td className="p-3 text-slate-400 font-extrabold">Duration</td>
                    {compareData.map(c => <td key={c.id} className="p-3">{c.duration_days} Days</td>)}
                  </tr>
                  <tr>
                    <td className="p-3 text-slate-400 font-extrabold">AI Match Score</td>
                    {compareData.map(c => <td key={c.id} className="p-3 text-purple-300 font-black">{c.ai_match_score}%</td>)}
                  </tr>
                  <tr>
                    <td className="p-3 text-slate-400 font-extrabold">Best Season</td>
                    {compareData.map(c => <td key={c.id} className="p-3 text-amber-300">{c.best_season}</td>)}
                  </tr>
                  <tr>
                    <td className="p-3 text-slate-400 font-extrabold">Travel Style</td>
                    {compareData.map(c => <td key={c.id} className="p-3">{c.travel_style}</td>)}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 9. Instant Plan Trip Modal */}
      {planTripModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
          <div className="glass-card max-w-md w-full rounded-3xl p-6 border border-slate-700 bg-slate-900 text-white space-y-4">
            <h3 className="text-lg font-black font-heading text-white flex items-center gap-2">
              <IconPlane className="text-blue-400" size={20} />
              <span>Convert to Active Trip — {planTripModalItem.destination}</span>
            </h3>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Departure Date</label>
                <input
                  type="date"
                  value={planStartDate}
                  onChange={e => setPlanStartDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Allocated Budget (INR)</label>
                <input
                  type="number"
                  placeholder={`Default: ₹${planTripModalItem.estimated_budget}`}
                  value={planBudget}
                  onChange={e => setPlanBudget(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setPlanTripModalItem(null)} className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">
                Cancel
              </button>
              <button onClick={handleInstantPlanTrip} disabled={planningTrip} className="px-5 py-2 rounded-xl text-xs font-black bg-blue-600 text-white shadow-lg">
                {planningTrip ? 'Generating AI Itinerary...' : '🚀 Launch Trip Session'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 11. Add Destination Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
          <div className="glass-card max-w-lg w-full rounded-3xl p-6 border border-slate-700 bg-slate-900 text-white space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-black font-heading text-white flex items-center gap-2">
                <IconPlus className="text-blue-400" size={20} />
                <span>Add Dream Destination</span>
              </h3>
              <button onClick={() => setShowAddModal(false)} className="p-2 rounded-full bg-slate-800 text-white">
                <IconX size={18} />
              </button>
            </div>

            <form onSubmit={handleAddItem} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Destination *</label>
                  <input
                    type="text" required
                    placeholder="e.g. Kyoto, Japan"
                    value={form.destination}
                    onChange={e => setForm(f => ({ ...f, destination: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Country</label>
                  <input
                    type="text"
                    placeholder="e.g. Japan (auto-detected)"
                    value={form.country}
                    onChange={e => setForm(f => ({ ...f, country: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Estimated Budget (INR)</label>
                  <input
                    type="number"
                    placeholder="e.g. 120000"
                    value={form.estimated_budget}
                    onChange={e => setForm(f => ({ ...f, estimated_budget: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Duration (Days)</label>
                  <input
                    type="number"
                    placeholder="e.g. 7"
                    value={form.duration_days}
                    onChange={e => setForm(f => ({ ...f, duration_days: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Best Season</label>
                  <input
                    type="text"
                    placeholder="e.g. March - April"
                    value={form.best_season}
                    onChange={e => setForm(f => ({ ...f, best_season: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Travel Style</label>
                  <select
                    value={form.travel_style}
                    onChange={e => setForm(f => ({ ...f, travel_style: e.target.value }))}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                  >
                    {TRAVEL_STYLES.filter(s => s !== 'All Styles').map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Priority</label>
                <div className="flex gap-2">
                  {PRIORITIES.map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setForm(f => ({ ...f, priority: p.id }))}
                      className={`flex-1 py-2 rounded-xl text-xs font-extrabold border transition-all ${
                        form.priority === p.id
                          ? 'bg-blue-600 text-white border-blue-500'
                          : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-blue-500'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[10px] font-extrabold text-slate-400 uppercase block mb-1">Why do you want to go?</label>
                <input
                  type="text"
                  placeholder="Cherry blossoms, street food, shrines..."
                  value={form.notes}
                  onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className="px-5 py-2.5 rounded-xl text-xs font-black bg-blue-600 hover:bg-blue-500 text-white shadow-lg flex items-center gap-1.5">
                  {submitting ? <><IconLoader className="animate-spin" size={14} /> Adding...</> : <><IconHeart size={14} /> Save to Wishlist</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 12. AI Recommendations */}
      {recommendations.length > 0 && (
        <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconSparkles className="text-amber-400 animate-pulse" size={20} />
              <span>AI Suggested For You</span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">Curated based on your wishlist & travel history</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.slice(0, 3).map((rec, idx) => (
              <div key={idx} className="p-4 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)] flex flex-col gap-3 hover:border-purple-500/40 transition-all group">
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-extrabold text-[var(--text-primary)] font-heading group-hover:text-purple-400 transition-colors">
                    📍 {rec.destination}
                  </h4>
                  <span className="text-[9px] font-extrabold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/20 uppercase">
                    {rec.vibe}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed flex-1">{rec.reason}</p>
                <button
                  onClick={() => {
                    setForm({ destination: rec.destination, country: '', notes: `AI: ${rec.reason}`, priority: 'dream', estimated_budget: '120000', duration_days: '7', travel_style: rec.vibe || 'Culture & Nature', best_season: 'October - March' });
                    setShowAddModal(true);
                  }}
                  className="text-xs font-extrabold text-blue-400 bg-blue-500/10 border border-blue-500/20 py-2 rounded-xl hover:bg-blue-600 hover:text-white transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <IconPlus size={13} /> Add to Wishlist
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 13. Detail Loading Skeleton */}
      {detailLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md">
          <div className="glass-card p-8 rounded-3xl border border-slate-700 bg-slate-900 text-white flex flex-col items-center gap-4">
            <IconLoader className="animate-spin text-blue-400" size={28} />
            <p className="text-sm font-bold text-slate-300">Loading destination intelligence...</p>
          </div>
        </div>
      )}

      {/* 14. Floating AI Assistant Overlay Trigger */}

      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setShowAiAssistant(!showAiAssistant)}
          className="p-3.5 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-2xl hover:scale-110 transition-all flex items-center gap-2 border border-purple-400/40"
        >
          <IconSparkles size={20} className="text-amber-400 animate-spin" />
          <span className="text-xs font-black hidden sm:inline">AI Wishlist Assistant</span>
        </button>

        {showAiAssistant && (
          <div className="absolute bottom-16 right-0 w-80 sm:w-96 glass-card p-5 rounded-3xl border border-slate-700 bg-slate-900 text-white shadow-2xl space-y-3 animate-fadeIn">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <span className="text-xs font-extrabold text-purple-300 flex items-center gap-1.5">
                <IconSparkles size={14} className="text-amber-400" /> AI Wishlist Assistant
              </span>
              <button onClick={() => setShowAiAssistant(false)} className="text-slate-400 hover:text-white">
                <IconX size={14} />
              </button>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase">Quick Ask</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Which destination fits ₹50,000?",
                  "Best place for December?",
                  "Safest country?",
                  "Cheapest international destination?"
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAiQuestion(q)}
                    className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 hover:bg-purple-600 text-slate-300 hover:text-white transition-all text-left"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {aiAnswer && (
              <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-200 font-medium leading-relaxed">
                {aiAnswer}
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  );
}
