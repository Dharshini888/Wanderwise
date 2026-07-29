import { useState } from 'react';
import {
  IconShieldCheck,
  IconSearch,
  IconAlertCircle,
  IconAlertTriangle,
  IconPhone,
  IconLoader,
  IconShieldHalf,
  IconInfoCircle,
  IconBulb,
} from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

function RiskDial({ label, score, size = 100, isOverall = false }) {
  let color = 'text-emerald-500';
  let bgColor = 'text-emerald-500';
  if (score > 33) { color = 'text-amber-500'; bgColor = 'text-amber-500'; }
  if (score > 66) { color = 'text-red-500'; bgColor = 'text-red-500'; }

  const circumference = 2 * Math.PI * (size / 2 - 8);
  const offset = circumference - (score / 100) * circumference;
  
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle 
            cx={size/2} cy={size/2} r={size/2-8} 
            fill="none" 
            stroke="var(--border-color)" 
            strokeWidth={isOverall ? 8 : 6} 
          />
          <circle 
            cx={size/2} cy={size/2} r={size/2-8} 
            fill="none" 
            stroke="currentColor"
            className={bgColor}
            strokeWidth={isOverall ? 8 : 6}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-black font-heading ${color} ${isOverall ? 'text-2xl' : 'text-base'}`}>
            {score}%
          </span>
        </div>
      </div>
      <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">{label}</div>
    </div>
  );
}

export default function Safety() {
  const [destination, setDestination] = useState('');
  const [safetyData, setSafetyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const token = localStorage.getItem('token');

  const fetchSafety = async (e) => {
    e.preventDefault();
    if (!destination.trim()) return;
    setLoading(true); setError(''); setSafetyData(null);
    try {
      const res = await fetch(`${API}/safety/${encodeURIComponent(destination.trim())}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) setSafetyData(data);
      else setError(data.detail || 'Could not fetch safety info');
    } catch (_) { setError('Network error'); }
    setLoading(false);
  };

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconShieldCheck className="text-emerald-500" size={32} /> Safety Hub
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Real-time risk assessment, scam alerts, and emergency contacts.</p>
      </div>

      {/* Search */}
      <form onSubmit={fetchSafety} className="glass-card p-4 flex gap-3 bg-[var(--bg-card)]">
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--text-muted)]">
            <IconSearch size={18} />
          </span>
          <input 
            value={destination} 
            onChange={e => setDestination(e.target.value)} 
            placeholder="Check safety for: Paris, Brazil, Bangkok..." 
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/10"
          />
        </div>
        <button 
          type="submit" 
          disabled={loading || !destination.trim()}
          className="btn btn-primary px-6 font-semibold flex items-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
        >
          {loading ? <><IconLoader className="animate-spin" size={16} /> Checking...</> : 'Check Safety'}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-600 dark:text-red-400 text-sm font-semibold flex items-center gap-2">
          <IconAlertCircle size={20} /> {error}
        </div>
      )}

      {safetyData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn">
          
          {/* SOS Banner */}
          <div className="glass-card p-6 lg:col-span-2 flex justify-between items-center bg-red-50/50 dark:bg-red-950/10 border border-red-200/50 dark:border-red-900/10 rounded-2xl">
            <div>
              <h3 className="text-base font-bold text-red-600 dark:text-red-400 font-heading flex items-center gap-2 mb-1">
                <IconShieldHalf size={22} /> Emergency SOS
              </h3>
              <p className="text-xs text-red-700/70 dark:text-red-300/60 font-medium">Press and hold for immediate life-threatening emergency alert.</p>
            </div>
            <button 
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.9)'}
              onMouseUp={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                alert("🚨 EMERGENCY SOS INITIATED! Contacting local authorities...");
              }}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
              className="w-20 h-20 rounded-full bg-gradient-to-br from-red-500 to-red-700 text-white font-black text-lg shadow-lg shadow-red-500/30 cursor-pointer flex items-center justify-center transition-transform border-2 border-red-400/50"
            >
              SOS
            </button>
          </div>

          {/* Risk Assessment Dials */}
          <div className="glass-card p-8 flex flex-col items-center gap-6 bg-[var(--bg-card)]">
            <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">Risk Assessment</h3>
            <RiskDial label="Overall Risk" score={safetyData.overall_score || 0} size={150} isOverall={true} />
            <div className="flex gap-8 mt-2">
              <RiskDial label="Weather" score={safetyData.weather_risk || 0} size={80} />
              <RiskDial label="Crowd" score={safetyData.crowd_risk || 0} size={80} />
              <RiskDial label="Safety" score={safetyData.safety_risk || 0} size={80} />
            </div>
            <div className={`text-xs font-bold px-3 py-1 rounded-full mt-2 ${
              safetyData.overall_risk === 'Low' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400' :
              safetyData.overall_risk === 'Medium' ? 'bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400' :
              'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400'
            }`}>
              Status: {safetyData.overall_risk}
            </div>
          </div>

          {/* Emergency Numbers */}
          <div className="glass-card p-6 bg-[var(--bg-card)]">
            <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4 flex items-center gap-1.5">
              <IconPhone size={16} className="text-red-500" /> Local Emergency Numbers
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Police', val: safetyData.emergency_numbers.police, icon: '🚓' },
                { label: 'Ambulance', val: safetyData.emergency_numbers.ambulance, icon: '🚑' },
                { label: 'Fire', val: safetyData.emergency_numbers.fire, icon: '🚒' },
                { label: 'General', val: safetyData.emergency_numbers.general, icon: '🚨' }
              ].map(({ label, val, icon }) => (
                <div key={label} className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-xl p-4 flex items-center gap-3">
                  <span className="text-2xl">{icon}</span>
                  <div>
                    <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5">{label}</div>
                    <div className="text-lg font-black text-[var(--text-primary)] font-heading">{val || '112'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Common Scams */}
          <div className="glass-card p-6 lg:col-span-2 bg-[var(--bg-card)]">
            <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4 flex items-center gap-1.5">
              <IconAlertTriangle size={16} className="text-amber-500" /> Common Scams & Alerts
            </h3>
            <div className="flex flex-col gap-2.5">
              {safetyData.common_scams.map((scam, i) => (
                <div key={i} className="flex items-start gap-3 bg-amber-50/30 dark:bg-amber-950/5 border border-amber-100/50 dark:border-amber-900/10 p-3.5 rounded-xl">
                  <span className="text-amber-500 mt-0.5 flex-shrink-0"><IconAlertTriangle size={16} /></span>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">{scam}</p>
                </div>
              ))}
            </div>
          </div>
          
          {/* Recommended Actions */}
          {safetyData.recommended_actions && (
            <div className="glass-card p-6 lg:col-span-2 bg-[var(--bg-card)]">
              <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4 flex items-center gap-1.5">
                <IconBulb size={16} className="text-blue-500" /> Recommended Actions
              </h3>
              <div className="flex flex-col gap-2.5">
                {safetyData.recommended_actions.map((adv, i) => (
                  <div key={i} className="flex items-start gap-3 bg-blue-50/30 dark:bg-blue-950/5 border border-blue-100/50 dark:border-blue-900/10 p-3.5 rounded-xl">
                    <span className="text-blue-500 mt-0.5 flex-shrink-0"><IconInfoCircle size={16} /></span>
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-medium">{adv}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
