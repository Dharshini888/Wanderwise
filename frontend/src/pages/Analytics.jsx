import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API = 'http://localhost:8000/api';

export default function Analytics() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  let userId = null;
  try { const p = JSON.parse(atob(token.split('.')[1])); userId = p.sub || p.user_id || p.id; } catch (_) {}

  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setTrips).catch(() => {}).finally(() => setLoading(false));
  }, [userId, token]);

  const getDays = (t) => Math.round((new Date(t.end_date) - new Date(t.start_date)) / 86400000) + 1;
  const totalTrips = trips.length;
  const totalDays = trips.reduce((acc, t) => acc + getDays(t), 0);
  const totalBudget = trips.reduce((acc, t) => acc + (t.budget || 0), 0);

  // Group by travel type
  const typeData = trips.reduce((acc, t) => {
    const type = t.travel_type || 'other';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});
  
  const chartData = Object.entries(typeData).map(([name, count]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    count
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>📈 Travel Analytics</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Overview of your travel history and trends.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
        {[
          { label: 'Total Trips', val: totalTrips, sub: 'All time' },
          { label: 'Days Traveling', val: totalDays, sub: 'Total duration' },
          { label: 'Total Budgeted', val: `$${totalBudget.toLocaleString()}`, sub: 'Across all trips' }
        ].map((stat, i) => (
          <div key={i} className="glass-card" style={{ padding: '24px', textAlign: 'center' }}>
            <div className="label-text" style={{ marginBottom: '8px' }}>{stat.label}</div>
            <div className="text-primary-dark" style={{ fontSize: '36px', fontWeight: 800, lineHeight: 1 }}>{stat.val}</div>
            <div style={{ fontSize: '12px', color: '#185FA5', marginTop: '8px', fontWeight: 500 }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="glass-card" style={{ padding: '24px', height: '400px', minHeight: 0, minWidth: 0, marginTop: '1rem', display: 'flex', flexDirection: 'column' }}>
        <h3 className="text-primary-dark" style={{ margin: '0 0 20px', fontSize: '16px' }}>Trips by Travel Type</h3>
        {chartData.length > 0 ? (
          <div style={{ flex: 1, minHeight: 0, minWidth: 0 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(200, 225, 245, 0.5)" vertical={false} />
                <XAxis dataKey="name" stroke="#5a7a9a" tick={{ fill: '#4a6080', fontSize: 12 }} />
                <YAxis stroke="#5a7a9a" tick={{ fill: '#4a6080', fontSize: 12 }} allowDecimals={false} />
                <Tooltip 
                  cursor={{ fill: 'rgba(24, 95, 165, 0.05)' }} 
                  contentStyle={{ borderRadius: '8px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.95)', boxShadow: '0 4px 20px rgba(24, 95, 165, 0.1)' }}
                />
                <Bar dataKey="count" fill="#185FA5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#5a7a9a' }}>
            {loading ? 'Loading data...' : 'Not enough data to display charts.'}
          </div>
        )}
      </div>
    </div>
  );
}
