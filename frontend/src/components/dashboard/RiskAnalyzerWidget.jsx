import { useState, useEffect } from 'react';
import { IconShieldHalf } from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

export default function RiskAnalyzerWidget({ trip, token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip) return;
    const fetchRisk = async () => {
      try {
        const dest = trip.destination.split(',')[0];
        const res = await fetch(`${API}/safety/risk-score`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ destination: dest, travel_dates: `${trip.start_date} to ${trip.end_date}`, budget: trip.budget || 1000 })
        });
        setData(await res.json());
      } catch (e) {}
      setLoading(false);
    };
    fetchRisk();
  }, [trip, token]);

  if (!trip) return null;
  if (loading) return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <div className="w-5 h-5 rounded-full border-2 border-red-500 border-t-transparent animate-spin"></div>
        <span>Evaluating safety advisory...</span>
      </div>
    </div>
  );
  if (!data || data.overall_score === undefined) return null;

  const isHighRisk = data.overall_score > 60;

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">
          Safety Analyzer
        </h3>
        <span className={`text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full ${
          isHighRisk 
            ? 'bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400' 
            : 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400'
        }`}>
          {data.overall_label || `${data.overall_score}% Risk`}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Weather Risk', val: data.weather_risk },
          { label: 'Crowd Risk', val: data.crowd_risk },
          { label: 'Safety Risk', val: data.safety_risk },
        ].map((r, i) => (
          <div key={i} className="bg-[var(--bg-app)] border border-[var(--border-color)] p-2.5 rounded-xl text-center">
            <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-1">{r.label}</div>
            <div className="text-base font-extrabold text-[var(--text-primary)]">{r.val || 0}%</div>
          </div>
        ))}
      </div>

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
