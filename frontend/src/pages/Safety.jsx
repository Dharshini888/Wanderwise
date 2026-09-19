import { useState, useEffect, useRef, useCallback } from 'react';
import {
  IconShieldCheck, IconSearch, IconLoader, IconAlertTriangle,
  IconPhone, IconMapPin, IconHeart, IconX, IconSparkles,
  IconBulb, IconAlertCircle, IconCheck, IconPlus, IconTrash, IconSend,
  IconRefresh, IconWind, IconDroplet, IconSun, IconEye,
  IconShare, IconBell, IconWoman, IconUser, IconClipboardCheck,
  IconActivity, IconBuildingHospital, IconCar, IconBus, IconBolt,
  IconFlame, IconCreditCard
} from '@tabler/icons-react';
import { MapContainer, TileLayer, Marker, Popup, Circle, LayerGroup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const API = 'http://localhost:8000/api';

const DEFAULT_CHECKLIST = [
  { text: 'Passport & National ID', cat: 'documents', done: false },
  { text: 'Digital copies of all documents in cloud', cat: 'documents', done: false },
  { text: 'Travel insurance policy', cat: 'documents', done: false },
  { text: 'Hotel confirmation & address (local language)', cat: 'documents', done: false },
  { text: 'Emergency contacts saved offline', cat: 'contacts', done: false },
  { text: 'Trip shared with trusted contact at home', cat: 'contacts', done: false },
  { text: 'Prescription medicines + extras', cat: 'health', done: false },
  { text: 'First aid kit', cat: 'health', done: false },
  { text: 'Power bank (fully charged)', cat: 'essentials', done: false },
  { text: 'Offline maps downloaded', cat: 'essentials', done: false },
  { text: 'Emergency cash (local currency)', cat: 'essentials', done: false },
  { text: 'Travel adapter / universal plug', cat: 'essentials', done: false },
  { text: 'Registered taxi / ride-hailing app installed', cat: 'transport', done: false },
];

const INCIDENT_TYPES = [
  { id: 'road_block', label: 'Road Block', icon: '🚧' },
  { id: 'accident', label: 'Accident', icon: '🚗' },
  { id: 'heavy_traffic', label: 'Heavy Traffic', icon: '🚦' },
  { id: 'flood', label: 'Flood / Waterlogging', icon: '🌊' },
  { id: 'medical_emergency', label: 'Medical Emergency', icon: '🚑' },
  { id: 'lost_item', label: 'Lost Item', icon: '🔍' },
  { id: 'unsafe_area', label: 'Unsafe Area', icon: '⚠️' },
  { id: 'metro_delay', label: 'Metro / Train Delay', icon: '🚇' },
  { id: 'other', label: 'Other', icon: '📋' },
];

const QUICK_QUESTIONS = [
  'Is this area safe at night?',
  'Nearest hospital?',
  'What if I lose my passport?',
  'Will it rain today?',
  'Nearest police station?',
  'Can I drink tap water here?',
];

function ScoreRing({ score, size = 100, label, sub = '' }) {
  const r = size / 2 - 10;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, score)) / 100) * c;
  const col = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex flex-col items-center gap-1 shrink-0">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={size > 90 ? 10 : 7} />
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={col}
            strokeWidth={size > 90 ? 10 : 7} strokeDasharray={c} strokeDashoffset={offset}
            strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.2s ease' }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-black font-heading" style={{ color: col, fontSize: size > 90 ? 24 : 15 }}>{score}</span>
          <span className="text-[8px] text-[var(--text-muted)] font-bold">/100</span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-widest">{label}</div>
        {sub && <div className="text-[9px] text-[var(--text-muted)] opacity-70">{sub}</div>}
      </div>
    </div>
  );
}

