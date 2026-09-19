import { useState, useEffect } from 'react';
import { IconSparkles } from '@tabler/icons-react';
import api from '../../api/axios';

export default function PersonalizedWidget({ trips }) {
  const [recs, setRecs] = useState([]);
  const [photos, setPhotos] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trips || trips.length === 0) { setLoading(false); return; }
    const dests = trips.map(t => (t.destination || '').split(',')[0]).filter(Boolean);
    const cacheKey = `personalized_${dests.join('_')}`;

    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try { setRecs(JSON.parse(cached)); setLoading(false); } catch (_) {}
    }

    const fetchRecs = async () => {
      try {
        const res = await api.post('/api/recommendations/personalized', { past_destinations: dests });
        const data = res.data;
        const list = data.recommendations || [];
        if (list.length > 0) {
          setRecs(list);
          localStorage.setItem(cacheKey, JSON.stringify(list));
        }
      } catch (e) {}
      setLoading(false);
    };
    fetchRecs();
  }, [trips]);

  useEffect(() => {
    if (!recs.length) return;
    recs.forEach(async (r) => {
      if (!r.destination || photos[r.destination]) return;
      try {
        const res = await fetch(
          `https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=400&titles=${encodeURIComponent(r.destination)}&origin=*`
        );
        const data = await res.json();
        const pages = data.query?.pages || {};
        const page = Object.values(pages)[0];
        if (page?.thumbnail?.source) {
          setPhotos(prev => ({ ...prev, [r.destination]: page.thumbnail.source }));
        }
      } catch (_) {}
    });
  }, [recs]);

  if (loading) return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <div className="w-5 h-5 rounded-full border-2 border-[var(--color-primary-500)] border-t-transparent animate-spin"></div>
        <span>Generating custom suggestions...</span>
      </div>
    </div>
  );
  if (!recs || recs.length === 0) return null;

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <div>
        <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5">
          Curated For You
        </h3>
        <p className="text-xs text-[var(--text-muted)] flex items-center gap-1">
          <IconSparkles size={14} className="text-amber-500 animate-pulse" /> Travel history matching
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {recs.slice(0, 3).map((r, i) => (
          <div key={i} className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <div className="h-20 w-full relative bg-slate-200">
              {photos[r.destination] && (
                <img
                  src={photos[r.destination]}
                  alt={r.destination}
                  className="w-full h-full object-cover"
                  onError={e => { e.target.style.display = 'none'; }}
                />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-2 left-3 right-3 flex justify-between items-end">
                <div className="text-xs font-bold text-white tracking-wide font-heading">{r.destination}</div>
                <span className="text-[9px] bg-white/25 text-white backdrop-blur-sm px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">{r.vibe}</span>
              </div>
            </div>
            <div className="p-3 space-y-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-[var(--color-primary-600)] dark:text-blue-400 block">
                Recommended because:
              </span>
              <ul className="text-[11px] text-[var(--text-secondary)] space-y-0.5 font-medium">
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span> Similar climate & seasonal timing
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span> Matches your budget tier
                </li>
                <li className="flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span> {r.reason || 'Based on your travel style'}
                </li>
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
