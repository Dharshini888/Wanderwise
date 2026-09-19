import { useState, useEffect } from 'react';
import { IconShieldHalf } from '@tabler/icons-react';
import api from '../../api/axios';

export default function RiskAnalyzerWidget({ trip }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip) return;
    const fetchRisk = async () => {
      try {
        const dest = trip.destination.split(',')[0];
        const res = await api.get(`/api/safety/dashboard?destination=${encodeURIComponent(dest)}`);
        const json = res.data;
        // Transform dashboard response into expected format
        setData({
          overall_score: json.dashboard?.overall_score || 0,
          overall_label: json.dashboard?.risk_label || 'Moderate',
          weather_risk: json.dashboard?.weather_risk || 0,
          crowd_risk: 15, // Default placeholder since dashboard doesn't provide crowd_risk directly
          safety_risk: json.dashboard?.overall_score ? 100 - json.dashboard.overall_score : 0,
          emergency_numbers: json.emergency_contacts || {}
        });
      } catch (e) {}
      setLoading(false);
    };
    fetchRisk();
  }, [trip]);

  if (!trip) return null;
  if (loading) return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <div className="w-5 h-5 rounded-full border-2 border-red-500 border-t-transparent animate-spin"></div>
        <span>Evaluating safety advisory...</span>
      </div>
    </div>
  );
  const hasLiveData = data && typeof data.overall_score === 'number' && data.overall_score > 0;
  const isHighRisk = data?.overall_score > 60;

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">
          Safety Analyzer
        </h3>
        <span className={`text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full ${
          !hasLiveData
            ? 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
            : isHighRisk 
            ? 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400' 
            : 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400'
        }`}>
          {!hasLiveData ? 'Not enough live data' : (data.overall_label || `${data.overall_score}% Risk`)}
        </span>
      </div>

      {!hasLiveData ? (
        <div className="p-3 rounded-xl bg-slate-500/5 border border-slate-500/10 text-xs text-[var(--text-muted)] font-medium text-center">
          Live regional telemetry limited for this destination. Emergency contacts and standard safety guidelines remain active below.
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: 'Weather Risk', val: data.weather_risk },
            { label: 'Crowd Risk', val: data.crowd_risk },
            { label: 'Safety Risk', val: data.safety_risk },
          ].map((r, i) => (
            <div key={i} className="bg-[var(--bg-app)] border border-[var(--border-color)] p-2.5 rounded-xl text-center">
              <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-1">{r.label}</div>
              <div className="text-base font-extrabold text-[var(--text-primary)]">{r.val !== undefined ? `${r.val}%` : 'N/A'}</div>
            </div>
          ))}
        </div>
      )}

      <div>
        <h4 className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1">
          <IconShieldHalf size={14} /> Emergency Contacts
        </h4>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(data.emergency_numbers || {}).slice(0, 4).map(([k, v]) => (
            <div key={k} className="text-xs bg-red-50/50 dark:bg-red-950/10 border border-red-100/50 dark:border-red-900/10 p-2 rounded-lg flex justify-between items-center">
              <span className="text-[var(--text-secondary)] capitalize font-medium">{k.replace('_', ' ')}:</span>
              <strong className="text-red-600 dark:text-red-400 font-bold">{v}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
