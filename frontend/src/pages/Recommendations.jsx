import { useState, useEffect } from 'react';
import {
  IconSparkles,
  IconSearch,
  IconMapPin,
  IconStar,
  IconHeart,
  IconCompass,
  IconAlertCircle,
  IconLoader,
  IconCheck,
  IconExternalLink,
  IconClock,
  IconSun,
  IconBus
} from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

const CATEGORIES = [
  "All",
  "Top Attractions",
  "Hidden Gems",
  "Cafes",
  "Restaurants",
  "Nature Spots",
  "Shopping Places",
  "Local Experiences",
  "Nightlife",
  "Historical Places",
  "AI Recommended Places"
];

export default function Recommendations() {
  const [destination, setDestination] = useState('');
  const [interests, setInterests] = useState('');
  const [recsData, setRecsData] = useState(null);
  const [activeCategory, setActiveCategory] = useState('All');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [favorites, setFavorites] = useState([]);
  const token = localStorage.getItem('token');

  const fetchRecs = async (e) => {
    if (e) e.preventDefault();
    if (!destination.trim()) return;
    setLoading(true); setError(''); setRecsData(null);
    try {
      const res = await fetch(`${API}/recommendations/places`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          destination,
          interests: interests || 'sightseeing, local food'
        })
      });
      const data = await res.json();
      if (res.ok) {
        setRecsData(data);
      } else {
        setError(data.detail || 'Could not fetch recommendations');
      }
    } catch (_) {
      setError('Network error. Please make sure backend is running.');
    }
    setLoading(false);
  };

  const toggleFavorite = async (item) => {
    const name = item.name;
    const isFav = favorites.includes(name);
    setFavorites(prev => isFav ? prev.filter(i => i !== name) : [...prev, name]);

    if (!isFav && token) {
      try {
        await fetch(`${API}/wishlist/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            title: item.name,
            destination: destination || item.address || '',
            category: item.category || 'Attraction',
            notes: item.description || ''
          })
        });
      } catch (_) {}
    }
  };

  // Group items by category or filter flat list
  const getDisplayItems = () => {
    if (!recsData) return [];
    if (recsData.categories && Object.keys(recsData.categories).length > 0) {
      if (activeCategory === 'All') {
        let all = [];
        Object.entries(recsData.categories).forEach(([cat, items]) => {
          if (Array.isArray(items)) {
            items.forEach(it => all.push({ ...it, categoryName: cat }));
          }
        });
        return all;
      }
      const catItems = recsData.categories[activeCategory] || [];
      return catItems.map(it => ({ ...it, categoryName: activeCategory }));
    }
    return recsData.recommendations || [];
  };

  const itemsToRender = getDisplayItems();

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconSparkles className="text-amber-500 animate-pulse" size={32} /> AI Personalized Discoveries
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">
          Get tailor-made place recommendations ranked by your unique travel preferences.
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={fetchRecs} className="glass-card p-6 flex flex-col md:flex-row gap-4 items-end border-t-4 border-t-[var(--color-primary-500)]">
        <div className="flex-1 w-full">
          <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Where are you going?</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--text-muted)]">
              <IconMapPin size={18} />
            </span>
            <input 
              value={destination} 
              onChange={e => setDestination(e.target.value)} 
              placeholder="e.g. Ooty, Kyoto, Paris, New York" 
              required 
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/10 transition-all"
            />
          </div>
        </div>

        <div className="flex-1 w-full">
          <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Your Interests / Vibe</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--text-muted)]">
              <IconCompass size={18} />
            </span>
            <input 
              value={interests} 
              onChange={e => setInterests(e.target.value)} 
              placeholder="e.g. photography, tea gardens, historic temples, quiet cafes" 
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/10 transition-all"
            />
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading || !destination.trim()}
          className="btn btn-primary px-8 py-3 w-full md:w-auto font-semibold flex items-center justify-center gap-2 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <>
              <IconLoader className="animate-spin" size={18} />
              <span>Analyzing AI Match...</span>
            </>
          ) : (
            <>
              <IconSearch size={18} />
              <span>Generate Recommendations</span>
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-600 dark:text-red-400 text-sm font-semibold flex items-center gap-2">
          <IconAlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Category Tabs */}
      {recsData && (
        <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap border ${
                activeCategory === cat
                  ? 'bg-[var(--color-primary-600)] text-white border-[var(--color-primary-600)] shadow-md'
                  : 'bg-[var(--bg-card)] border-[var(--border-color)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Skeleton Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="glass-card p-6 flex flex-col gap-4 animate-pulse">
              <div className="h-6 bg-[var(--border-color)] rounded-lg w-3/4"></div>
              <div className="h-4 bg-[var(--border-color)] rounded-lg w-1/2"></div>
              <div className="h-16 bg-[var(--border-color)] rounded-xl w-full"></div>
              <div className="h-8 bg-[var(--border-color)] rounded-lg w-full mt-auto"></div>
            </div>
          ))}
        </div>
      )}

      {/* Recommendations Feed */}
      {!loading && recsData && (
        <div>
          {recsData.message && itemsToRender.length === 0 ? (
            <div className="glass-card p-12 text-center flex flex-col items-center justify-center gap-3">
              <span className="text-4xl">🗺️</span>
              <div className="text-base font-bold text-[var(--text-primary)]">{recsData.message}</div>
              <p className="text-xs text-[var(--text-muted)]">No recommendations available yet. Try another destination or interest.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {itemsToRender.map((r, i) => {
                const isFav = favorites.includes(r.name);
                const score = r.ai_match_score || 95;
                const reasons = r.match_reasons || ["✓ Matches Interests", "✓ Highly Recommended"];
                return (
                  <div key={i} className="glass-card p-6 flex flex-col justify-between hover:border-[var(--color-primary-400)] transition-all bg-[var(--bg-card)] group relative border border-[var(--border-color)] rounded-2xl shadow-sm hover:shadow-md">
                    
                    <div>
                      {/* Category & AI Match Badge */}
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-50 dark:bg-blue-950/30 text-[var(--color-primary-600)] dark:text-blue-400 px-2.5 py-1 rounded-full border border-blue-100 dark:border-blue-900">
                          {r.categoryName || r.category || 'Recommendation'}
                        </span>

                        <span className="text-[11px] font-extrabold bg-gradient-to-r from-amber-500 to-orange-500 text-white px-2.5 py-0.5 rounded-full shadow-sm flex items-center gap-1">
                          <IconSparkles size={12}/> AI Match {score}%
                        </span>
                      </div>

                      {/* Header */}
                      <div className="flex justify-between items-start gap-4 mb-2">
                        <div>
                          <h3 className="text-lg font-black text-[var(--text-primary)] tracking-wide font-heading group-hover:text-[var(--color-primary-600)] transition-colors">
                            {r.name}
                          </h3>
                          <div className="text-xs text-[var(--text-muted)] font-medium flex items-center gap-1 mt-1">
                            <IconMapPin size={14} className="text-blue-500 flex-shrink-0" />
                            <span className="truncate">{r.address || r.location || destination}</span>
                          </div>
                        </div>
                        <button 
                          onClick={() => toggleFavorite(r)}
                          className="p-2 rounded-full text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-all flex-shrink-0"
                          title={isFav ? "Remove from wishlist" : "Add to wishlist"}
                        >
                          <IconHeart size={20} fill={isFav ? "red" : "none"} className={isFav ? "text-red-500 scale-110" : "transition-transform group-hover:scale-110"} />
                        </button>
                      </div>

                      {/* Badges row */}
                      <div className="flex flex-wrap items-center gap-2 my-3">
                        {r.rating && (
                          <span className="flex items-center gap-1 text-xs font-bold bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900 px-2 py-0.5 rounded-md">
                            <IconStar size={12} fill="currentColor" /> {r.rating}
                          </span>
                        )}
                        {r.price_range && (
                          <span className="text-xs font-bold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 px-2 py-0.5 rounded-md">
                            {r.price_range} ({r.budget_badge || 'Standard'})
                          </span>
                        )}
                        {r.open_status && (
                          <span className="text-[10px] font-bold text-[var(--text-muted)] flex items-center gap-1 bg-[var(--bg-app)] px-2 py-0.5 rounded-md border border-[var(--border-color)]">
                            <IconClock size={12}/> {r.open_status}
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      <p className="text-xs sm:text-sm text-[var(--text-secondary)] leading-relaxed mb-4">{r.description}</p>
                      
                      {/* AI Match Reasons Checklist */}
                      {reasons && reasons.length > 0 && (
                        <div className="bg-[var(--bg-app)] p-3 rounded-xl border border-[var(--border-color)] mb-4 flex flex-col gap-1">
                          <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] tracking-wider">Why AI Recommends This</span>
                          {reasons.slice(0, 4).map((reason, idx) => (
                            <div key={idx} className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5">
                              <IconCheck size={12} className="flex-shrink-0" /> {reason.replace(/^✓\s*/, '')}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Footer Actions & Metadata */}
                    <div className="pt-4 border-t border-[var(--border-color)] flex items-center justify-between">
                      <div className="text-[11px] text-[var(--text-muted)] font-medium">
                        {r.distance ? `📍 ${r.distance}` : 'Center location'}
                      </div>

                      <a 
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.name + ' ' + (r.address || destination))}`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-outline text-xs py-1.5 px-3 flex items-center gap-1 font-semibold"
                      >
                        <IconExternalLink size={14} /> View Map
                      </a>
                    </div>
                    
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Empty State when no search conducted yet */}
      {!loading && !recsData && (
        <div className="glass-card p-16 text-center flex flex-col items-center justify-center gap-4 border-dashed border-2">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-full flex items-center justify-center text-blue-500">
            <span className="text-4xl animate-bounce">✨</span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--text-primary)] font-heading mb-2">Ready to explore?</h3>
            <p className="text-sm text-[var(--text-muted)] max-w-md mx-auto leading-relaxed">
              Tell us where you're going and what you enjoy.<br/>
              We'll create personalized recommendations, restaurants, cafes, hidden gems, transport, weather insights, and a complete AI itinerary.
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
