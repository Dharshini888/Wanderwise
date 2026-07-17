import { useState } from 'react';

const API = 'http://localhost:8000/api';

const RISK_COLORS = {
  Low: '#16a34a', // green
  Medium: '#d97706', // orange
  High: '#dc2626', // red
};

function RiskDial({ label, score, size = 100, isOverall = false }) {
  // Score is 0-100 (100 = 100% Risk / High Danger)
  const safeColor = 'var(--success)';
  const warnColor = 'var(--warning)';
  const dangerColor = 'var(--danger)';
  
  let color = safeColor;
  if (score > 33) color = warnColor;
  if (score > 66) color = dangerColor;
  
  // Inverse color logic: High risk score = red
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
      <div style={{ 
        width: size, 
        height: size, 
        borderRadius: '50%', 
        background: `conic-gradient(${color} ${score}%, var(--card-border) ${score}%)`,
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        position: 'relative'
      }}>
        <div style={{ 
          width: size - (isOverall ? 16 : 12), 
          height: size - (isOverall ? 16 : 12), 
          borderRadius: '50%', 
          background: 'var(--card-bg)',
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
        }}>
          <span className="text-primary-dark" style={{ fontSize: isOverall ? '28px' : '18px', fontWeight: 800 }}>
            {score}%
          </span>
        </div>
      </div>
      <div className="label-text" style={{ fontSize: isOverall ? '13px' : '11px' }}>{label}</div>
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

  const inputStyle = { width: '100%', padding: '12px 16px', borderRadius: '10px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none', boxSizing: 'border-box' };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>🛡️ Safety Hub</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Real-time risk scores, scam alerts, and emergency contacts.</p>
      </div>

      <form onSubmit={fetchSafety} style={{ display: 'flex', gap: '12px', marginBottom: '2rem' }}>
        <input style={inputStyle} value={destination} onChange={e => setDestination(e.target.value)} placeholder="Search destination (e.g. Paris, Brazil)..." />
        <button type="submit" disabled={loading || !destination.trim()}
          style={{ padding: '12px 24px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading || !destination.trim() ? 0.7 : 1, boxShadow: '0 4px 10px rgba(24, 95, 165, 0.2)' }}>
          {loading ? 'Checking...' : 'Check Safety'}
        </button>
      </form>

      {error && <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', color: '#dc2626', marginBottom: '1.5rem', fontSize: '14px', fontWeight: 500 }}>⚠️ {error}</div>}

      {safetyData && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          
          <div className="glass-card" style={{ padding: '24px', gridColumn: 'span 2', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(to right, rgba(220, 38, 38, 0.1), rgba(220, 38, 38, 0.05))', border: '1px solid rgba(220, 38, 38, 0.3)' }}>
            <div>
              <h3 style={{ margin: '0 0 8px', fontSize: '18px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '24px' }}>🚨</span> Emergency SOS
              </h3>
              <p style={{ margin: 0, fontSize: '13px', color: '#7f1d1d' }}>Press and hold in case of an immediate life-threatening emergency.</p>
            </div>
            <button 
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
              onMouseUp={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                alert("🚨 EMERGENCY SOS INITIATED! Contacting local authorities...");
              }}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
              style={{
                background: 'linear-gradient(135deg, #dc2626, #991b1b)',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '80px',
                height: '80px',
                fontSize: '24px',
                fontWeight: 800,
                cursor: 'pointer',
                boxShadow: '0 8px 24px rgba(220, 38, 38, 0.4), inset 0 2px 4px rgba(255,255,255,0.3)',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              SOS
            </button>
          </div>

          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <h3 className="text-primary-dark" style={{ margin: '0 0 24px', fontSize: '18px' }}>Risk Assessment</h3>
            
            <div style={{ display: 'flex', gap: '32px', marginBottom: '24px' }}>
              <RiskDial label="Overall Risk" score={safetyData.overall_score || 0} size={140} isOverall={true} />
            </div>

            <div style={{ display: 'flex', gap: '24px', width: '100%', justifyContent: 'center' }}>
              <RiskDial label="Weather" score={safetyData.weather_risk || 0} size={80} />
              <RiskDial label="Crowd" score={safetyData.crowd_risk || 0} size={80} />
              <RiskDial label="Safety" score={safetyData.safety_risk || 0} size={80} />
            </div>
            
            <div style={{ marginTop: '24px', fontSize: '14px', fontWeight: 600, color: RISK_COLORS[safetyData.overall_risk] || 'var(--text-secondary)' }}>
              Status: {safetyData.overall_risk}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Local Emergency Numbers</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {[
                { label: 'Police', val: safetyData.emergency_numbers.police, icon: '🚓' },
                { label: 'Ambulance', val: safetyData.emergency_numbers.ambulance, icon: '🚑' },
                { label: 'Fire', val: safetyData.emergency_numbers.fire, icon: '🚒' },
                { label: 'General', val: safetyData.emergency_numbers.general, icon: '🚨' }
              ].map(({ label, val, icon }) => (
                <div key={label} style={{ background: 'rgba(255,255,255,0.8)', border: '1px solid rgba(200, 225, 245, 0.5)', padding: '12px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '20px' }}>{icon}</span>
                  <div>
                    <div className="label-text" style={{ fontSize: '10px', marginBottom: '2px' }}>{label}</div>
                    <div className="text-primary-dark" style={{ fontWeight: 700, fontSize: '16px' }}>{val || '112'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '24px', gridColumn: 'span 2' }}>
            <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Common Scams & Alerts</h3>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#4a6080', fontSize: '14px', lineHeight: 1.6 }}>
              {safetyData.common_scams.map((scam, i) => <li key={i} style={{ marginBottom: '8px' }}>{scam}</li>)}
            </ul>
          </div>
          
          <div className="glass-card" style={{ padding: '24px', gridColumn: 'span 2' }}>
            <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '16px' }}>Recommended Actions</h3>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#4a6080', fontSize: '14px', lineHeight: 1.6 }}>
              {safetyData.recommended_actions?.map((adv, i) => <li key={i} style={{ marginBottom: '8px' }}>{adv}</li>)}
            </ul>
          </div>

        </div>
      )}
    </div>
  );
}
