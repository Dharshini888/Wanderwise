import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  IconBook, IconSearch, IconSparkles, IconCalendar, IconMapPin, IconClock,
  IconCurrencyRupee, IconSun, IconCamera, IconTrophy, IconShare, IconDownload,
  IconArrowLeft, IconCheck, IconStar, IconCar, IconWalk, IconFlame,
  IconLeaf, IconHeart, IconSend, IconChecklist, IconShieldCheck, IconPhotoOff,
  IconBuilding
} from '@tabler/icons-react';
import InteractiveTransitMap from '../components/transit/InteractiveTransitMap';

const API = 'http://localhost:8000/api';

export default function Journal() {
  const { tripId: paramTripId } = useParams();

  const [journals, setJournals] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState(paramTripId ? parseInt(paramTripId) : null);
  const [detailData, setDetailData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Search & AI Memory Query state
  const [searchQuery, setSearchQuery] = useState('');
  const [aiMemoryQuery, setAiMemoryQuery] = useState('');
  const [aiMemoryResult, setAiMemoryResult] = useState(null);
  const [aiMemoryLoading, setAiMemoryLoading] = useState(false);

  // Mood & Reflection state
  const [selectedMood, setSelectedMood] = useState('😊 Amazing');

  const token = localStorage.getItem('token');

  const getHeaders = () => {
    const h = {};
    if (token && token !== 'null' && token !== 'undefined') {
      h.Authorization = `Bearer ${token}`;
    }
    return h;
  };

  // Fetch all journal trips
  const fetchJournals = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/journal/trips`, {
        headers: getHeaders()
      });
      if (res.ok) {
        setJournals(await res.json());
      }
    } catch (_) {}
    setLoading(false);
  };

  const [detailLoading, setDetailLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  // Fetch detailed journal payload
  const fetchJournalDetails = async (id) => {
    console.log("Journal ID requested:", id);
    setDetailLoading(true);
    setNotFound(false);
    setDetailData(null);
    try {
      const res = await fetch(`${API}/journal/details/${id}`, {
        headers: getHeaders()
      });
      console.log("Backend response status:", res.status);
      if (res.ok) {
        const data = await res.json();
        console.log("Backend response data:", data);
        setDetailData(data);
        if (data.mood) setSelectedMood(data.mood);
      } else {
        console.warn(`Trip #${id} returned status ${res.status}`);
        setNotFound(true);
      }
    } catch (err) {
      console.error("Error fetching journal details:", err);
      setNotFound(true);
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchJournals();
  }, []);

  useEffect(() => {
    if (selectedTripId) {
      fetchJournalDetails(selectedTripId);
    } else {
      setDetailData(null);
    }
  }, [selectedTripId]);

  // AI Memory Search Handler
  const handleAiMemorySearch = async (e) => {
    e?.preventDefault();
    if (!aiMemoryQuery.trim()) return;
    setAiMemoryLoading(true);
    setAiMemoryResult(null);
    try {
      const res = await fetch(`${API}/journal/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ query: aiMemoryQuery })
      });
      if (res.ok) {
        setAiMemoryResult(await res.json());
      }
    } catch (_) {}
    setAiMemoryLoading(false);
  };

  const filteredJournals = journals.filter(j =>
    j.destination.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.travel_mode.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen pb-16 space-y-8">
      
      {/* Header Banner */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-indigo-950/40 border border-purple-500/30 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 bg-purple-600/30 rounded-2xl border border-purple-400/30 text-purple-300">
                <IconBook size={28} />
              </div>
              <div>
                <span className="text-xs uppercase tracking-widest text-purple-400 font-bold">Memory Vault</span>
                <h1 className="text-3xl font-black text-white font-heading">AI Travel Journal</h1>
              </div>
            </div>
            <p className="text-sm text-purple-200/80 max-w-2xl">
              Clean, non-redundant travel memories. Review authentic itineraries, interactive route maps, photo galleries, expenses, and AI recommendations.
            </p>
          </div>

          {selectedTripId && (
            <button
              onClick={() => setSelectedTripId(null)}
              className="flex items-center gap-2 bg-purple-900/50 hover:bg-purple-800/60 text-purple-200 px-4 py-2.5 rounded-xl border border-purple-500/30 font-bold text-xs transition-all"
            >
              <IconArrowLeft size={18} /> Back to All Journals
            </button>
          )}
        </div>
      </div>

      {/* VIEW 1: JOURNAL HOME GRID */}
      {!selectedTripId ? (
        <div className="space-y-8">
          
          {/* AI Memory Search & Keyword Search Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* AI Conversational Memory Box */}
            <div className="md:col-span-2 glass-card p-6 rounded-2xl border border-purple-500/30 bg-purple-950/20 space-y-4">
              <div className="flex items-center gap-2 text-purple-300 font-bold text-sm">
                <IconSparkles className="text-amber-300" size={20} />
                <span>Ask AI Travel Memory</span>
              </div>
              <form onSubmit={handleAiMemorySearch} className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. 'Show me the restaurant I visited in Erode' or 'Which trip had lowest budget?'"
                  className="flex-1 bg-[var(--bg-glass)] border border-purple-500/30 rounded-xl px-4 py-3 text-xs text-white placeholder-purple-300/50 outline-none focus:border-purple-400"
                  value={aiMemoryQuery}
                  onChange={(e) => setAiMemoryQuery(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={aiMemoryLoading}
                  className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-3 rounded-xl text-xs font-bold transition-all flex items-center gap-2"
                >
                  {aiMemoryLoading ? 'Searching...' : <><IconSend size={16} /> Ask AI</>}
                </button>
              </form>

              {aiMemoryResult && (
                <div className="p-4 rounded-xl bg-purple-900/40 border border-purple-400/30 text-xs text-purple-100 space-y-2 animate-fadeIn">
                  <div className="font-semibold text-purple-200">{aiMemoryResult.reply}</div>
                  {aiMemoryResult.matched_trip_id && (
                    <button
                      onClick={() => setSelectedTripId(aiMemoryResult.matched_trip_id)}
                      className="text-amber-300 underline font-bold hover:text-amber-200 block text-xs"
                    >
                      View Journal Entry →
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Keyword Search Filter */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] flex flex-col justify-between">
              <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Filter Journals</div>
              <div className="relative">
                <IconSearch className="absolute left-3 top-3 text-purple-400" size={18} />
                <input
                  type="text"
                  placeholder="Search Erode, Train, Beach..."
                  className="w-full bg-[var(--bg-glass)] border border-[var(--border-color)] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white outline-none focus:border-purple-400"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="text-[11px] text-purple-300/70 mt-3">
                Displaying {filteredJournals.length} completed travel journals
              </div>
            </div>

          </div>

          {/* Journal Trip Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredJournals.map((j) => (
              <div
                key={j.id}
                className="glass-card rounded-2xl border border-[var(--border-color)] overflow-hidden flex flex-col hover:border-purple-500/50 transition-all duration-300 group shadow-xl"
              >
                <div className="h-44 relative overflow-hidden">
                  <img
                    src={j.cover_image}
                    alt={j.destination}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-card)] via-transparent to-black/30" />
                  <div className="absolute top-3 left-3 bg-purple-900/80 backdrop-blur-md text-white text-[10px] font-bold px-3 py-1 rounded-full border border-purple-400/30">
                    📍 {j.origin} → {j.destination}
                  </div>
                  <div className="absolute top-3 right-3 bg-emerald-500/80 backdrop-blur-md text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                    <IconStar size={12} className="fill-current" /> {j.rating}
                  </div>
                </div>

                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div>
                    <h3 className="text-lg font-bold text-white font-heading group-hover:text-purple-300 transition-colors">
                      {j.title}
                    </h3>
                    <div className="text-xs text-[var(--text-muted)] flex items-center gap-2 mt-1">
                      <IconCalendar size={14} className="text-purple-400" /> {j.start_date}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 py-3 border-y border-[var(--border-color)] text-xs">
                    <div className="text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Duration</div>
                      <div className="font-bold text-white mt-0.5">{j.duration}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Budget Spent</div>
                      <div className="font-bold text-emerald-400 mt-0.5">₹{j.budget_spent.toLocaleString()}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Photos</div>
                      <div className="font-bold text-purple-300 mt-0.5">{j.photo_count} Photos</div>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedTripId(j.id)}
                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-2.5 rounded-xl text-xs shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    <IconBook size={16} /> View Travel Journal
                  </button>
                </div>
              </div>
            ))}
          </div>

        </div>
      ) : (
        /* VIEW 2: NON-REDUNDANT 12-STEP JOURNAL DETAIL PAGE */
        detailLoading ? (
          <div className="glass-card p-12 text-center rounded-3xl border border-purple-500/30 text-purple-200 font-bold text-sm">
            ⏳ Loading Journal Details...
          </div>
        ) : notFound || !detailData ? (
          <div className="glass-card p-12 text-center rounded-3xl border border-purple-500/30 space-y-4 animate-fadeIn">
            <div className="text-4xl">🗺️</div>
            <h2 className="text-2xl font-bold text-white font-heading">Trip Not Found</h2>
            <p className="text-xs text-purple-200">No travel journal entry recorded for trip #{selectedTripId} in your database.</p>
            <button
              onClick={() => setSelectedTripId(null)}
              className="bg-purple-600 hover:bg-purple-500 text-white font-bold px-6 py-2.5 rounded-xl text-xs inline-flex items-center gap-2 shadow-lg transition-all"
            >
              <IconArrowLeft size={16} /> Go Back to All Journals
            </button>
          </div>
        ) : (
          <div className="space-y-8 animate-fadeIn">
            
            {/* 1. Trip Overview (Hero Section) */}
            <div className="glass-card p-6 sm:p-8 rounded-3xl border border-purple-500/30 bg-gradient-to-br from-purple-950/40 via-indigo-950/20 to-purple-950/40 space-y-6">
              <div className="flex flex-wrap justify-between items-start gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold px-3 py-1 rounded-full uppercase flex items-center gap-1">
                      <IconCheck size={12} /> {detailData.status}
                    </span>
                    <span className="text-xs text-purple-300 font-medium">
                      📅 {detailData.date}
                    </span>
                    <span className="bg-purple-900/40 text-purple-300 border border-purple-500/30 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <IconShieldCheck size={12} className="text-emerald-400" /> Route Verified
                    </span>
                  </div>
                  <h2 className="text-3xl font-black text-white font-heading">
                    {detailData.origin} → {detailData.destination}
                  </h2>
                </div>

                <div className="bg-purple-900/40 p-3 rounded-2xl border border-purple-500/30 text-center">
                  <div className="text-2xl font-black text-amber-300">★★★★★</div>
                  <div className="text-[10px] text-purple-300">Trip Rating</div>
                </div>
              </div>

              {/* Concise Hero Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Duration</span>
                  <span className="text-sm font-extrabold text-white mt-0.5 block">{detailData.duration}</span>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Travel Mode</span>
                  <span className="text-sm font-extrabold text-purple-300 mt-0.5 block">{detailData.travel_mode}</span>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Distance</span>
                  <span className="text-sm font-extrabold text-white mt-0.5 block">{detailData.distance_km} km</span>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Total Expense</span>
                  <span className="text-sm font-extrabold text-emerald-400 mt-0.5 block">₹{detailData.total_expense.toLocaleString()}</span>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Weather</span>
                  <span className="text-sm font-extrabold text-blue-300 mt-0.5 block">{detailData.weather_summary}</span>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold block">Places Visited</span>
                  <span className="text-sm font-extrabold text-white mt-0.5 block">{detailData.visited_places.length} Places</span>
                </div>
              </div>
            </div>

            {/* 2. Interactive Route Map */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconMapPin className="text-purple-400" /> Interactive Route Map
              </h3>
              <InteractiveTransitMap
                origin={detailData.origin}
                destination={detailData.destination}
                markers={[
                  { pos: [detailData.map_data.origin_coords.lat, detailData.map_data.origin_coords.lon], label: `Origin: ${detailData.origin}` },
                  ...detailData.map_data.visited_stops.map(s => ({ pos: [s.lat, s.lon], label: `Stop: ${s.name}` })),
                  { pos: [detailData.map_data.dest_coords.lat, detailData.map_data.dest_coords.lon], label: `Destination: ${detailData.destination}` }
                ]}
              />
            </div>

            {/* 3. Journey Timeline */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconClock className="text-purple-400" /> Journey Timeline
              </h3>
              {detailData.timeline && detailData.timeline.length > 0 ? (
                <div className="relative border-l-2 border-purple-500/30 ml-4 space-y-4">
                  {detailData.timeline.map((step, idx) => (
                    <div key={idx} className="relative pl-6">
                      <div className="absolute -left-[17px] top-0 w-8 h-8 bg-purple-900 border-2 border-purple-400 rounded-full text-white flex items-center justify-center text-sm">
                        {step.emoji}
                      </div>
                      <div className="bg-[var(--bg-glass)] p-3.5 rounded-xl border border-[var(--border-color)] space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold text-white">{step.title}</span>
                          <span className="text-[10px] text-purple-300 font-bold bg-purple-900/40 px-2 py-0.5 rounded">{step.time}</span>
                        </div>
                        <p className="text-xs text-[var(--text-muted)]">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center bg-[var(--bg-glass)] rounded-xl text-xs text-purple-200/70">
                  No timeline steps recorded for this trip yet
                </div>
              )}
            </div>

            {/* 4. AI Travel Story */}
            <div className="glass-card p-6 rounded-2xl border border-purple-500/30 bg-purple-950/20 space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconSparkles className="text-amber-300" /> AI Travel Story
              </h3>
              <div className="p-5 rounded-2xl bg-purple-900/30 border border-purple-500/20 text-sm text-purple-100 leading-relaxed italic relative">
                <span className="text-4xl text-purple-400/40 absolute -top-2 left-2 font-serif font-black">“</span>
                <p className="pl-4 relative z-10">{detailData.ai_story}</p>
              </div>
            </div>

            {/* 5. Places Visited */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconChecklist className="text-emerald-400" /> Places Visited
              </h3>
              {detailData.visited_places && detailData.visited_places.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 text-xs">
                  {detailData.visited_places.map((placeName, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex items-center gap-2">
                      <IconCheck size={16} className="text-emerald-400 flex-shrink-0" />
                      <span className="text-white font-medium truncate">{placeName}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center bg-[var(--bg-glass)] rounded-xl text-xs text-purple-200/70">
                  No places visited recorded for this trip yet
                </div>
              )}
            </div>

            {/* 6. Photo Gallery */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconCamera className="text-purple-400" /> Photo Memories
              </h3>
              {detailData.photos && detailData.photos.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                  {detailData.photos.map((photo, idx) => (
                    <div key={idx} className="glass-card rounded-xl border border-[var(--border-color)] overflow-hidden group">
                      <div className="h-40 overflow-hidden relative">
                        <img
                          src={photo.url}
                          alt={photo.caption}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <span className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-md text-[10px] text-white px-2 py-0.5 rounded">
                          📍 {photo.location} • {photo.time}
                        </span>
                      </div>
                      <div className="p-3 text-xs text-purple-200 italic font-medium">
                        "{photo.caption}"
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center bg-[var(--bg-glass)] rounded-xl border border-[var(--border-color)] text-purple-200/70 text-xs flex flex-col items-center gap-2">
                  <IconPhotoOff size={32} className="text-purple-400" />
                  <span>No photos added for this trip yet</span>
                </div>
              )}
            </div>

            {/* 7. Expense Breakdown */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconCurrencyRupee className="text-emerald-400" /> Expense Breakdown
              </h3>
              {Object.keys(detailData.expense_breakdown || {}).length > 0 ? (
                <div className="space-y-2.5 text-xs">
                  {Object.entries(detailData.expense_breakdown).map(([cat, amt], idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex justify-between items-center">
                      <span className="text-white font-medium">{cat}</span>
                      <span className="font-bold text-emerald-400">₹{amt.toLocaleString()}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-[var(--border-color)] flex justify-between items-center font-extrabold text-sm text-white">
                    <span>Total</span>
                    <span className="text-emerald-400">₹{detailData.total_expense.toLocaleString()}</span>
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center bg-[var(--bg-glass)] rounded-xl text-xs text-purple-200/70">
                  No expenses recorded for this trip yet
                </div>
              )}
            </div>

            {/* 8. Travel Weather Card (Single non-redundant status) */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconSun className="text-amber-400" /> Travel Weather
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] block">Condition</span>
                  <span className="font-bold text-white mt-0.5 block">{detailData.travel_weather.condition}</span>
                </div>
                <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] block">Average Temp</span>
                  <span className="font-bold text-amber-300 mt-0.5 block">{detailData.travel_weather.avg_temp}</span>
                </div>
                <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] block">Rain Alert</span>
                  <span className="font-bold text-blue-300 mt-0.5 block">{detailData.travel_weather.rain}</span>
                </div>
                <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                  <span className="text-[10px] uppercase text-[var(--text-muted)] block">Travel Impact</span>
                  <span className="font-bold text-emerald-400 mt-0.5 block">{detailData.travel_weather.impact}</span>
                </div>
              </div>
            </div>

            {/* 9. Trip Statistics */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconTrophy className="text-purple-400" /> Trip Statistics
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center">
                  <IconCar size={20} className="mx-auto text-purple-400 mb-1" />
                  <div className="text-[10px] text-[var(--text-muted)]">Distance</div>
                  <div className="font-bold text-white mt-0.5">{detailData.statistics.distance_km} km</div>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center">
                  <IconWalk size={20} className="mx-auto text-emerald-400 mb-1" />
                  <div className="text-[10px] text-[var(--text-muted)]">Walking</div>
                  <div className="font-bold text-white mt-0.5">{detailData.statistics.walking_km} km</div>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center">
                  <IconFlame size={20} className="mx-auto text-orange-400 mb-1" />
                  <div className="text-[10px] text-[var(--text-muted)]">Calories</div>
                  <div className="font-bold text-white mt-0.5">{detailData.statistics.calories_burned} kcal</div>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center">
                  <IconLeaf size={20} className="mx-auto text-emerald-400 mb-1" />
                  <div className="text-[10px] text-[var(--text-muted)]">CO₂ Saved</div>
                  <div className="font-bold text-emerald-400 mt-0.5">{detailData.statistics.co2_saved_kg} kg</div>
                </div>
                <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center">
                  <IconClock size={20} className="mx-auto text-blue-400 mb-1" />
                  <div className="text-[10px] text-[var(--text-muted)]">Time Travelled</div>
                  <div className="font-bold text-white mt-0.5">{detailData.statistics.travel_time}</div>
                </div>
              </div>
            </div>

            {/* 10. Achievements */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconTrophy className="text-amber-300" /> Gamified Achievements
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                {detailData.achievements.map((ach, idx) => (
                  <div key={idx} className="p-4 rounded-2xl bg-gradient-to-br from-amber-500/10 to-purple-500/10 border border-amber-500/30 flex items-center gap-3">
                    <span className="text-2xl">{ach.title.split(' ')[0]}</span>
                    <div>
                      <div className="font-bold text-white">{ach.title.replace(/^[^\s]+\s/, '')}</div>
                      <div className="text-[10px] text-purple-200">{ach.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 11. Mood & Reflection */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconHeart className="text-rose-400" /> Mood & Reflection
              </h3>
              
              <div className="flex gap-2 flex-wrap mb-2">
                {['😊 Amazing', '🙂 Good', '😐 Average', '☹ Poor'].map(m => (
                  <button
                    key={m}
                    onClick={() => setSelectedMood(m)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                      selectedMood === m
                        ? 'bg-purple-600 text-white border-purple-400'
                        : 'bg-[var(--bg-glass)] text-purple-200 border-[var(--border-color)] hover:border-purple-400'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-1">
                  <span className="font-bold text-white block">What did you enjoy?</span>
                  <p className="text-purple-200">{detailData.reflection.favorite_moment}</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-1">
                  <span className="font-bold text-white block">What will you improve?</span>
                  <p className="text-purple-200">{detailData.reflection.what_to_improve}</p>
                </div>
              </div>
            </div>

            {/* 12. AI Recommended Next Destinations (Personalized preferences) */}
            <div className="glass-card p-6 rounded-2xl border border-purple-500/30 bg-purple-950/20 space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconSparkles className="text-amber-300" /> AI Recommended Next Destinations
              </h3>
              <p className="text-xs text-purple-200">
                Based on your travel preferences from this journey, you may also enjoy:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                {detailData.ai_recommendations.map((rec, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-purple-900/30 border border-purple-500/20 space-y-2">
                    <div className="font-bold text-white text-sm">{rec.name}</div>
                    <div className="text-[11px] text-purple-300 leading-relaxed">{rec.reason}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* 13. Share / Export Toolbar */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)] flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-bold text-white font-heading">Share / Export Journal</h4>
                <p className="text-xs text-[var(--text-muted)]">Export entry as PDF, Instagram Story, or shareable link.</p>
              </div>

              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={() => alert("PDF Export generated for " + detailData.destination)}
                  className="flex items-center gap-2 bg-purple-900/40 hover:bg-purple-800/60 text-purple-200 px-4 py-2 rounded-xl border border-purple-500/30 text-xs font-bold transition-all"
                >
                  <IconDownload size={16} /> Export PDF
                </button>
                <button
                  onClick={() => alert("Instagram Story layout ready!")}
                  className="flex items-center gap-2 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-lg transition-all"
                >
                  <IconShare size={16} /> Instagram Story
                </button>
              </div>
            </div>

          </div>
        )
      )}

    </div>
  );
}
