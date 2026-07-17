import { useState } from 'react';

const API = 'http://localhost:8000/api';

const WMO_ICONS = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌧️', 55: '🌧️',
  56: '🌧️', 57: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌊',
  66: '🌧️', 67: '🌊',
  71: '❄️', 73: '❄️', 75: '🌨️', 77: '🌨️',
  80: '🌦️', 81: '⛈️', 82: '⛈️',
  85: '🌨️', 86: '🌨️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
};

const uvLabel = (uv) => {
  if (uv == null) return { label: 'N/A', color: '#5a7a9a' };
  if (uv <= 2) return { label: `${uv} Low`, color: '#16a34a' };
  if (uv <= 5) return { label: `${uv} Moderate`, color: '#d97706' };
  if (uv <= 7) return { label: `${uv} High`, color: '#ea580c' };
  if (uv <= 10) return { label: `${uv} Very High`, color: '#dc2626' };
  return { label: `${uv} Extreme`, color: '#7c3aed' };
};

const fmtTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit', hour12: true });
};

const fmtHour = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en', { hour: 'numeric', hour12: true });
};

export default function Weather() {
  const [city, setCity] = useState('');
  const [weather, setWeather] = useState(null);
  const [activities, setActivities] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingAct, setLoadingAct] = useState(false);
  const [error, setError] = useState('');

  const token = localStorage.getItem('token');

  const fetchWeather = async (e) => {
    e.preventDefault();
    if (!city.trim()) return;
    setLoading(true); setError(''); setWeather(null); setActivities(null);
    try {
      const res = await fetch(`${API}/weather/${encodeURIComponent(city.trim())}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) setWeather(data);
      else setError(data.detail || 'City not found');
    } catch (_) { setError('Network error — please try again'); }
    setLoading(false);
  };

  const fetchActivities = async () => {
    if (!weather) return;
    setLoadingAct(true); setActivities(null);
    try {
      const res = await fetch(`${API}/weather/activities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          destination: weather.city,
          weather_desc: weather.current.description,
          temperature: weather.current.temperature,
        }),
      });
      const data = await res.json();
      if (res.ok) setActivities(data);
    } catch (_) {}
    setLoadingAct(false);
  };

  const cur = weather?.current;
  const uv = cur ? uvLabel(cur.uv_index) : null;

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>
          Weather Intelligence
        </h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>
          Live forecasts powered by <strong>Open-Meteo</strong> — free &amp; accurate, no API key needed.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={fetchWeather} style={{ display: 'flex', gap: '12px', marginBottom: '2rem' }}>
        <input
          value={city}
          onChange={e => setCity(e.target.value)}
          placeholder="Search any city: Tokyo, Paris, Mumbai..."
          style={{
            flex: 1, padding: '12px 16px', borderRadius: '10px', border: '1px solid #c8dff0',
            background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '14px', outline: 'none'
          }}
        />
        <button
          type="submit"
          disabled={loading || !city.trim()}
          style={{
            padding: '12px 24px', background: '#185FA5', border: 'none', borderRadius: '10px',
            color: 'white', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading || !city.trim() ? 0.7 : 1, boxShadow: '0 4px 10px rgba(24, 95, 165, 0.2)',
            transition: 'all 0.2s ease',
          }}
        >
          {loading ? 'Searching...' : '🔍 Search'}
        </button>
      </form>

      {error && (
        <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.2)', borderRadius: '8px', padding: '12px', marginBottom: '1.5rem', color: '#dc2626', fontSize: '14px', fontWeight: 500 }}>
          ⚠️ {error}
        </div>
      )}

      {weather && cur && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* ── Main Current Weather Card ── */}
          <div className="glass-card" style={{ padding: '28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ fontSize: '5rem', lineHeight: 1, filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))' }}>
                {WMO_ICONS[cur.weather_code] || '🌡️'}
              </div>
              <div>
                <h2 className="text-primary-dark" style={{ margin: '0 0 2px', fontSize: '1.8rem', fontWeight: 800 }}>{weather.city}</h2>
                <div style={{ fontSize: '12px', color: '#5a7a9a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{weather.country}</div>
                <div style={{ fontSize: '13px', color: '#4a6080', marginTop: '6px' }}>{cur.description}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '40px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '4rem', fontWeight: 900, color: '#185FA5', lineHeight: 1 }}>{cur.temperature?.toFixed(0)}°C</div>
                <div style={{ fontSize: '13px', color: '#5a7a9a', marginTop: '4px' }}>Feels {cur.feels_like?.toFixed(0)}°C</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 24px', borderLeft: '1px solid rgba(200,225,245,0.9)', paddingLeft: '32px' }}>
                {[
                  { icon: '💧', label: 'Humidity', val: `${cur.humidity}%` },
                  { icon: '💨', label: 'Wind', val: `${cur.wind_speed} km/h ${cur.wind_direction}` },
                  { icon: '🌡️', label: 'Pressure', val: cur.pressure ? `${Math.round(cur.pressure)} hPa` : 'N/A' },
                  { icon: '👁️', label: 'Visibility', val: cur.visibility ? `${(cur.visibility / 1000).toFixed(1)} km` : 'N/A' },
                  { icon: '☀️', label: 'UV Index', val: uv.label, color: uv.color },
                  { icon: '🌧️', label: 'Precip', val: `${cur.precipitation ?? 0} mm` },
                ].map(({ icon, label, val, color }) => (
                  <div key={label} style={{ fontSize: '13px' }}>
                    <div style={{ color: '#5a7a9a', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', marginBottom: '2px' }}>{icon} {label}</div>
                    <div style={{ fontWeight: 700, color: color || '#1a2a3a' }}>{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Hourly Forecast (next 24h) ── */}
          {weather.hourly && weather.hourly.length > 0 && (
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '15px' }}>⏱️ Next 24 Hours</h3>
              <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
                {weather.hourly.slice(0, 24).map((h, i) => (
                  <div key={i} style={{
                    minWidth: '64px', textAlign: 'center', padding: '12px 8px',
                    background: i === 0 ? 'rgba(24,95,165,0.1)' : 'rgba(255,255,255,0.6)',
                    border: i === 0 ? '1px solid rgba(24,95,165,0.3)' : '1px solid rgba(200,225,245,0.5)',
                    borderRadius: '10px', flexShrink: 0,
                  }}>
                    <div style={{ fontSize: '11px', color: '#5a7a9a', fontWeight: 600, marginBottom: '6px' }}>
                      {i === 0 ? 'Now' : fmtHour(h.time)}
                    </div>
                    <div style={{ fontSize: '20px', marginBottom: '6px' }}>{WMO_ICONS[h.weather_code] || '🌡️'}</div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#1a2a3a' }}>{h.temperature?.toFixed(0)}°</div>
                    {h.precipitation_probability != null && (
                      <div style={{ fontSize: '10px', color: '#185FA5', marginTop: '4px' }}>{h.precipitation_probability}%💧</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── 7-day Forecast + AI Activities ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

            {/* 7-day forecast */}
            {weather.forecast && (
              <div className="glass-card" style={{ padding: '20px' }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 16px', fontSize: '15px' }}>📅 7-Day Forecast</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {weather.forecast.slice(0, 7).map((day, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '10px 0', borderBottom: i < 6 ? '1px solid rgba(200,225,245,0.5)' : 'none',
                    }}>
                      <div style={{ width: '40px', fontSize: '13px', color: '#4a6080', fontWeight: 600 }}>
                        {i === 0 ? 'Today' : new Date(day.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' })}
                      </div>
                      <div style={{ fontSize: '20px', width: '28px', textAlign: 'center' }}>
                        {WMO_ICONS[day.weather_code] || '🌡️'}
                      </div>
                      <div style={{ flex: 1, fontSize: '11px', color: '#5a7a9a', paddingLeft: '10px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {day.precipitation_probability != null && (
                          <span style={{ color: '#185FA5', fontWeight: 600 }}>{day.precipitation_probability}%💧</span>
                        )}
                        {day.uv_index_max != null && (
                          <span style={{ color: uvLabel(day.uv_index_max).color, fontWeight: 600 }}>UV {day.uv_index_max}</span>
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: '10px', fontSize: '13px' }}>
                        <span style={{ fontWeight: 800, color: '#1a2a3a' }}>{day.max_temp?.toFixed(0)}°</span>
                        <span style={{ color: '#5a7a9a' }}>{day.min_temp?.toFixed(0)}°</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Sunrise / Sunset today */}
                {weather.forecast[0]?.sunrise && (
                  <div style={{ display: 'flex', gap: '16px', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid rgba(200,225,245,0.5)' }}>
                    <div style={{ flex: 1, textAlign: 'center', background: 'rgba(251,191,36,0.1)', borderRadius: '8px', padding: '8px' }}>
                      <div style={{ fontSize: '18px' }}>🌅</div>
                      <div style={{ fontSize: '11px', color: '#5a7a9a', fontWeight: 600 }}>Sunrise</div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#d97706' }}>{fmtTime(weather.forecast[0].sunrise)}</div>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', background: 'rgba(99,102,241,0.08)', borderRadius: '8px', padding: '8px' }}>
                      <div style={{ fontSize: '18px' }}>🌇</div>
                      <div style={{ fontSize: '11px', color: '#5a7a9a', fontWeight: 600 }}>Sunset</div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#6366f1' }}>{fmtTime(weather.forecast[0].sunset)}</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI Activities */}
            <div>
              <div className="glass-card" style={{ padding: '20px', marginBottom: '1.5rem', background: 'rgba(24,95,165,0.04)', border: '1px solid rgba(24,95,165,0.15)' }}>
                <h3 className="text-primary-dark" style={{ margin: '0 0 10px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🤖</span> WanderWise AI Activities
                </h3>
                <p className="text-secondary" style={{ margin: '0 0 14px', fontSize: '13px', lineHeight: 1.5 }}>
                  Smart activity &amp; clothing recommendations for {weather.city} based on current conditions.
                </p>
                <button
                  onClick={fetchActivities}
                  disabled={loadingAct}
                  style={{
                    padding: '10px 16px', background: '#185FA5', border: 'none', borderRadius: '8px',
                    color: 'white', fontWeight: 600, cursor: loadingAct ? 'not-allowed' : 'pointer',
                    fontSize: '13px', width: '100%', opacity: loadingAct ? 0.7 : 1, transition: 'all 0.2s ease',
                  }}
                >
                  {loadingAct ? '⏳ Analyzing weather...' : '✨ Generate AI Recommendations'}
                </button>
              </div>

              {activities && (
                <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {activities.ai_suggestion && (
                    <div style={{ background: 'rgba(24,95,165,0.08)', padding: '12px 16px', borderRadius: '10px', fontSize: '13px', color: '#185FA5', lineHeight: 1.6, fontWeight: 500, borderLeft: '3px solid #185FA5' }}>
                      💡 {activities.ai_suggestion}
                    </div>
                  )}

                  {[
                    { title: 'Indoor Activities', items: activities.indoor_activities, icon: '🏠', color: '#185FA5' },
                    { title: 'Outdoor Activities', items: activities.outdoor_activities, icon: '🌳', color: '#16a34a' },
                  ].map(({ title, items, icon, color }) => (
                    <div key={title}>
                      <h4 style={{ margin: '0 0 8px', fontSize: '13px', color, display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}>
                        {icon} {title}
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {(items || []).slice(0, 3).map((act, i) => (
                          <div key={i} style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(200,225,245,0.6)', borderRadius: '8px', padding: '8px 12px' }}>
                            <div style={{ fontSize: '13px', fontWeight: 600, color: '#1a2a3a' }}>{act.name}</div>
                            <div style={{ fontSize: '11px', color: '#5a7a9a', marginTop: '2px' }}>{act.reason}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {activities.what_to_wear && (
                    <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(200,225,245,0.6)' }}>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: '#5a7a9a', textTransform: 'uppercase', marginBottom: '8px' }}>👗 What to Wear</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {activities.what_to_wear.map((item, i) => (
                          <span key={i} style={{ background: 'rgba(24,95,165,0.08)', border: '1px solid rgba(24,95,165,0.2)', borderRadius: '12px', padding: '4px 10px', fontSize: '12px', color: '#185FA5', fontWeight: 500 }}>
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
