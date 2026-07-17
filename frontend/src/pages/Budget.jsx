import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const API = 'http://localhost:8000/api';

const CATEGORIES = ['accommodation', 'food', 'transport', 'activities', 'shopping', 'miscellaneous'];
const COLORS = ['#185FA5', '#0891b2', '#d97706', '#16a34a', '#dc2626', '#8b5cf6'];

export default function Budget() {
  const [searchParams] = useSearchParams();
  const preTrip = searchParams.get('trip');
  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(preTrip || '');
  const [expenses, setExpenses] = useState([]);
  const [total, setTotal] = useState(0);
  const [form, setForm] = useState({ category: 'food', amount: '', description: '', date: new Date().toISOString().split('T')[0] });
  const [adding, setAdding] = useState(false);
  const [loadingExp, setLoadingExp] = useState(false);
  const token = localStorage.getItem('token');

  let userId = null;
  try { const p = JSON.parse(atob(token.split('.')[1])); userId = p.sub || p.user_id || p.id; } catch (_) {}

  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setTrips).catch(() => {});
  }, [userId, token]);

  useEffect(() => {
    if (!selectedTrip) return;
    setLoadingExp(true);
    fetch(`${API}/expenses/${selectedTrip}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(d => { setExpenses(d.expenses || []); setTotal(d.total || 0); }).catch(() => {})
      .finally(() => setLoadingExp(false));
  }, [selectedTrip, token]);

  const addExpense = async (e) => {
    e.preventDefault();
    if (!selectedTrip) return alert('Select a trip first');
    setAdding(true);
    try {
      const res = await fetch(`${API}/expenses/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ...form, trip_id: parseInt(selectedTrip), amount: parseFloat(form.amount) }),
      });
      if (res.ok) {
        const data = await res.json();
        setExpenses(prev => [data, ...prev]);
        setTotal(prev => prev + parseFloat(form.amount));
        setForm({ category: 'food', amount: '', description: '', date: new Date().toISOString().split('T')[0] });
      }
    } catch (_) {}
    setAdding(false);
  };

  const selectedTripData = trips.find(t => t.id === parseInt(selectedTrip));
  const budget = selectedTripData?.budget || 0;
  const utilization = budget > 0 ? Math.min((total / budget) * 100, 100) : 0;
  const remaining = budget - total;

  // Prepare data for Recharts PieChart
  const byCategory = expenses.reduce((acc, e) => {
    acc[e.category] = (acc[e.category] || 0) + e.amount; return acc;
  }, {});
  
  const chartData = Object.entries(byCategory)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    borderRadius: '8px',
    border: '1px solid #c8dff0',
    background: 'rgba(255,255,255,0.9)',
    color: '#1a2a3a',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box'
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '6px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#5a7a9a',
    textTransform: 'uppercase'
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>
          Budget Manager
        </h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>
          Track expenses and analyze your travel spending.
        </p>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <label style={labelStyle}>Select Trip</label>
        <select 
          value={selectedTrip} 
          onChange={e => setSelectedTrip(e.target.value)}
          style={{ ...inputStyle, background: 'white', maxWidth: '400px' }}
        >
          <option value="">— Choose a trip —</option>
          {trips.map(t => <option key={t.id} value={t.id}>📍 {t.destination} ({t.start_date} → {t.end_date})</option>)}
        </select>
      </div>

      {selectedTripData && (
        <>
          {/* Budget overview */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { label: 'Trip Budget', value: `$${budget.toLocaleString()}`, color: '#185FA5' },
              { label: 'Spent', value: `$${total.toFixed(2)}`, color: total > budget ? '#dc2626' : '#d97706' },
              { label: remaining >= 0 ? 'Remaining' : 'Over Budget', value: `$${Math.abs(remaining).toFixed(2)}`, color: remaining >= 0 ? '#16a34a' : '#dc2626' },
            ].map(({ label, value, color }) => (
              <div key={label} className="glass-card" style={{ padding: '20px', textAlign: 'center' }}>
                <div className="label-text" style={{ marginBottom: '8px' }}>{label}</div>
                <div style={{ fontSize: '28px', fontWeight: 800, color }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="glass-card" style={{ padding: '20px', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#5a7a9a', marginBottom: '8px', fontWeight: 600 }}>
              <span>Budget Utilization</span>
              <span style={{ color: utilization > 90 ? '#dc2626' : '#1a2a3a' }}>{utilization.toFixed(1)}%</span>
            </div>
            <div style={{ background: 'rgba(24, 95, 165, 0.1)', borderRadius: '10px', height: '14px', overflow: 'hidden' }}>
              <div style={{ background: utilization > 90 ? '#dc2626' : '#185FA5', height: '100%', borderRadius: '10px', width: `${utilization}%`, transition: 'width 0.8s ease' }} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            {/* Add expense form */}
            <div>
              <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Add Expense</h3>
              <form className="glass-card" onSubmit={addExpense} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={labelStyle}>Category</label>
                  <select style={inputStyle} value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Amount (USD)</label>
                  <input style={inputStyle} type="number" step="0.01" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="0.00" required />
                </div>
                <div>
                  <label style={labelStyle}>Description</label>
                  <input style={inputStyle} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="e.g. Dinner at Nobu" />
                </div>
                <div>
                  <label style={labelStyle}>Date</label>
                  <input style={inputStyle} type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} required />
                </div>
                <button type="submit" disabled={adding}
                  style={{ padding: '12px', background: '#185FA5', border: 'none', borderRadius: '8px', color: 'white', fontWeight: 600, cursor: adding ? 'not-allowed' : 'pointer', opacity: adding ? 0.7 : 1, transition: 'all 0.2s', marginTop: '8px' }}>
                  {adding ? 'Adding...' : 'Add Expense'}
                </button>
              </form>
            </div>

            {/* Expense list & Chart */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              
              {chartData.length > 0 && (
                <div className="glass-card" style={{ padding: '24px', height: '300px', minHeight: 0, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
                  <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Spending Breakdown</h3>
                  <div style={{ flex: 1, minHeight: 0, minWidth: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value) => `$${value.toFixed(2)}`}
                          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              <div className="glass-card" style={{ padding: '24px', flex: 1 }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Expenses ({expenses.length})</h3>
                {loadingExp ? (
                  <div className="text-secondary" style={{ textAlign: 'center', padding: '2rem' }}>Loading...</div>
                ) : expenses.length === 0 ? (
                  <div className="text-secondary" style={{ textAlign: 'center', padding: '2rem', border: '1px dashed rgba(200, 225, 245, 0.9)', borderRadius: '12px' }}>
                    No expenses yet.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '350px', overflowY: 'auto', paddingRight: '8px' }}>
                    {expenses.map((exp, i) => (
                      <div key={exp.id || i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', background: 'rgba(255,255,255,0.6)', borderRadius: '10px', border: '1px solid rgba(200, 225, 245, 0.5)' }}>
                        <div>
                          <div className="text-primary-dark" style={{ fontWeight: 600, fontSize: '14px', marginBottom: '2px' }}>{exp.description || exp.category}</div>
                          <div className="text-muted" style={{ fontSize: '11px', textTransform: 'capitalize' }}>{exp.category} · {exp.date}</div>
                        </div>
                        <div style={{ fontWeight: 700, color: '#1a2a3a', fontSize: '15px' }}>${exp.amount.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
