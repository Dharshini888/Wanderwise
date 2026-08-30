import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import {
  IconChartBar,
  IconPlane,
  IconCalendar,
  IconCoin,
  IconLoader,
  IconTrendingUp,
} from '@tabler/icons-react';
import { calculateTripDuration } from '../utils/date_helpers';
import { getStoredUserId } from '../utils/formatters';

const API = 'http://localhost:8000/api';
const PIE_COLORS = ['#185FA5', '#0891b2', '#059669', '#d97706', '#7c3aed', '#db2777'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl px-4 py-3 shadow-xl text-xs">
        <p className="font-bold text-[var(--text-primary)] mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} className="text-[var(--text-secondary)]">
            {p.name}: <span className="font-bold text-[var(--color-primary-600)]">{p.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Analytics() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  const userId = getStoredUserId();

  useEffect(() => {
    if (!userId || userId === 'undefined' || String(userId) === 'undefined') { setLoading(false); return; }
    fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setTrips).catch(() => {}).finally(() => setLoading(false));
  }, [userId, token]);

  const getDays = (t) => calculateTripDuration(t.start_date, t.end_date);
  const totalTrips  = trips.length;
  const totalDays   = trips.reduce((acc, t) => acc + getDays(t), 0);
  const totalBudget = trips.reduce((acc, t) => acc + (t.budget || 0), 0);
  const avgBudget   = totalTrips > 0 ? Math.round(totalBudget / totalTrips) : 0;

  const typeData = Object.entries(
    trips.reduce((acc, t) => {
      const type = t.travel_type || 'other';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, count]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), count }));

  const monthData = trips.reduce((acc, t) => {
    const month = new Date(t.start_date).toLocaleString('default', { month: 'short', year: '2-digit' });
    acc[month] = (acc[month] || 0) + 1;
    return acc;
  }, {});
  const monthChartData = Object.entries(monthData).map(([name, count]) => ({ name, count }));

  const stats = [
    { label: 'Total Trips', value: totalTrips, sub: 'All time', icon: <IconPlane size={22} className="text-[var(--color-primary-600)]" />, bg: 'bg-blue-50 dark:bg-blue-950/20' },
    { label: 'Days Traveled', value: totalDays, sub: 'Total duration', icon: <IconCalendar size={22} className="text-emerald-500" />, bg: 'bg-emerald-50 dark:bg-emerald-950/20' },
    { label: 'Total Budgeted', value: `$${totalBudget.toLocaleString()}`, sub: 'Across all trips', icon: <IconCoin size={22} className="text-amber-500" />, bg: 'bg-amber-50 dark:bg-amber-950/20' },
    { label: 'Avg. Trip Budget', value: `$${avgBudget.toLocaleString()}`, sub: 'Per trip', icon: <IconTrendingUp size={22} className="text-purple-500" />, bg: 'bg-purple-50 dark:bg-purple-950/20' },
  ];

  return (
    <div className="flex flex-col gap-6 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconChartBar className="text-[var(--color-primary-600)]" size={32} /> Travel Analytics
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Insights and trends from your travel history.</p>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-16 text-[var(--text-muted)]">
          <IconLoader className="animate-spin text-[var(--color-primary-500)] mr-2" size={20} />
          <span className="text-sm font-semibold">Loading analytics...</span>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((s, i) => (
              <div key={i} className="glass-card p-5 bg-[var(--bg-card)] flex flex-col gap-3">
                <div className={`w-10 h-10 rounded-xl ${s.bg} flex items-center justify-center`}>
                  {s.icon}
                </div>
                <div>
                  <div className="text-2xl font-black text-[var(--text-primary)] font-heading leading-none mb-0.5">{s.value}</div>
                  <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">{s.label}</div>
                  <div className="text-[10px] text-[var(--color-primary-600)] font-semibold mt-0.5">{s.sub}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

            {/* Bar Chart – by travel type */}
            <div className="glass-card p-6 bg-[var(--bg-card)]">
              <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4">Trips by Travel Type</h3>
              {typeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={typeData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" name="Trips" fill="#185FA5" radius={[6, 6, 0, 0]} maxBarSize={48} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-60 flex items-center justify-center text-sm text-[var(--text-muted)] font-medium">
                  No trip data yet.
                </div>
              )}
            </div>

            {/* Pie Chart – distribution */}
            <div className="glass-card p-6 bg-[var(--bg-card)]">
              <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4">Travel Style Distribution</h3>
              {typeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={typeData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      dataKey="count"
                      nameKey="name"
                      paddingAngle={3}
                    >
                      {typeData.map((_, idx) => (
                        <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      formatter={(v) => <span className="text-xs text-[var(--text-secondary)] font-semibold">{v}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-60 flex items-center justify-center text-sm text-[var(--text-muted)] font-medium">
                  Not enough data.
                </div>
              )}
            </div>

            {/* Monthly trips bar */}
            {monthChartData.length > 0 && (
              <div className="glass-card p-6 bg-[var(--bg-card)] lg:col-span-2">
                <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-4">Trips Over Time</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={monthChartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="count" name="Trips" fill="#0891b2" radius={[6, 6, 0, 0]} maxBarSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