function RiskBadge({ level, score }) {
  const map = {
    Low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    Moderate: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    High: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  const icons = { Low: '✅', Moderate: '⚠️', High: '🔴' };
  return (
    <span className={`text-xs font-extrabold px-3 py-1 rounded-full border ${map[level] || map.Moderate}`}>
      {icons[level] || '⚠️'} {level} Risk · {score}/100
    </span>
  );
}

function WeatherMetric({ icon, label, value, sub, color = 'text-[var(--text-primary)]' }) {
  return (
    <div className="flex flex-col gap-2 p-4 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
      <div className="flex items-center gap-2">{icon}<span className="text-[10px] text-[var(--text-muted)] font-bold uppercase">{label}</span></div>
      <span className={`text-xl font-black font-heading ${color}`}>{value}</span>
      {sub && <span className="text-[10px] text-[var(--text-muted)] font-semibold">{sub}</span>}
    </div>
  );
}

export default function SafetyHub() {
  const [destination, setDestination] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [checklist, setChecklist] = useState(DEFAULT_CHECKLIST.map((c, i) => ({ id: i + 1, ...c })));
  const [newItem, setNewItem] = useState('');
  const [showAssistant, setShowAssistant] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [showIncident, setShowIncident] = useState(false);
  const [incidentType, setIncidentType] = useState('');
  const [incidentDesc, setIncidentDesc] = useState('');
  const [incidentSubmitted, setIncidentSubmitted] = useState(false);
  const [shareActive, setShareActive] = useState(false);
  const [shareToken, setShareToken] = useState('');
  const [mapLayer, setMapLayer] = useState('all');
  const reqIdRef = useRef(0);

  const userId = parseInt(localStorage.getItem('user_id') || '0');
  const token = localStorage.getItem('token');

  const fetchDashboard = async (e) => {
    if (e) e.preventDefault();
    if (!destination.trim()) return;
    const currentReqId = ++reqIdRef.current;
    setLoading(true); setError(''); setData(null); setActiveTab('dashboard');
    try {
      const res = await fetch(
        `${API}/safety/dashboard?destination=${encodeURIComponent(destination.trim())}&user_id=${userId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const json = await res.json();
      if (currentReqId !== reqIdRef.current) return;
      if (res.ok) {
        setData(json);
      } else {
        setError(json.detail || 'Unable to resolve destination');
      }
    } catch (_) {
      if (currentReqId === reqIdRef.current) {
        setError('Network error — please check your connection.');
      }
    }
    if (currentReqId === reqIdRef.current) {
      setLoading(false);
    }
  };

  const askAI = async (q = aiQuestion) => {
    if (!q.trim()) return;
    setAiLoading(true); setAiAnswer(''); setAiQuestion(q);
    try {
      const res = await fetch(
        `${API}/safety/assistant?question=${encodeURIComponent(q)}&destination=${encodeURIComponent(destination || '')}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const json = await res.json();
      setAiAnswer(json.answer || 'No answer found.');
    } catch (_) { setAiAnswer('AI assistant is temporarily unavailable.'); }
    setAiLoading(false);
  };

  useEffect(() => {
    if (!userId) return;
    const fetchChecklist = async () => {
      try {
        const res = await fetch(`${API}/safety/checklist/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
        const json = await res.json();
        if (res.ok && json.length > 0) {
          setChecklist(json.map(i => ({ id: i.id, text: i.item_text, cat: i.category, done: Boolean(i.is_done) })));
        } else if (res.ok && json.length === 0) {
          // If no items, auto-populate DEFAULT_CHECKLIST via API
          for (const item of DEFAULT_CHECKLIST) {
            await fetch(`${API}/safety/checklist`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
              body: JSON.stringify({ user_id: userId, item_text: item.text, category: item.cat })
            });
          }
          // Fetch again
          const newRes = await fetch(`${API}/safety/checklist/${userId}`, { headers: { Authorization: `Bearer ${token}` } });
          const newJson = await newRes.json();
          if (newRes.ok) setChecklist(newJson.map(i => ({ id: i.id, text: i.item_text, cat: i.category, done: Boolean(i.is_done) })));
        }
      } catch (_) {}
    };
    fetchChecklist();
  }, [userId, token]);

  const toggleCheck = async (id) => {
    const item = checklist.find(i => i.id === id);
    if (!item) return;
    setChecklist(p => p.map(i => i.id === id ? { ...i, done: !i.done } : i));
    try {
      await fetch(`${API}/safety/checklist`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ item_id: id, is_done: !item.done })
      });
    } catch (_) {}
  };

  const removeCheck = async (id) => {
    setChecklist(p => p.filter(i => i.id !== id));
    try {
      await fetch(`${API}/safety/checklist/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (_) {}
  };

  const addCheck = async () => {
    if (!newItem.trim() || !userId) return;
    const itemText = newItem.trim();
    const tempId = Date.now();
    setChecklist(p => [...p, { id: tempId, text: itemText, cat: 'custom', done: false }]);
    setNewItem('');
    try {
      const res = await fetch(`${API}/safety/checklist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ user_id: userId, item_text: itemText, category: 'custom' })
      });
      if (res.ok) {
        const json = await res.json();
        setChecklist(p => p.map(i => i.id === tempId ? { ...i, id: json.id } : i));
      }
    } catch (_) {}
  };
  const activateShare = () => { setShareToken(Math.random().toString(36).substring(2, 10).toUpperCase()); setShareActive(true); };
  const submitIncident = () => { setIncidentSubmitted(true); setTimeout(() => { setShowIncident(false); setIncidentSubmitted(false); setIncidentType(''); setIncidentDesc(''); }, 2000); };

  const done = checklist.filter(i => i.done).length;
  const pct = checklist.length > 0 ? Math.round((done / checklist.length) * 100) : 0;
  const readinessLabel = loading ? 'Calculating...' : `${pct}%`;

  const TABS = [
    { id: 'dashboard', label: '🛡 Dashboard' },
    { id: 'weather', label: '🌤 Weather' },
    { id: 'nearby', label: '📍 Nearby' },
    { id: 'health', label: '💊 Health' },
    { id: 'checklist', label: `✅ Readiness (${readinessLabel})` },
    { id: 'women', label: '👩 Women' },
    { id: 'solo', label: '🧳 Solo' },
    { id: 'incidents', label: '📋 Incidents' },
  ];

  return (
    <div className="flex flex-col gap-6 pb-24">

      {/* ── HERO ── */}
      <div className="relative overflow-hidden rounded-3xl p-8 bg-gradient-to-br from-[#0a0f1e] via-[#0d1b3e] to-[#0a0f1e] border border-blue-900/30 shadow-2xl">
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-400 via-blue-600 to-indigo-800" />
        <div className="absolute top-3 right-4 text-[120px] opacity-5 select-none pointer-events-none">🛡️</div>
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div>
            <div className="inline-flex items-center gap-2 text-[10px] font-extrabold text-emerald-400 border border-emerald-500/30 rounded-full px-3 py-1 bg-emerald-500/10 mb-3 uppercase tracking-widest">
              <IconShieldCheck size={11} className="animate-pulse" /> AI Travel Safety Command Center v2.0
            </div>
            <h1 className="text-3xl md:text-4xl font-black text-white flex items-center gap-3 tracking-tight">
              <IconShieldCheck className="text-emerald-400" size={36} /> Safety Hub
            </h1>
            <p className="text-slate-300 text-sm mt-2 font-medium max-w-lg">
              Destination-specific emergency contacts · Live weather alerts · Nearby hospitals &amp; police · AI safety analysis
            </p>
          </div>
          {/* SOS */}
          <button
            onClick={() => { if (window.confirm('🚨 Confirm Emergency SOS?\nThis will simulate alerting emergency services. In a real emergency, call 112.')) alert('🚨 SOS activated. In a real emergency, call 112 or your local emergency number immediately.'); }}
            className="shrink-0 w-20 h-20 rounded-full bg-gradient-to-br from-red-500 to-red-700 text-white font-black text-base shadow-2xl shadow-red-500/50 border-2 border-red-400/60 hover:scale-110 transition-all flex items-center justify-center"
            style={{ animation: 'pulse 2s infinite' }}
          >
            SOS
          </button>
        </div>
        {/* Search */}
        <form onSubmit={fetchDashboard} className="relative z-10 mt-6 flex gap-3">
          <div className="relative flex-1">
            <IconSearch size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <input
              value={destination}
              onChange={e => setDestination(e.target.value)}
              placeholder="Enter destination: Tokyo, Paris, Bangkok, Mumbai..."
              className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-slate-400 text-sm font-medium focus:outline-none focus:border-emerald-400 backdrop-blur-sm"
            />
          </div>
          <button type="submit" disabled={loading || !destination.trim()}
            className="px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-sm flex items-center gap-2 transition-all disabled:opacity-50">
            {loading ? <><IconLoader className="animate-spin" size={15} /> Analyzing...</> : <><IconShieldCheck size={15} /> Analyze</>}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-semibold flex items-center gap-2">
          <IconAlertCircle size={18} /> {error}
        </div>
      )}

      {/* Live Share Banner */}
      {shareActive && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between gap-4 animate-fadeIn">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-sm font-extrabold text-emerald-400">Live Sharing Active</span>
            <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-white">{shareToken}</span>
            <span className="text-xs text-slate-400">· Expires in 6 hours</span>
          </div>
          <button onClick={() => setShareActive(false)} className="text-slate-400 hover:text-white"><IconX size={16} /></button>
        </div>
      )}

      {/* Tab Navigation */}
      {data && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-xl text-xs font-extrabold border transition-all shrink-0 ${activeTab === tab.id ? 'bg-emerald-600 text-white border-emerald-500 shadow-md' : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-emerald-400'}`}>
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* ═══════════════════ TAB: DASHBOARD ═══════════════════ */}
      {data && activeTab === 'dashboard' && (
        <div className="flex flex-col gap-5 animate-fadeIn">

          {/* ── Travel Alert Banners ── */}
          {(data.dashboard?.travel_alerts || []).map((alert, i) => (
            <div key={i} className={`flex items-start gap-3 p-4 rounded-2xl border animate-fadeIn ${
              alert.level === 'high' ? 'bg-red-500/10 border-red-500/30' :
              alert.level === 'moderate' ? 'bg-amber-500/10 border-amber-500/30' :
              'bg-blue-500/10 border-blue-500/20'
            }`}>
              <span className="text-2xl shrink-0">{alert.icon}</span>
              <div>
                <div className={`text-sm font-extrabold ${
                  alert.level === 'high' ? 'text-red-400' :
                  alert.level === 'moderate' ? 'text-amber-400' : 'text-blue-400'
                }`}>
                  {alert.level === 'high' ? '🔴 High Alert' : alert.level === 'moderate' ? '⚠️ Travel Advisory' : '💡 Notice'}
                </div>
                <p className="text-xs text-[var(--text-secondary)] font-medium mt-0.5">{alert.message}</p>
              </div>
            </div>
          ))}

          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex flex-col lg:flex-row items-center lg:items-start gap-6">
              {/* Score rings */}
              <div className="flex items-center gap-6 shrink-0">
                <ScoreRing score={data.dashboard?.overall_score || 88} size={130} label="Overall Safety" />
                <div className="flex flex-col gap-4">
                  <ScoreRing score={data.dashboard?.women_score || 78} size={75} label="Women Safety" />
                  <ScoreRing score={data.dashboard?.solo_score || 80} size={75} label="Solo Safety" />
                </div>
              </div>
              {/* Factors */}
              <div className="flex-1 flex flex-col gap-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h2 className="text-lg font-black text-[var(--text-primary)] font-heading">{destination}</h2>
                  <RiskBadge level={data.dashboard?.risk_label || 'Low'} score={data.dashboard?.overall_score || 88} />
                </div>
                <p className="text-sm font-extrabold text-emerald-400">🟢 {data.dashboard?.travel_status}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                  {(data.dashboard?.factors || []).map((f, i) => (
                    <div key={i} className={`flex flex-col gap-1.5 p-3 rounded-xl border text-xs ${
                      f.positive ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-amber-500/5 border-amber-500/20'
                    }`}>
                      {/* Row: icon + label + status */}
                      <div className="flex items-start gap-2">
                        <span className="shrink-0 mt-0.5">{f.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className={`font-extrabold text-[11px] ${
                            f.positive ? 'text-[var(--text-primary)]' : 'text-amber-400'
                          }`}>{f.label}</div>
                          <div className={`font-bold mt-0.5 ${
                            f.label === 'Tourist Friendly' ? 'text-amber-400 tracking-widest text-base leading-none' : 'text-[var(--text-secondary)]'
                          }`}>{f.status}</div>
                        </div>
                      </div>
                      {/* Tourist sub-details */}
                      {f.sub_details?.length > 0 && (
                        <div className="ml-5 flex flex-col gap-0.5">
                          {f.sub_details.map((d, j) => (
                            <span key={j} className="text-[9px] text-[var(--text-muted)]">· {d}</span>
                          ))}
                        </div>
                      )}
                      {/* Medical AI tip */}
                      {f.tip && f.label === 'Medical Facilities' && (
                        <div className="ml-5 mt-0.5 text-[9px] text-blue-400 font-semibold">💡 {f.tip}</div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Visa / Entry — honest disclaimer with link */}
                {data.dashboard?.entry_info && (
                  <div className="bg-[var(--bg-app)] rounded-xl p-3 border border-[var(--border-color)] flex flex-col gap-1">
                    <div className="flex items-center gap-1.5">
                      <span>🛂</span>
                      <span className="text-[11px] font-extrabold text-[var(--text-primary)]">Visa Requirement</span>
                    </div>
                    <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{data.dashboard.entry_info}</p>
                    {data.dashboard.entry_link && (
                      <a href={data.dashboard.entry_link} target="_blank" rel="noopener noreferrer"
                        className="text-[11px] text-blue-400 font-extrabold hover:underline mt-0.5">
                        Official Source →
                      </a>
                    )}
                  </div>
                )}

                {data.dashboard?.transport_tip && (
                  <div className="text-[11px] text-[var(--text-muted)] bg-[var(--bg-app)] rounded-xl p-2.5 border border-[var(--border-color)] font-medium">
                    🚌 <strong>Transport:</strong> {data.dashboard.transport_tip}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Score Breakdown */}
          {(data.dashboard?.score_breakdown || []).length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
              <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading mb-4 flex items-center gap-2">
                📊 Score Breakdown <span className="text-[10px] font-bold text-[var(--text-muted)] font-body normal-case">— {data.dashboard.overall_score}/100 overall</span>
              </h3>
              <div className="flex flex-col gap-3">
                {(data.dashboard.score_breakdown).map((item, i) => {
                  const pctVal = Math.round((item.score / item.max) * 100);
                  const col = pctVal >= 80 ? 'from-emerald-500 to-teal-400' : pctVal >= 60 ? 'from-amber-500 to-yellow-400' : 'from-red-500 to-orange-400';
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <div className="text-xs font-bold text-[var(--text-muted)] w-36 shrink-0">{item.label}</div>
                      <div className="flex-1 h-2.5 rounded-full bg-slate-800 overflow-hidden">
                        <div className={`h-full rounded-full bg-gradient-to-r ${col} transition-all`}
                          style={{ width: `${pctVal}%` }} />
                      </div>
                      <div className="text-xs font-black text-[var(--text-primary)] font-heading w-12 text-right">
                        {item.score}<span className="text-[var(--text-muted)] font-normal">/{item.max}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}


          {/* Status Quick Cards — Health multi-metric */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { l: 'Weather Risk', v: data.dashboard?.weather_risk > 40 ? 'Elevated' : 'Low', i: '🌤', c: data.dashboard?.weather_risk > 40 ? 'text-amber-400' : 'text-emerald-400' },
              { l: 'AQI', v: data.health_advisory?.aqi_label || 'Good', i: '💨', c: data.health_advisory?.aqi_label === 'Good' ? 'text-emerald-400' : 'text-amber-400' },
              { l: 'Heat Index', v: data.health_advisory?.heat_label || '--', i: '🌡️', c: data.health_advisory?.heat_label === 'Comfortable' ? 'text-emerald-400' : 'text-amber-400' },
              { l: 'UV Index', v: `${data.weather?.uv_index ?? '--'}`, i: '☀️', c: data.weather?.uv_index >= 8 ? 'text-amber-400' : 'text-emerald-400' },
              { l: 'Pollen', v: data.health_advisory?.pollen || 'Low', i: '🌸', c: data.health_advisory?.pollen === 'Low' ? 'text-emerald-400' : 'text-amber-400' },
              { l: 'Water Safety', v: data.health_advisory?.water_safety?.includes('Safe') ? 'Safe' : 'Bottled', i: '💧', c: 'text-blue-400' },
            ].map((card, i) => (
              <div key={i} className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] flex flex-col gap-1.5">
                <span className="text-2xl">{card.i}</span>
                <div className={`text-sm font-extrabold font-heading ${card.c}`}>{card.v}</div>
                <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wide">{card.l}</div>
              </div>
            ))}
          </div>


          {/* Emergency Contacts */}
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
                <IconPhone className="text-red-400" size={20} /> Emergency Contacts · {data.country}
              </h3>
              <span className="text-[10px] text-slate-500 font-bold">Verified Country Dataset</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {Object.entries(data.emergency_contacts || {}).map(([key, number]) => {
                const icons = { Police: '🚓', Ambulance: '🚑', Fire: '🚒', 'Tourist Helpline': '🗺️', 'Tourist Hotline': '🗺️', 'Women Helpline': '👩', 'Disaster Mgmt': '⛑️', Emergency: '🚨', 'Coast Guard': '⚓', 'Non-Emergency': '📞', 'Police/Fire/Ambulance': '🆘', NHS: '💊', SAR: '🛥️' };
                return (
                  <div key={key} className="p-4 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)] flex flex-col gap-2">
                    <div className="flex items-start gap-2">
                      <span className="text-xl">{icons[key] || '📞'}</span>
                      <span className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-wider leading-tight">{key.replace(/_/g, ' ')}</span>
                    </div>
                    <span className="text-xl font-black text-[var(--text-primary)] font-heading">{number}</span>
                    <div className="flex gap-1.5">
                      <a href={`tel:${String(number).replace(/[^0-9+]/g, '').split('/')[0]}`}
                        className="flex-1 text-center text-[10px] font-bold py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-600 hover:text-white transition-all">
                        📞 Call
                      </a>
                      <button onClick={() => navigator.clipboard?.writeText(String(number))}
                        className="flex-1 text-center text-[10px] font-bold py-1.5 rounded-lg bg-slate-500/10 border border-slate-500/20 text-slate-400 hover:bg-slate-600 hover:text-white transition-all">
                        📋 Copy
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Safety Timeline */}
          {data.timeline?.length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
              <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-4">
                🕐 Safety Timeline · Next 12 Hours
              </h3>
              <div className="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
                {data.timeline.map((slot, i) => (
                  <div key={i} className={`shrink-0 flex flex-col items-center gap-2 p-4 rounded-2xl border w-36 ${slot.risk === 'high' ? 'bg-red-500/10 border-red-500/30' : slot.risk === 'moderate' ? 'bg-amber-500/10 border-amber-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                    <span className="text-[11px] font-extrabold text-[var(--text-muted)] uppercase">{slot.time}</span>
                    <span className="text-base">{slot.label.split(' ')[0]}</span>
                    <span className={`text-[11px] font-extrabold text-center leading-tight ${slot.risk === 'high' ? 'text-red-400' : slot.risk === 'moderate' ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {slot.label.replace(/^[^\s]+\s/, '')}
                    </span>
                    {slot.temperature && <span className="text-[10px] text-[var(--text-muted)] font-semibold">{slot.temperature}°C</span>}
                    <span className="text-[9px] text-[var(--text-muted)] text-center leading-tight">{slot.tip}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Safety Tips */}
          {data.ai_tips?.length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
              <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-4">
                <IconSparkles className="text-amber-400 animate-pulse" size={20} /> AI Safety Recommendations · {destination.split(',')[0]}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {data.ai_tips.map((tip, i) => (
                  <div key={i} className="flex items-start gap-3 p-3.5 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
                    <span className="text-emerald-400 mt-0.5 shrink-0 text-base">
                      {tip.startsWith('⛈') ? '⛈️' : tip.startsWith('🌧') ? '🌧️' : tip.startsWith('💨') ? '💨' : tip.startsWith('☀️') ? '☀️' : '💡'}
                    </span>
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">{tip}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scam Alerts */}
          {data.scam_alerts?.length > 0 && (
            <div className="glass-card p-6 rounded-3xl border border-amber-500/20 bg-amber-500/5">
              <h3 className="text-base font-extrabold text-amber-400 font-heading flex items-center gap-2 mb-4">
                <IconAlertTriangle size={20} /> Scam Awareness · {destination.split(',')[0]}
              </h3>
              <div className="flex flex-col gap-3">
                {data.scam_alerts.slice(0, 4).map((scam, i) => (
                  <div key={i} className="p-4 rounded-2xl bg-[var(--bg-card)] border border-amber-500/20">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-extrabold text-[var(--text-primary)]">{scam.name || `Scam Alert ${i + 1}`}</span>
                      {scam.severity && <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase ${scam.severity === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>{scam.severity}</span>}
                    </div>
                    <p className="text-xs text-[var(--text-muted)] leading-relaxed">{scam.description || scam}</p>
                    {scam.how_to_avoid && <p className="text-xs text-emerald-400 font-semibold mt-1.5">✅ {scam.how_to_avoid}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════ TAB: WEATHER ═══════════════════ */}
      {data && activeTab === 'weather' && (
        <div className="flex flex-col gap-5 animate-fadeIn">
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex items-center gap-3 mb-5">
              <span className="text-4xl">{data.weather?.icon}</span>
              <div>
                <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading">{data.weather?.description}</h3>
                <p className="text-xs text-[var(--text-muted)] font-medium">Live data · Open-Meteo API · {destination}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <WeatherMetric icon={<IconSun size={18} className="text-amber-400" />} label="Temperature" value={`${data.weather?.temperature ?? '--'}°C`} sub={`Feels ${data.weather?.feels_like ?? '--'}°C`} />
              <WeatherMetric icon={<IconDroplet size={18} className="text-blue-400" />} label="Rain Probability" value={`${data.weather?.rain_probability ?? 0}%`} sub={data.weather?.rain_probability > 60 ? '⚠️ Carry gear' : '✅ Unlikely'} color={data.weather?.rain_probability > 60 ? 'text-blue-400' : 'text-[var(--text-primary)]'} />
              <WeatherMetric icon={<IconWind size={18} className="text-slate-400" />} label="Wind Speed" value={`${data.weather?.wind_speed ?? '--'} km/h`} sub={data.weather?.wind_speed > 40 ? '⚠️ Strong' : '✅ Safe'} />
              <WeatherMetric icon={<IconSun size={18} className="text-orange-400" />} label="UV Index" value={`${data.weather?.uv_index ?? '--'}`} sub={data.weather?.uv_index >= 8 ? '🔴 Very High' : data.weather?.uv_index >= 5 ? '⚠️ Moderate' : '✅ Low'} color={data.weather?.uv_index >= 8 ? 'text-orange-400' : 'text-[var(--text-primary)]'} />
              <WeatherMetric icon={<IconEye size={18} className="text-sky-400" />} label="Visibility" value={`${data.weather?.visibility ?? '--'} km`} sub={data.weather?.visibility < 2 ? '⚠️ Poor' : '✅ Clear'} />
              <WeatherMetric icon={<IconDroplet size={18} className="text-cyan-400" />} label="Humidity" value={`${data.weather?.humidity ?? '--'}%`} sub={data.weather?.humidity > 80 ? '💦 Very humid' : '✅ OK'} />
            </div>
          </div>

          {data.weather?.warnings?.length > 0 ? (
            <div className="flex flex-col gap-3">
              {data.weather.warnings.map((w, i) => (
                <div key={i} className={`p-4 rounded-2xl border flex items-center gap-3 ${w.level === 'high' ? 'bg-red-500/10 border-red-500/30' : 'bg-amber-500/10 border-amber-500/30'}`}>
                  <span className="text-2xl">{w.icon}</span>
                  <div>
                    <div className={`text-sm font-extrabold ${w.level === 'high' ? 'text-red-400' : 'text-amber-400'}`}>{w.level === 'high' ? '🔴 High Alert' : '⚠️ Weather Advisory'}</div>
                    <p className="text-xs text-[var(--text-secondary)] font-medium mt-0.5">{w.message}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <span className="text-sm font-extrabold text-emerald-400">No active weather warnings. Conditions are safe for travel.</span>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════ TAB: NEARBY ═══════════════════ */}
      {data && activeTab === 'nearby' && (
        <NearbyServicesTab
          lat={data.location?.latitude ?? data.coordinates?.lat}
          lon={data.location?.longitude ?? data.coordinates?.lon}
          destination={data.location?.display_name || data.location?.name || data.destination || destination}
          token={token}
        />
      )}

      {/* ═══════════════════ TAB: HEALTH ═══════════════════ */}
      {data && activeTab === 'health' && (
        <HealthAdvisoryTab health={data.health_advisory} destination={destination} />
      )}

      {/* ═══════════════════ TAB: CHECKLIST ═══════════════════ */}
      {activeTab === 'checklist' && (
        <div className="flex flex-col gap-5 animate-fadeIn">
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
                <IconClipboardCheck size={20} className="text-emerald-400" /> Travel Readiness Checklist
              </h3>
              <div className="flex items-center gap-2">
                <div className="text-lg font-black text-emerald-400 font-heading">{pct}%</div>
                <span className="text-xs text-[var(--text-muted)] font-bold">Ready</span>
              </div>
            </div>
            <div className="h-3 rounded-full bg-slate-800 mb-5 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all" style={{ width: `${pct}%` }} />
            </div>
            <div className="flex gap-2 mb-4">
              <input value={newItem} onChange={e => setNewItem(e.target.value)} onKeyDown={e => e.key === 'Enter' && addCheck()} placeholder="Add custom safety item..."
                className="flex-1 px-3.5 py-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-emerald-500" />
              <button onClick={addCheck} className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5"><IconPlus size={14} /> Add</button>
            </div>
            {['documents', 'contacts', 'health', 'essentials', 'transport', 'custom'].map(cat => {
              const items = checklist.filter(i => i.cat === cat);
              if (!items.length) return null;
              const catLabels = { documents: '📄 Documents', contacts: '📞 Contacts', health: '💊 Health', essentials: '🎒 Essentials', transport: '🚖 Transport', custom: '➕ Custom' };
              return (
                <div key={cat} className="mb-4">
                  <div className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-widest mb-2">{catLabels[cat]}</div>
                  <div className="flex flex-col gap-1.5">
                    {items.map(item => (
                      <div key={item.id} className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${item.done ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-[var(--bg-app)] border-[var(--border-color)]'}`}>
                        <button onClick={() => toggleCheck(item.id)} className={`shrink-0 w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${item.done ? 'bg-emerald-500 border-emerald-500' : 'bg-transparent border-slate-600 hover:border-emerald-400'}`}>
                          {item.done ? <IconCheck size={12} className="text-white" /> : null}
                        </button>
                        <span className={`flex-1 text-xs font-semibold ${item.done ? 'line-through text-[var(--text-muted)]' : 'text-[var(--text-secondary)]'}`}>{item.text}</span>
                        <button onClick={() => removeCheck(item.id)} className="text-slate-600 hover:text-red-400 transition-colors"><IconTrash size={13} /></button>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Location Sharing */}
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-4">
              <IconShare className="text-blue-400" size={20} /> Live Location Sharing
            </h3>
            {shareActive ? (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-sm font-extrabold text-emerald-400">Live Sharing ON</span>
                  <span className="text-xs font-mono text-white bg-slate-800 px-2 py-0.5 rounded ml-1">{shareToken}</span>
                </div>
                <p className="text-xs text-[var(--text-muted)]">Token expires in 6 hours. Share this code with trusted contacts.</p>
                <button onClick={() => setShareActive(false)} className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-bold w-fit">Stop Sharing</button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <p className="text-xs text-[var(--text-muted)]">Generate a temporary 6-hour share token to let trusted contacts follow your location.</p>
                <button onClick={activateShare} className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-extrabold flex items-center gap-2 w-fit">
                  <IconShare size={14} /> Start Live Sharing
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════ TAB: WOMEN SAFETY ═══════════════════ */}
      {activeTab === 'women' && (
        <WomenSafetyTab data={data} destination={destination} />
      )}

      {/* ═══════════════════ TAB: SOLO TRAVEL ═══════════════════ */}
      {activeTab === 'solo' && (
        <SoloSafetyTab data={data} destination={destination} />
      )}

      {/* ═══════════════════ TAB: INCIDENTS ═══════════════════ */}
      {activeTab === 'incidents' && (
        <div className="flex flex-col gap-5 animate-fadeIn">
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-2">
              <IconBell className="text-amber-400" size={20} /> Nearby Incidents
            </h3>
            {/* No incidents — show timestamp */}
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3 mb-5">
              <span className="text-xl">✅</span>
              <div>
                <div className="text-sm font-extrabold text-emerald-400">No active incidents reported today.</div>
                <div className="text-xs text-[var(--text-muted)] font-semibold mt-0.5">
                  Last updated: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · Source: Community Reports
                </div>
              </div>
            </div>

            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-4">Report a Safety Incident</h3>
            {incidentSubmitted ? (
              <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold text-sm flex items-center gap-2">
                <IconCheck size={18} /> Incident reported. Stay safe!
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {INCIDENT_TYPES.map(t => (
                    <button key={t.id} onClick={() => setIncidentType(t.id)}
                      className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition-all ${incidentType === t.id ? 'bg-amber-500/20 border-amber-500/40 text-amber-400' : 'bg-[var(--bg-app)] border-[var(--border-color)] text-[var(--text-muted)] hover:border-amber-400'}`}>
                      <span className="text-xl">{t.icon}</span><span>{t.label}</span>
                    </button>
                  ))}
                </div>
                <textarea rows={3} value={incidentDesc} onChange={e => setIncidentDesc(e.target.value)}
                  placeholder="Describe what happened, where, and when..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-amber-500 resize-none" />
                <button onClick={submitIncident} disabled={!incidentType || !incidentDesc.trim()}
                  className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-extrabold text-xs flex items-center gap-2 w-fit disabled:opacity-50">
                  <IconSend size={14} /> Submit Report
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick access cards before search */}
      {!data && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: '✅', title: 'Travel Readiness', desc: '13 pre-loaded safety items. Track your departure readiness.', tab: 'checklist', border: 'border-emerald-500/20 hover:border-emerald-400' },
            { icon: '👩', title: 'Women Safety', desc: 'Dedicated tips, helplines, safe areas, and guidance for women travelers.', tab: 'women', border: 'border-pink-500/20 hover:border-pink-400' },
            { icon: '🧳', title: 'Solo Traveler', desc: 'Essential guidance for solo adventurers to stay safe on the road.', tab: 'solo', border: 'border-blue-500/20 hover:border-blue-400' },
            { icon: '📋', title: 'Report Incident', desc: 'Log safety incidents encountered during your trip.', tab: 'incidents', border: 'border-amber-500/20 hover:border-amber-400' },
          ].map(card => (
            <button key={card.tab} onClick={() => setActiveTab(card.tab)}
              className={`glass-card p-5 rounded-3xl border ${card.border} bg-[var(--bg-card)] text-left flex flex-col gap-3 hover:shadow-lg transition-all`}>
              <span className="text-3xl">{card.icon}</span>
              <div>
                <div className="text-sm font-extrabold text-[var(--text-primary)] font-heading">{card.title}</div>
                <div className="text-xs text-[var(--text-muted)] font-medium mt-0.5 leading-relaxed">{card.desc}</div>
              </div>
              <div className="text-xs font-bold text-blue-400">Open →</div>
            </button>
          ))}
        </div>
      )}

      {/* ── DATA SOURCES BADGE ── */}
      <div className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)]">
        <div className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-widest mb-3">Data Sources &amp; Transparency</div>
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Geocoding', source: 'Nominatim OSM', icon: '🗺️', color: 'border-blue-500/30 text-blue-400 bg-blue-500/5' },
            { label: 'Routing', source: 'OSRM', icon: '🚗', color: 'border-slate-500/30 text-slate-400 bg-slate-500/5' },
            { label: 'Weather', source: 'Open-Meteo', icon: '🌤️', color: 'border-sky-500/30 text-sky-400 bg-sky-500/5' },
            { label: 'Nearby Services', source: 'Overpass API', icon: '📍', color: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5' },
            { label: 'Country Data', source: 'REST Countries', icon: '🌏', color: 'border-purple-500/30 text-purple-400 bg-purple-500/5' },
            { label: 'AI Analysis', source: 'Gemini', icon: '✨', color: 'border-amber-500/30 text-amber-400 bg-amber-500/5' },
            { label: 'Maps', source: 'OpenStreetMap', icon: '🗾', color: 'border-green-500/30 text-green-400 bg-green-500/5' },
          ].map((s, i) => (
            <div key={i} className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-[10px] font-bold ${s.color}`}>
              <span>{s.icon}</span>
              <span className="text-[var(--text-muted)]">{s.label}:</span>
              <span>{s.source}</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-[var(--text-muted)] mt-2.5 leading-relaxed">
          ⚠️ Visa and entry requirements vary by nationality. Always verify with official government sources before travel.
          Safety scores are derived from live weather data, destination crime indices, and AI analysis — not guarantees.
        </p>
      </div>

      {/* ── FLOATING AI ASSISTANT ── */}
      <div className="fixed bottom-6 right-6 z-40">
        <button onClick={() => setShowAssistant(!showAssistant)}
          className="p-3.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-2xl hover:scale-110 transition-all flex items-center gap-2 border border-emerald-400/40">
          <IconShieldCheck size={20} />
          <span className="text-xs font-black hidden sm:inline">AI Safety Guide</span>
        </button>
        {showAssistant && (
          <div className="absolute bottom-16 right-0 w-80 sm:w-96 glass-card p-5 rounded-3xl border border-slate-700 bg-slate-900 text-white shadow-2xl space-y-3 animate-fadeIn">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <span className="text-xs font-extrabold text-emerald-300 flex items-center gap-1.5">
                <IconShieldCheck size={14} className="text-emerald-400" /> AI Safety Assistant
              </span>
              <button onClick={() => setShowAssistant(false)} className="text-slate-400 hover:text-white"><IconX size={14} /></button>
            </div>
            <div className="space-y-1.5">
              <span className="text-[10px] text-slate-400 font-extrabold uppercase">Quick Ask</span>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_QUESTIONS.map((q, i) => (
                  <button key={i} onClick={() => askAI(q)}
                    className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-800 hover:bg-emerald-700 text-slate-300 hover:text-white transition-all text-left">
                    {q}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <input value={aiQuestion} onChange={e => setAiQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && askAI()}
                placeholder="Ask anything about safety..."
                className="flex-1 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500" />
              <button onClick={() => askAI()} disabled={aiLoading} className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50">
                {aiLoading ? <IconLoader className="animate-spin" size={14} /> : <IconSend size={14} />}
              </button>
            </div>
            {aiAnswer && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200 font-medium leading-relaxed">
                {aiAnswer}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Nearby Services Tab ───────────────────────────────────────────────────────
function NearbyServicesTab({ lat, lon, destination, token }) {
  const [services, setServices] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeService, setActiveService] = useState('hospitals');
  const reqIdRef = useRef(0);
  const fetchedCoordsRef = useRef('');

  const load = useCallback(async (force = false) => {
    const numLat = Number(lat);
    const numLon = Number(lon);
    if (!Number.isFinite(numLat) || !Number.isFinite(numLon) || (numLat === 0 && numLon === 0)) {
      console.warn('[SAFETY] Nearby request blocked — invalid or missing coordinates:', { lat, lon });
      return;
    }

    const coordKey = `${numLat.toFixed(4)}_${numLon.toFixed(4)}`;
    if (!force && fetchedCoordsRef.current === coordKey) {
      return;
    }
    fetchedCoordsRef.current = coordKey;

    console.log('[SAFETY] Nearby request', {
      destination,
      latitude: numLat,
      longitude: numLon,
    });
    console.trace('[SAFETY] Nearby request source');

    const currentReqId = ++reqIdRef.current;
    setLoading(true);
    setServices(null);
    try {
      const res = await fetch(`${API}/safety/nearby?lat=${numLat}&lon=${numLon}`, { headers: { Authorization: `Bearer ${token}` } });
      if (currentReqId !== reqIdRef.current) return;
      if (res.ok) setServices(await res.json());
      else setServices({});
    } catch (_) {
      if (currentReqId === reqIdRef.current) setServices({});
    }
    if (currentReqId === reqIdRef.current) setLoading(false);
  }, [lat, lon, token, destination]);

  useEffect(() => { load(); }, [load]);

  const SERVICE_TYPES = [
    { key: 'hospitals', label: 'Hospitals', icon: '🏥' },
    { key: 'police', label: 'Police', icon: '🚓' },
    { key: 'pharmacies', label: 'Pharmacies', icon: '💊' },
    { key: 'fire_stations', label: 'Fire Stations', icon: '🚒' },
    { key: 'atms', label: 'ATMs', icon: '🏧' },
    { key: 'metro_stations', label: 'Metro', icon: '🚇' },
    { key: 'bus_stops', label: 'Bus Stops', icon: '🚌' },
    { key: 'fuel_stations', label: 'Fuel', icon: '⛽' },
  ];

  const allMarkers = services ? Object.entries(services).flatMap(([type, items]) =>
    (items || []).map(item => ({ ...item, type }))
  ).filter(m => m.lat && m.lon) : [];

  return (
    <div className="flex flex-col gap-5 animate-fadeIn">
      {/* Map */}
      <div className="glass-card p-4 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
        <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-3">
          <IconMapPin className="text-red-400" size={18} /> Live Safety Map · {destination}
        </h3>
        <div className="h-72 rounded-2xl overflow-hidden border border-[var(--border-color)]" style={{ zIndex: 0 }}>
          {lat && lon ? (
            <MapContainer key={`${lat}_${lon}`} center={[lat, lon]} zoom={15} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
              <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Circle center={[lat, lon]} radius={300} pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.12 }} />
              <Marker position={[lat, lon]}><Popup><strong>📍 Your Location</strong><br />{destination}</Popup></Marker>
              {allMarkers.map((m, i) => (
                <Marker key={i} position={[m.lat, m.lon]}>
                  <Popup>
                    <strong>{SERVICE_TYPES.find(s => s.key === m.type)?.icon} {m.name}</strong><br />
                    {m.distance_km} km · ~{m.walk_min} min walk
                    {m.phone && <><br />📞 {m.phone}</>}
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-[var(--text-muted)] bg-[var(--bg-app)]">Search a destination first</div>
          )}
        </div>
      </div>

      {/* Service Type Selector */}
      <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
        {SERVICE_TYPES.map(st => (
          <button key={st.key} onClick={() => setActiveService(st.key)}
            className={`px-3.5 py-2 rounded-xl text-xs font-extrabold border transition-all shrink-0 flex items-center gap-1.5 ${activeService === st.key ? 'bg-red-600 text-white border-red-500' : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-[var(--border-color)] hover:border-red-400'}`}>
            {st.icon} {st.label}
            {services && services[st.key]?.length > 0 && (
              <span className="text-[9px] bg-white/20 rounded-full px-1.5 py-0.5 font-black">{services[st.key].length}</span>
            )}
          </button>
        ))}
        <button onClick={() => load(true)} className="px-3.5 py-2 rounded-xl text-xs font-extrabold border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-muted)] hover:border-blue-400 flex items-center gap-1.5 shrink-0">
          <IconRefresh size={13} /> Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center p-8 gap-3 text-[var(--text-muted)]">
          <IconLoader className="animate-spin" size={18} />
          <span className="text-sm font-bold">Discovering nearby services via Overpass API...</span>
        </div>
      )}

      {!loading && services && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(services[activeService] || []).length === 0 ? (
            <div className="col-span-2 p-6 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] text-center">
              <div className="text-2xl mb-2">{SERVICE_TYPES.find(s => s.key === activeService)?.icon}</div>
              <div className="text-xs text-[var(--text-muted)] font-bold">No {SERVICE_TYPES.find(s => s.key === activeService)?.label} found within search radius via OpenStreetMap.</div>
            </div>
          ) : (
            (services[activeService] || []).map((item, i) => {
              const st = SERVICE_TYPES.find(s => s.key === activeService);
              return (
                <div key={i} className="p-4 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-red-500/30 transition-all">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-extrabold text-[var(--text-primary)] font-heading truncate">{st?.icon} {item.name}</div>
                      {item.phone && <div className="text-xs text-[var(--text-muted)] mt-0.5">📞 {item.phone}</div>}
                      {item.opening_hours && <div className="text-[10px] text-emerald-400 font-semibold mt-0.5">🕐 {item.opening_hours}</div>}
                      {item.operator && <div className="text-[10px] text-[var(--text-muted)]">🏢 {item.operator}</div>}
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-base font-black text-blue-400 font-heading">{item.distance_km} km</div>
                      <div className="text-[10px] text-[var(--text-muted)]">~{item.walk_min} min walk</div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {item.phone && (
                      <a href={`tel:${item.phone.replace(/[^0-9+]/g, '')}`}
                        className="flex-1 text-center text-[10px] font-bold py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-600 hover:text-white transition-all">
                        📞 Call
                      </a>
                    )}
                    <a href={`https://www.openstreetmap.org/directions?from=${lat},${lon}&to=${item.lat},${item.lon}`}
                      target="_blank" rel="noopener noreferrer"
                      className="flex-1 text-center text-[10px] font-bold py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-600 hover:text-white transition-all">
                      🗺 Navigate
                    </a>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

// ── Health Advisory Tab ───────────────────────────────────────────────────────
function HealthAdvisoryTab({ health, destination }) {
  if (!health) {
    return (
      <div className="glass-card p-8 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] text-center">
        <p className="text-sm text-[var(--text-muted)] font-bold">Search a destination to load health advisory data.</p>
      </div>
    );
  }
  const metrics = [
    { label: 'Heat Index', val: `${health.heat_index}°C`, sub: health.heat_label, icon: '🌡️', color: health.heat_label === 'Extreme' || health.heat_label === 'Very Hot' ? 'text-red-400' : health.heat_label === 'Hot' ? 'text-amber-400' : 'text-emerald-400' },
    { label: 'Air Quality (AQI)', val: health.aqi, sub: health.aqi_label, icon: '💨', color: health.aqi_label === 'Good' ? 'text-emerald-400' : health.aqi_label === 'Moderate' ? 'text-amber-400' : 'text-red-400' },
    { label: 'Pollen Level', val: health.pollen, sub: 'Allergy risk', icon: '🌸', color: health.pollen === 'Low' ? 'text-emerald-400' : 'text-amber-400' },
    { label: 'Mosquito Risk', val: health.mosquito_risk, sub: 'Dengue/Malaria alert', icon: '🦟', color: health.mosquito_risk === 'High' ? 'text-red-400' : 'text-emerald-400' },
    { label: 'Water Safety', val: 'See note', sub: health.water_safety, icon: '💧', color: 'text-blue-400' },
    { label: 'Sun Protection', val: health.sun_protection?.split(' ')[0], sub: health.sun_protection, icon: '☀️', color: health.sun_protection?.includes('50+') ? 'text-amber-400' : 'text-emerald-400' },
  ];
  return (
    <div className="flex flex-col gap-5 animate-fadeIn">
      <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)]">
        <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2 mb-5">
          💊 Health Advisory · {destination}
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {metrics.map((m, i) => (
            <div key={i} className="flex flex-col gap-2 p-4 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
              <div className="flex items-center gap-2">
                <span className="text-xl">{m.icon}</span>
                <span className="text-[10px] text-[var(--text-muted)] font-bold uppercase">{m.label}</span>
              </div>
              <span className={`text-lg font-black font-heading ${m.color}`}>{m.val}</span>
              <span className="text-[10px] text-[var(--text-muted)] font-semibold leading-tight">{m.sub}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="glass-card p-5 rounded-3xl border border-blue-500/20 bg-blue-500/5">
        <h4 className="text-sm font-extrabold text-blue-400 flex items-center gap-2 mb-3">💉 Vaccination Note</h4>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{health.vaccination_note}</p>
      </div>
    </div>
  );
}

// ── Women Safety Tab ───────────────────────────────────────────────────────
function WomenSafetyTab({ data, destination }) {
  const womenScore = data?.dashboard?.women_score || 78;
  const safeAreas = data?.dashboard?.safe_areas || [];
  const avoidAreas = data?.dashboard?.avoid_areas || [];
  const WOMEN_TIPS = [
    { icon: '🚖', tip: 'Use only registered taxis or verified ride-hailing apps after dark.' },
    { icon: '📞', tip: 'Save the Women Helpline (1091 in India, 999 in most countries) offline.' },
    { icon: '🌃', tip: 'Avoid isolated areas and parks after 9 PM.' },
    { icon: '👥', tip: 'Travel in groups or stay in well-lit, populated areas at night.' },
    { icon: '📲', tip: 'Share your live location with a trusted contact before every outing.' },
    { icon: '🛡️', tip: 'Trust your instincts — leave any situation that feels uncomfortable.' },
    { icon: '🚇', tip: 'Use women-only train coaches where available (Japan, India, Mexico).' },
    { icon: '💳', tip: 'Keep a backup card separate from your wallet.' },
  ];
  return (
    <div className="flex flex-col gap-5 animate-fadeIn">
      <div className="glass-card p-6 rounded-3xl border border-pink-500/20 bg-gradient-to-br from-pink-500/5 to-purple-500/5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconWoman className="text-pink-400" size={22} /> Women Safety Hub
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{destination || 'Current destination'}</p>
          </div>
          <ScoreRing score={womenScore} size={90} label="Women Safety" />
        </div>

        {(safeAreas.length > 0 || avoidAreas.length > 0) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
            {safeAreas.length > 0 && (
              <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                <div className="text-xs font-extrabold text-emerald-400 mb-2 flex items-center gap-1.5">✅ Recommended Areas</div>
                {safeAreas.map((a, i) => <div key={i} className="text-xs text-[var(--text-secondary)] font-medium py-0.5">• {a}</div>)}
              </div>
            )}
            {avoidAreas.length > 0 && (
              <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20">
                <div className="text-xs font-extrabold text-red-400 mb-2 flex items-center gap-1.5">⚠️ Avoid (especially late night)</div>
                {avoidAreas.map((a, i) => <div key={i} className="text-xs text-[var(--text-secondary)] font-medium py-0.5">• {a}</div>)}
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {WOMEN_TIPS.map((t, i) => (
            <div key={i} className="flex items-start gap-3 p-3.5 rounded-2xl bg-[var(--bg-card)] border border-pink-500/10">
              <span className="text-xl shrink-0">{t.icon}</span>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">{t.tip}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 p-4 rounded-2xl bg-pink-500/10 border border-pink-500/20">
          <div className="text-xs font-extrabold text-pink-400 mb-2 flex items-center gap-1.5"><IconPhone size={14} /> Emergency Helplines</div>
          <div className="grid grid-cols-2 gap-2">
            {[{ l: 'Women Helpline (India)', n: '1091' }, { l: 'Police (Universal)', n: '112' }, { l: 'Ambulance', n: '108' }, { l: 'National Emergency', n: '112' }].map(h => (
              <a key={h.l} href={`tel:${h.n}`} className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-card)] border border-pink-500/10 hover:border-pink-400 transition-all">
                <span className="text-[10px] font-bold text-[var(--text-muted)]">{h.l}</span>
                <span className="text-sm font-black text-pink-400 font-heading">{h.n}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Solo Safety Tab ───────────────────────────────────────────────────────
function SoloSafetyTab({ data, destination }) {
  const soloScore = data?.dashboard?.solo_score || 80;
  const SOLO_TIPS = [
    { icon: '📵', tip: 'Keep your phone charged. Always carry a power bank.' },
    { icon: '🗺️', tip: 'Download offline maps (Maps.me or Google Maps offline) before you need them.' },
    { icon: '💰', tip: 'Avoid displaying valuables, expensive cameras, or jewelry in public.' },
    { icon: '💵', tip: 'Keep emergency cash in a separate pocket or money belt.' },
    { icon: '📍', tip: 'Share your live location with a trusted person at home.' },
    { icon: '🏨', tip: 'Save your hotel name in local language in your phone\'s notes.' },
    { icon: '🔦', tip: 'Carry a small torch for unexpected power cuts or dark alleys.' },
    { icon: '🚪', tip: 'Always lock your accommodation door, even during the day.' },
  ];
  return (
    <div className="flex flex-col gap-5 animate-fadeIn">
      <div className="glass-card p-6 rounded-3xl border border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-indigo-500/5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconUser className="text-blue-400" size={22} /> Solo Traveler Safety
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{destination || 'Your destination'}</p>
          </div>
          <ScoreRing score={soloScore} size={90} label="Solo Safety" />
        </div>

        {data?.coordinates && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Safety Score', val: `${soloScore}/100`, icon: '🛡️', color: 'text-emerald-400' },
              { label: 'Emergency Readiness', val: data.dashboard?.emergency_readiness || 'Available', icon: '🚑', color: 'text-emerald-400' },
              { label: 'Weather Status', val: data.weather?.description || 'Clear', icon: data.weather?.icon || '☀️', color: 'text-amber-400' },
              { label: 'Travel Status', val: data.dashboard?.travel_status?.split(' ')[0] || 'Safe', icon: '✅', color: 'text-emerald-400' },
            ].map((m, i) => (
              <div key={i} className="p-4 rounded-2xl bg-[var(--bg-card)] border border-blue-500/10 flex flex-col gap-1.5">
                <span className="text-xl">{m.icon}</span>
                <div className={`text-sm font-extrabold font-heading ${m.color}`}>{m.val}</div>
                <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase tracking-wide">{m.label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SOLO_TIPS.map((t, i) => (
            <div key={i} className="flex items-start gap-3 p-3.5 rounded-2xl bg-[var(--bg-card)] border border-blue-500/10 hover:border-blue-400/30 transition-all">
              <span className="text-xl shrink-0">{t.icon}</span>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">{t.tip}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
