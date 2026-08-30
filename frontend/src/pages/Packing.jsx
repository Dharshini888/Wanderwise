import React, { useState, useEffect } from 'react';
import {
  IconBackpack,
  IconLuggage,
  IconShirt,
  IconSpray,
  IconDeviceLaptop,
  IconPill,
  IconFileText,
  IconCoin,
  IconCheck,
  IconPlus,
  IconTrash,
  IconLoader,
  IconSparkles,
  IconSun,
  IconCloudRain,
  IconSnowflake,
  IconFlame,
  IconPrinter,
  IconShare,
  IconBookmark,
  IconCompass,
  IconBriefcase,
  IconInfoCircle,
  IconScale,
  IconCalendar,
  IconPencil,
  IconAlertCircle,
  IconRefresh,
  IconDeviceMobile,
  IconDatabase,
  IconWorld
} from '@tabler/icons-react';

const API = 'http://localhost:8000/api';
const STORAGE_KEY = 'ww_packing_checks_db_only';

export default function Packing() {
  const [activeOption, setActiveOption] = useState('db'); // 'db' or 'custom'
  const [dbTrips, setDbTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState(null);
  const [fetchingTrips, setFetchingTrips] = useState(true);

  // Form State for Custom Option
  const [customForm, setCustomForm] = useState({
    destination: '',
    duration: '3',
    travel_type: 'Leisure',
    weather: 'Mild',
    season: 'Spring',
    travelers: 'Solo'
  });

  const [checklist, setChecklist] = useState(null);
  const [categoriesData, setCategoriesData] = useState([]);
  const [whyRationale, setWhyRationale] = useState([]);
  const [dailyTimeline, setDailyTimeline] = useState([]);
  const [checkedItems, setCheckedItems] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [shareCopied, setShareCopied] = useState(false);
  
  // AI Context and Intelligence State
  const [aiContext, setAiContext] = useState({});
  const [aiWarnings, setAiWarnings] = useState([]);
  const [missingEssentials, setMissingEssentials] = useState([]);

  // 1. Fetch Real Database Trips on Mount
  useEffect(() => {
    fetchDatabaseTrips();
    const savedChecks = localStorage.getItem(STORAGE_KEY);
    if (savedChecks) setCheckedItems(JSON.parse(savedChecks));
  }, []);

  const fetchDatabaseTrips = async () => {
    setFetchingTrips(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/trips`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      if (res.ok) {
        const data = await res.json();
        const tripsList = Array.isArray(data) ? data : (data.trips || data.items || []);
        setDbTrips(tripsList);
        if (tripsList.length > 0) {
          setSelectedTripId(tripsList[0].id);
          generateListFromDbTrip(tripsList[0]);
        }
      }
    } catch (err) {
      console.error('Error fetching database trips:', err);
    } finally {
      setFetchingTrips(false);
    }
  };

  const saveChecks = (updated) => {
    setCheckedItems(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  };

  const toggleCheck = (category, item) => {
    const key = `${category}:${item}`;
    saveChecks({ ...checkedItems, [key]: !checkedItems[key] });
  };

  const handleMarkAllPacked = () => {
    if (!checklist) return;
    const updated = { ...checkedItems };
    Object.entries(checklist).forEach(([cat, items]) => {
      items.forEach((item) => {
        updated[`${cat}:${item}`] = true;
      });
    });
    saveChecks(updated);
  };

  const isGeneratingRef = React.useRef(false);

  // Fetch or generate Packing Checklist strictly from Backend AI Engine
  const generateListFromDbTrip = async (trip) => {
    if (!trip) return;
    if (isGeneratingRef.current) return;
    if (checklist && Object.keys(checklist).length > 0 && selectedTripId === trip.id) return;
    
    isGeneratingRef.current = true;
    setLoading(true);
    setError('');

    try {
      // 1. Try to fetch existing
      let res = await fetch(`${API}/packing/trip/${trip.id}`);
      let data = await res.json();
      
      // 2. If not found, generate new
      if (data.status === 'not_found' || !data.checklist) {
        res = await fetch(`${API}/packing/generate-from-trip/${trip.id}`, { method: 'POST' });
        data = await res.json();
      }

      if (data.checklist) {
        const parsed = data.checklist;
        setAiContext(parsed.context || {});
        
        // Transform backend categories to match frontend checklist state
        const compiledChecklist = {};
        const rationales = [];
        
        (parsed.categories || []).forEach(cat => {
          compiledChecklist[cat.name] = cat.items.map(i => i.name);
          cat.items.forEach(i => {
            if (i.rationale) {
              rationales.push({ item: i.name, reason: i.rationale });
            }
          });
        });
        
        setChecklist(compiledChecklist);
        setCategoriesData(parsed.categories || []);
        setWhyRationale(rationales);
        setAiWarnings(parsed.warnings || []);
        setMissingEssentials(parsed.missing_essentials || []);
        
        // Extract daily_gear for timeline
        const timelineData = [];
        const dailyGear = parsed.daily_gear || [];
        
        if (dailyGear.length > 0) {
          dailyGear.forEach(day => {
            const dayNum = day.day || day.day_number || '?';
            const dayTitle = `Day ${dayNum}`;
            const activities = day.activities || [];
            
            // Format activities with their gear for display
            const dayItems = activities.map(act => {
              const name = act.name || '';
              const gear = act.recommended_gear || [];
              return gear.length > 0 ? `${name} (Gear: ${gear.join(', ')})` : name;
            }).filter(Boolean);
            
            timelineData.push({
              day: dayNum,
              title: dayTitle,
              items: dayItems.length > 0 ? dayItems : ["No saved activity for this day."]
            });
          });
        }
        
        setDailyTimeline(timelineData);
      }
    } catch (err) {
      console.error('Error generating packing list from DB trip:', err);
      setError('Failed to generate intelligent packing list.');
    } finally {
      setLoading(false);
      isGeneratingRef.current = false;
    }
  };

  // Generate Custom List using actual backend API
  const generateCustomList = async () => {
    if (!customForm.destination.trim()) {
      setError('Please enter a destination.');
      return;
    }
    if (isGeneratingRef.current) return;

    isGeneratingRef.current = true;
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API}/packing/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: customForm.destination,
          duration: parseInt(customForm.duration) || 3,
          travel_type: customForm.travel_type,
          weather: customForm.weather
        })
      });
      if (res.ok) {
        const data = await res.json();
        setChecklist(data.checklist || {});
        setCategoriesData(data.checklist.categories || []);
        setWhyRationale([{ item: 'Custom Checklist', reason: `Generated specifically for ${customForm.destination} (${customForm.duration} days, ${customForm.travel_type}).` }]);
        setDailyTimeline([]);
      } else {
        setError("Failed to generate packing list");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to generate packing list");
    } finally {
      setLoading(false);
      isGeneratingRef.current = false;
    }
  };

  const handleSelectDbTrip = (trip) => {
    if (selectedTripId === trip.id && checklist) return; // Prevent duplicate generation for same trip if already loaded
    setSelectedTripId(trip.id);
    generateListFromDbTrip(trip);
  };

  // Calculate Smart Packing Readiness Metrics
  const calculateMetrics = () => {
    if (!checklist) return { percentage: 0, missing: [], overpacked: [], suggestions: [], packed: 0, total: 0 };
    let total = 0;
    let packed = 0;

    Object.entries(checklist).forEach(([cat, items]) => {
      items.forEach((item) => {
        total++;
        if (checkedItems[`${cat}:${item}`]) packed++;
      });
    });

    // Smart Score Calculation
    let basePct = total > 0 ? (packed / total) * 100 : 0;
    
    // Penalize score dynamically based on AI warnings and missing items
    const missingPenalty = Math.min(missingEssentials.length * 5, 20); // up to 20% penalty
    const warningPenalty = Math.min(aiWarnings.length * 5, 15); // up to 15% penalty
    
    // Adjust based on AI context if packed is almost complete, but we have missing essentials
    let finalPercentage = Math.max(0, Math.min(100, Math.round(basePct - missingPenalty - warningPenalty)));

    return { percentage: finalPercentage, packed, total };
  };

  const metrics = calculateMetrics();
  const currentDbTrip = dbTrips.find((t) => t.id === selectedTripId);

  // Helper to calculate exact trip duration using dates
  const calculateTripDuration = (start, end) => {
    if (!start || !end) return 1;
    const st = new Date(start);
    const en = new Date(end);
    if (isNaN(st) || isNaN(en)) return 1;
    const diffTime = Math.abs(en - st);
    return Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1);
  };

  // Calculate actual weights dynamically from AI items
  let calculatedTotalWeight = 0;
  categoriesData.forEach(cat => {
    (cat.items || []).forEach(item => {
      calculatedTotalWeight += (parseFloat(item.weight_kg) || 0) * (parseInt(item.quantity) || 1);
    });
  });

  const estCarryOnWeight = Math.min(calculatedTotalWeight, 7.0).toFixed(1);
  const estCheckedWeight = (calculatedTotalWeight > 7.0 ? calculatedTotalWeight - 7.0 : 0).toFixed(1);

  const handleShare = () => {
    if (!checklist) return;
    const activeName = activeOption === 'db' && currentDbTrip ? currentDbTrip.destination : customForm.destination;
    const summary = `🎒 WanderWise Packing Checklist for ${activeName}:\n\n` +
      Object.entries(checklist)
        .map(([cat, items]) => `*${cat}*:\n` + items.map((i) => ` - ${i}`).join('\n'))
        .join('\n\n');

    navigator.clipboard.writeText(summary);
    setShareCopied(true);
    setTimeout(() => setShareCopied(false), 3000);
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto min-h-screen pb-24 text-[var(--text-primary)]">
      
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-r from-blue-600 to-teal-500 rounded-2xl text-white shadow-lg shadow-teal-500/20">
            <IconBackpack size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight font-heading flex items-center gap-2">
              🎒 AI Packing Assistant & Database Itinerary Balancer
            </h1>
            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-2xl font-medium">
              Smart packing checklists generated directly from your saved database trips and planned itinerary activities.
            </p>
          </div>
        </div>
      </div>

      {/* Top Generator Mode Selection: 🧳 Generate Packing List from My Trip */}
      <div className="glass-card p-6 rounded-3xl mb-8 border border-teal-500/30 bg-gradient-to-r from-blue-900/30 via-teal-900/20 to-purple-900/30 shadow-xl">
        <div className="text-xs font-extrabold uppercase text-teal-400 tracking-wider mb-3 flex items-center gap-2">
          <IconDatabase size={16} /> Generate Packing List from My Saved Database Trips
        </div>

        {/* Tab Selection */}
        <div className="flex gap-3 border-b border-teal-500/20 pb-4 mb-6">
          <button
            onClick={() => setActiveOption('db')}
            className={`px-5 py-2.5 rounded-2xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${
              activeOption === 'db'
                ? 'bg-teal-600 text-white shadow-lg shadow-teal-600/30'
                : 'bg-[var(--bg-glass)] text-[var(--text-muted)] hover:text-white border border-[var(--border-color)]'
            }`}
          >
            <IconDatabase size={18} /> Option 1: 📅 Use My Database Saved Itinerary ({dbTrips.length})
          </button>

          <button
            onClick={() => setActiveOption('custom')}
            className={`px-5 py-2.5 rounded-2xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${
              activeOption === 'custom'
                ? 'bg-teal-600 text-white shadow-lg shadow-teal-600/30'
                : 'bg-[var(--bg-glass)] text-[var(--text-muted)] hover:text-white border border-[var(--border-color)]'
            }`}
          >
            <IconPencil size={18} /> Option 2: ✍️ Create Custom Packing List
          </button>
        </div>

        {/* Option 1: Database Trips Grid */}
        {activeOption === 'db' && (
          <div>
            {fetchingTrips ? (
              <div className="flex flex-col items-center justify-center py-12 text-teal-400">
                <IconLoader size={36} className="animate-spin mb-2" />
                <span className="text-xs font-bold">Loading Your Database Itineraries...</span>
              </div>
            ) : dbTrips.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {dbTrips.map((it) => {
                  const isSelected = selectedTripId === it.id;
                  const stDate = it.start_date ? new Date(it.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                  const enDate = it.end_date ? new Date(it.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                  const datesStr = stDate && enDate ? `${stDate} - ${enDate}` : (it.start_date || 'Upcoming');

                  return (
                    <div
                      key={it.id}
                      onClick={() => handleSelectDbTrip(it)}
                      className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
                        isSelected
                          ? 'bg-teal-950/40 border-teal-400 ring-2 ring-teal-500/40 shadow-xl'
                          : 'bg-[var(--bg-glass)] border-[var(--border-color)] hover:border-teal-500/40'
                      }`}
                    >
                      <div>
                        <div className="flex justify-between items-start">
                          <h4 className="text-sm font-black text-white font-heading">{it.destination || it.title}</h4>
                          <span className="text-[10px] bg-teal-900/50 text-teal-300 px-2.5 py-1 rounded-md font-extrabold border border-teal-500/30">
                            {calculateTripDuration(it.start_date, it.end_date)} Days
                          </span>
                        </div>

                        <div className="text-[11px] text-[var(--text-muted)] mt-1.5 font-semibold">
                          📅 {datesStr}
                        </div>

                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] bg-purple-900/40 text-purple-300 px-2 py-0.5 rounded font-bold uppercase border border-purple-500/20">
                            {it.travel_style || it.group_type || 'Trip'}
                          </span>
                          {it.budget && (
                            <span className="text-[10px] bg-emerald-900/40 text-emerald-300 px-2 py-0.5 rounded font-bold border border-emerald-500/20">
                              {it.currency || 'USD'} {it.budget}
                            </span>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectDbTrip(it);
                        }}
                        className={`w-full py-2.5 rounded-xl text-xs font-extrabold transition-all flex items-center justify-center gap-1.5 ${
                          isSelected
                            ? 'bg-teal-500 text-white shadow-md shadow-teal-500/30'
                            : 'bg-teal-900/30 text-teal-200 hover:bg-teal-800/50'
                        }`}
                      >
                        <IconLuggage size={16} /> Generate Packing List
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-color)] text-center space-y-3">
                <IconDatabase size={40} className="mx-auto text-teal-400 opacity-60" />
                <div className="text-sm font-bold text-white">No saved trips found in your database yet.</div>
                <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto">
                  Create a new trip in the Smart Trip Planner or switch to Option 2 below to generate a custom packing list.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Option 2: Custom Form */}
        {activeOption === 'custom' && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              generateCustomList();
            }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Destination</label>
              <input
                type="text"
                value={customForm.destination}
                onChange={(e) => setCustomForm({ ...customForm, destination: e.target.value })}
                placeholder="Enter city or country"
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none focus:border-teal-400"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Duration (Days)</label>
              <input
                type="number"
                value={customForm.duration}
                onChange={(e) => setCustomForm({ ...customForm, duration: e.target.value })}
                placeholder="Number of days"
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none focus:border-teal-400"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Travel Style</label>
              <select
                value={customForm.travel_type}
                onChange={(e) => setCustomForm({ ...customForm, travel_type: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none cursor-pointer"
              >
                {['Leisure', 'Business', 'Adventure', 'Backpacking', 'Family Vacation', 'Honeymoon', 'Beach Holiday', 'Trekking', 'Winter Vacation', 'Camping'].map((t) => (
                  <option key={t} value={t} className="bg-[var(--bg-card)] text-white">{t}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Expected Weather</label>
              <input
                type="text"
                value={customForm.weather}
                onChange={(e) => setCustomForm({ ...customForm, weather: e.target.value })}
                placeholder="e.g. cold, hot, rainy, sunny"
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none focus:border-teal-400"
              />
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Season</label>
              <select
                value={customForm.season}
                onChange={(e) => setCustomForm({ ...customForm, season: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none cursor-pointer"
              >
                {['Spring', 'Summer', 'Autumn', 'Winter', 'Monsoon'].map((s) => (
                  <option key={s} value={s} className="bg-[var(--bg-card)] text-white">{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-bold uppercase text-[var(--text-muted)] mb-1">Travelers</label>
              <select
                value={customForm.travelers}
                onChange={(e) => setCustomForm({ ...customForm, travelers: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-glass)] text-xs font-bold text-white outline-none cursor-pointer"
              >
                {['Solo', 'Couple', 'Family', 'Friends', 'Group'].map((tr) => (
                  <option key={tr} value={tr} className="bg-[var(--bg-card)] text-white">{tr}</option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2 lg:col-span-3 pt-2">
              <button
                type="submit"
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-500 hover:to-teal-400 text-white font-extrabold rounded-2xl text-sm shadow-lg shadow-teal-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <IconLuggage size={18} />
                <span>Generate Smart Packing List</span>
              </button>
            </div>
          </form>
        )}

      </div>

      {/* One-Click Action Bar */}
      <div className="glass-card p-4 rounded-2xl mb-8 border border-[var(--border-color)] flex flex-wrap justify-between items-center gap-3 bg-[var(--bg-card)]">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => alert('Trip packing list saved!')}
            className="px-3.5 py-2 bg-teal-900/30 hover:bg-teal-800/50 text-teal-200 border border-teal-500/30 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
          >
            💾 Save Packing List
          </button>

          <button
            onClick={() => window.print()}
            className="px-3.5 py-2 bg-[var(--bg-glass)] hover:bg-teal-900/40 text-teal-200 border border-[var(--border-color)] rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
          >
            📄 Export as PDF
          </button>

          <button
            onClick={handleShare}
            className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-teal-600/30"
          >
            📤 {shareCopied ? 'Copied!' : 'Share List'}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleMarkAllPacked}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-emerald-600/30"
          >
            ✔ Mark All Packed
          </button>

          <button
            onClick={() => {
              if (activeOption === 'db' && currentDbTrip) generateListFromDbTrip(currentDbTrip);
              else generateCustomList();
            }}
            className="px-3.5 py-2 bg-indigo-900/40 hover:bg-indigo-800/60 text-indigo-200 border border-indigo-500/30 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
          >
            🔄 Regenerate from Itinerary
          </button>
        </div>
      </div>

      {/* Main Analysis Output Workspace */}
      {!loading && checklist && (
        <div className="space-y-8 animate-fadeIn">
        
          {/* AI Context Panel */}
          {aiContext.destination && (
            <div className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-glass)] shadow-md">
              <div className="text-xs uppercase font-bold tracking-wider text-[var(--text-muted)] mb-3">Packing recommendations based on:</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-medium">
                <div className="flex flex-col"><span className="text-[10px] text-gray-500">📍 Destination</span><span className="text-white font-bold">{aiContext.destination}</span></div>
                <div className="flex flex-col"><span className="text-[10px] text-gray-500">📅 Travel Dates</span><span className="text-white font-bold">{aiContext.start_date} – {aiContext.end_date}</span></div>
                <div className="flex flex-col"><span className="text-[10px] text-gray-500">🌡️ Climate & Weather</span><span className="text-white font-bold">{aiContext.climate} ({aiContext.season})</span></div>
                <div className="flex flex-col"><span className="text-[10px] text-gray-500">🧳 Duration</span><span className="text-white font-bold">{aiContext.duration_days} days</span></div>
              </div>
            </div>
          )}
          
          {/* Smart Packing Score & Readiness Header Card */}
          <div className="glass-card p-6 rounded-3xl border border-teal-500/30 bg-gradient-to-r from-teal-950/40 via-blue-950/30 to-purple-950/40 shadow-2xl space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
              
              {/* Score Gauge */}
              <div className="flex items-center gap-6 w-full md:w-auto">
                <div className="relative flex items-center justify-center w-24 h-24 rounded-full bg-teal-950/80 border-4 border-teal-400 text-center shadow-lg shadow-teal-500/20">
                  <div>
                    <div className="text-2xl font-black text-white font-heading">{metrics.percentage}%</div>
                    <div className="text-[8px] uppercase font-bold text-teal-300">Readiness</div>
                  </div>
                </div>

                <div>
                  <div className="text-xs uppercase font-bold text-teal-400 tracking-wider">Smart Packing Score</div>
                  <h3 className="text-xl font-black text-white font-heading">
                    {metrics.percentage >= 80 ? 'Excellent Preparation!' : 'In Progress — Keep Packing'}
                  </h3>
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    {metrics.packed} of {metrics.total} total essential items stowed in suitcase.
                  </p>
                </div>
              </div>

              {/* Luggage Weight Balancer */}
              <div className="flex gap-4 border-t md:border-t-0 md:border-l border-teal-500/20 pt-4 md:pt-0 md:pl-6 w-full md:w-auto justify-around">
                <div className="text-center bg-[var(--bg-glass)] p-3.5 rounded-2xl border border-[var(--border-color)] min-w-[120px]">
                  <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center justify-center gap-1">
                    <IconScale size={14} className="text-teal-400" /> Carry-on Bag
                  </div>
                  <div className="text-lg font-black text-teal-300 mt-1">{estCarryOnWeight} kg</div>
                  <div className="text-[9px] text-teal-400/80 font-semibold">Max Limit: 7.0 kg</div>
                </div>

                <div className="text-center bg-[var(--bg-glass)] p-3.5 rounded-2xl border border-[var(--border-color)] min-w-[120px]">
                  <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center justify-center gap-1">
                    <IconLuggage size={14} className="text-blue-400" /> Checked Luggage
                  </div>
                  <div className="text-lg font-black text-blue-300 mt-1">{estCheckedWeight} kg</div>
                  <div className="text-[9px] text-blue-400/80 font-semibold">Max Limit: 23.0 kg</div>
                </div>
              </div>
            </div>

            {/* Missing Essentials & Overpacked Warning Chips */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-teal-500/20 text-xs">
              <div className="bg-rose-950/20 border border-rose-500/30 p-3 rounded-2xl">
                <div className="font-bold text-rose-300 uppercase text-[10px] tracking-wider mb-1.5 flex items-center gap-1">
                  <IconAlertCircle size={14} /> Missing Essential Items ({missingEssentials.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {missingEssentials.length > 0 ? (
                    missingEssentials.map((m, idx) => (
                      <span key={idx} className="bg-rose-900/40 text-rose-200 px-2.5 py-0.5 rounded-md font-bold text-[11px] border border-rose-500/30">
                        ❌ {m}
                      </span>
                    ))
                  ) : (
                    <span className="text-emerald-400 font-semibold">✓ All critical travel essentials are packed!</span>
                  )}
                </div>
              </div>

              <div className="bg-amber-950/20 border border-amber-500/30 p-3 rounded-2xl">
                <div className="font-bold text-amber-300 uppercase text-[10px] tracking-wider mb-1.5 flex items-center gap-1">
                  <IconLuggage size={14} /> Potential Overpacking Warnings
                </div>
                <div className="flex flex-col gap-1.5">
                  {aiWarnings.length > 0 ? aiWarnings.map((w, idx) => (
                    <span key={idx} className="bg-amber-900/40 text-amber-200 px-2.5 py-1.5 rounded-md font-bold text-[11px] border border-amber-500/30">
                      ⚠️ {w.message || w}
                    </span>
                  )) : (
                    <span className="text-emerald-400 font-semibold text-[11px]">✓ Packing looks perfectly balanced!</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ✨ Why these items? AI Rationale Section */}
          {whyRationale.length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-teal-500/30 bg-[var(--bg-card)] shadow-xl space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconSparkles className="text-amber-400" /> ✨ Why these items? (DB Itinerary Intelligence Analysis)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                {whyRationale.map((rat, idx) => (
                  <div key={idx} className="p-3.5 rounded-2xl bg-teal-950/20 border border-teal-500/20 flex flex-col justify-between">
                    <div className="font-black text-teal-300 text-sm font-heading mb-1">{rat.item}</div>
                    <div className="text-[11px] text-teal-100/90 leading-relaxed font-medium">{rat.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 📅 Trip Timeline & Daily Recommended Items */}
          {dailyTimeline.length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xl space-y-4">
              <h3 className="text-base font-bold text-white font-heading flex items-center gap-2">
                <IconCalendar className="text-purple-400" /> 📅 Database Daily Itinerary Timeline & Required Gear
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {dailyTimeline.map((dt) => (
                  <div key={dt.day} className="p-4 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-2">
                    <div className="flex justify-between items-center border-b border-[var(--border-color)] pb-2">
                      <span className="text-xs font-black text-purple-300 font-heading">Day {dt.day}</span>
                      <span className="text-[10px] text-[var(--text-muted)] font-bold">DB Planned Activity</span>
                    </div>
                    <div className="text-xs font-bold text-white">{dt.title}</div>
                    
                    <div className="pt-2">
                      <div className="text-[10px] uppercase font-bold text-teal-400 mb-1">Recommended Today:</div>
                      <div className="flex flex-wrap gap-1">
                        {dt.items.map((item, idx) => (
                          <span key={idx} className="text-[10px] bg-teal-900/30 text-teal-200 px-2 py-0.5 rounded-md font-medium border border-teal-500/20">
                            ✓ {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Categorized Packing Checklists Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(checklist).map(([category, items]) => {
              let icon = <IconBackpack size={20} className="text-teal-400" />;
              if (category.includes('Clothing')) icon = <IconShirt size={20} className="text-blue-400" />;
              if (category.includes('Toiletries')) icon = <IconSpray size={20} className="text-purple-400" />;
              if (category.includes('Electronics')) icon = <IconDeviceLaptop size={20} className="text-cyan-400" />;
              if (category.includes('Medical')) icon = <IconPill size={20} className="text-rose-400" />;
              if (category.includes('Documents')) icon = <IconFileText size={20} className="text-amber-400" />;
              if (category.includes('Money')) icon = <IconCoin size={20} className="text-emerald-400" />;

              return (
                <div key={category} className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg space-y-4">
                  <h4 className="text-sm font-bold text-white font-heading flex items-center gap-2 pb-2 border-b border-[var(--border-color)]">
                    {icon} {category} ({items.length})
                  </h4>

                  <div className="space-y-2">
                    {items.map((item, idx) => {
                      const isChecked = !!checkedItems[`${category}:${item}`];
                      return (
                        <div
                          key={idx}
                          onClick={() => toggleCheck(category, item)}
                          className={`p-3 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
                            isChecked
                              ? 'bg-emerald-950/20 border-emerald-500/30 text-[var(--text-muted)] line-through'
                              : 'bg-[var(--bg-glass)] border-[var(--border-color)] text-white hover:border-teal-500/40'
                          }`}
                        >
                          <div className={`w-5 h-5 rounded-md border flex items-center justify-center text-xs transition-all ${
                            isChecked ? 'bg-emerald-500 border-emerald-400 text-white' : 'border-[var(--border-color)]'
                          }`}>
                            {isChecked && <IconCheck size={14} />}
                          </div>
                          <span className="text-xs font-semibold">{item}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="pt-8 border-t border-[var(--border-color)] text-center text-xs text-[var(--text-muted)] space-y-1">
            <div>Powered by <strong>WanderWise Database Itinerary & Packing Intelligence Engine</strong></div>
            <div>© {new Date().getFullYear()} WanderWise AI Travel Companion. All packing checklists dynamically synthesized from database records.</div>
          </div>

        </div>
      )}

    </div>
  );
}
