import { useState } from 'react';
import {
  IconSun,
  IconCloudRain,
  IconSearch,
  IconDroplet,
  IconWind,
  IconGauge,
  IconEye,
  IconAlertCircle,
  IconSunrise,
  IconSunset,
  IconSparkles,
  IconLoader,
  IconShirt,
  IconUser,
  IconCalendar,
  IconClock,
} from '@tabler/icons-react';

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
  if (uv == null) return { label: 'N/A', color: 'text-slate-500 bg-slate-50' };
  if (uv <= 2) return { label: `${uv} Low`, color: 'text-green-600 bg-green-50' };
  if (uv <= 5) return { label: `${uv} Mod`, color: 'text-amber-600 bg-amber-50' };
  if (uv <= 7) return { label: `${uv} High`, color: 'text-orange-600 bg-orange-50' };
  if (uv <= 10) return { label: `${uv} Very High`, color: 'text-red-600 bg-red-50' };
  return { label: `${uv} Extreme`, color: 'text-purple-600 bg-purple-50' };
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
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconSun className="text-amber-500" size={32} /> Weather Intelligence
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">
          Live forecasts powered by Open-Meteo. Discover clothing tips and matching activities.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={fetchWeather} className="glass-card p-4 flex gap-3 bg-[var(--bg-card)]">
        <div className="relative flex-1">
          <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[var(--text-muted)]">
            <IconSearch size={18} />
          </span>
          <input
            value={city}
            onChange={e => setCity(e.target.value)}
            placeholder="Search any city: Tokyo, Paris, Mumbai..."
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/10"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !city.trim()}
          className="btn btn-primary px-6 py-3 font-semibold flex items-center gap-1.5 shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <>
              <IconLoader className="animate-spin" size={16} />
              <span>Searching...</span>
            </>
          ) : (
            <span>Search</span>
          )}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-600 dark:text-red-400 text-sm font-semibold flex items-center gap-2">
          <IconAlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {weather && cur && (
        <div className="flex flex-col gap-6 animate-fadeIn">

          {/* Current Weather Card */}
          <div className="glass-card p-6 sm:p-8 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 bg-[var(--bg-card)]">
            <div className="flex items-center gap-6">
              <span className="text-7xl drop-shadow-md">{WMO_ICONS[cur.weather_code] || '🌡️'}</span>
              <div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1">{weather.city}</h2>
                <div className="text-[10px] text-[var(--text-muted)] font-bold tracking-wider uppercase">{weather.country}</div>
                <div className="text-sm font-semibold text-[var(--text-secondary)] mt-2 capitalize">{cur.description}</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-8 items-center border-t lg:border-t-0 lg:border-l border-[var(--border-color)] pt-6 lg:pt-0 lg:pl-8 w-full lg:w-auto">
              <div className="text-center lg:text-left">
                <div className="text-5xl font-black text-[var(--color-primary-600)] dark:text-blue-400 font-heading leading-none">
                  {cur.temperature?.toFixed(0)}°C
                </div>
                <div className="text-xs text-[var(--text-muted)] mt-1.5 font-medium">Feels like {cur.feels_like?.toFixed(0)}°C</div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 flex-1">
                {[
                  { icon: <IconDroplet size={14} className="text-blue-500" />, label: 'Humidity', val: `${cur.humidity}%` },
                  { icon: <IconWind size={14} className="text-teal-500" />, label: 'Wind', val: `${cur.wind_speed} km/h` },
                  { icon: <IconGauge size={14} className="text-purple-500" />, label: 'Pressure', val: cur.pressure ? `${Math.round(cur.pressure)} hPa` : 'N/A' },
                  { icon: <IconEye size={14} className="text-pink-500" />, label: 'Visibility', val: cur.visibility ? `${(cur.visibility / 1000).toFixed(1)} km` : 'N/A' },
                  { icon: <IconSun size={14} className="text-amber-500" />, label: 'UV Index', val: uv.label, badge: uv.color },
                  { icon: <IconCloudRain size={14} className="text-indigo-500" />, label: 'Precipitation', val: `${cur.precipitation ?? 0} mm` },
                ].map(({ icon, label, val, badge }) => (
                  <div key={label} className="text-xs">
                    <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                      {icon} {label}
                    </div>
                    {badge ? (
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${badge}`}>{val}</span>
                    ) : (
                      <span className="font-bold text-[var(--text-primary)]">{val}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Hourly Forecast */}
          {weather.hourly && weather.hourly.length > 0 && (
            <div className="glass-card p-6 bg-[var(--bg-card)]">
              <h3 className="text-base font-bold text-[var(--text-primary)] font-heading mb-4 flex items-center gap-2">
                <IconClock size={20} className="text-[var(--color-primary-500)]" /> Next 24 Hours
              </h3>
              <div className="flex gap-3 overflow-x-auto pb-3 custom-scrollbar">
                {weather.hourly.slice(0, 24).map((h, i) => (
                  <div 
                    key={i} 
                    className={`min-w-[70px] text-center py-3.5 px-2.5 rounded-xl border flex flex-col items-center justify-center ${
                      i === 0 
                        ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800' 
                        : 'bg-[var(--bg-app)] border-[var(--border-color)]'
                    }`}
                  >
                    <div className="text-[10px] text-[var(--text-muted)] font-bold mb-2">
                      {i === 0 ? 'Now' : fmtHour(h.time)}
                    </div>
                    <div className="text-2xl mb-2">{WMO_ICONS[h.weather_code] || '🌡️'}</div>
                    <div className="text-sm font-extrabold text-[var(--text-primary)]">{h.temperature?.toFixed(0)}°</div>
                    {h.precipitation_probability != null && (
                      <div className="text-[9px] font-bold text-blue-500 mt-2">{h.precipitation_probability}%💧</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 7-Day Forecast & AI Activities */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

            {/* 7-Day Forecast */}
            {weather.forecast && (
              <div className="glass-card p-6 bg-[var(--bg-card)]">
                <h3 className="text-base font-bold text-[var(--text-primary)] font-heading mb-4 flex items-center gap-2">
                  <IconCalendar size={20} className="text-[var(--color-primary-500)]" /> 7-Day Forecast
                </h3>
                <div className="flex flex-col gap-1">
                  {weather.forecast.slice(0, 7).map((day, i) => (
                    <div key={i} className="flex items-center justify-between py-3 border-b border-[var(--border-color)] last:border-b-0">
                      <div className="w-14 text-xs font-bold text-[var(--text-secondary)]">
                        {i === 0 ? 'Today' : new Date(day.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' })}
                      </div>
                      <div className="text-2xl w-10 text-center">
                        {WMO_ICONS[day.weather_code] || '🌡️'}
                      </div>
                      <div className="flex-1 text-xs text-[var(--text-muted)] px-3 flex gap-4">
                        {day.precipitation_probability != null && (
                          <span className="text-blue-500 font-bold">{day.precipitation_probability}% 💧</span>
                        )}
                        {day.uv_index_max != null && (
                          <span className="font-semibold">UV {day.uv_index_max}</span>
                        )}
                      </div>
                      <div className="flex gap-3 text-xs font-bold font-heading">
                        <span className="text-[var(--text-primary)]">{day.max_temp?.toFixed(0)}°</span>
                        <span className="text-[var(--text-muted)]">{day.min_temp?.toFixed(0)}°</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Sunrise / Sunset */}
                {weather.forecast[0]?.sunrise && (
                  <div className="flex gap-4 mt-6 pt-5 border-t border-[var(--border-color)]">
                    <div className="flex-1 text-center bg-amber-50/50 dark:bg-amber-950/10 border border-amber-100 dark:border-amber-900/10 rounded-xl p-3.5">
                      <IconSunrise className="text-amber-500 mx-auto mb-1.5" size={24} />
                      <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-0.5">Sunrise</div>
                      <div className="text-xs font-extrabold text-amber-600 dark:text-amber-400 font-heading">{fmtTime(weather.forecast[0].sunrise)}</div>
                    </div>
                    <div className="flex-1 text-center bg-indigo-50/50 dark:bg-indigo-950/10 border border-indigo-100 dark:border-indigo-900/10 rounded-xl p-3.5">
                      <IconSunset className="text-indigo-500 mx-auto mb-1.5" size={24} />
                      <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-0.5">Sunset</div>
                      <div className="text-xs font-extrabold text-indigo-600 dark:text-indigo-400 font-heading">{fmtTime(weather.forecast[0].sunset)}</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI Advisor Panel */}
            <div className="flex flex-col gap-6">
              
              <div className="glass-card p-6 bg-blue-50/10 dark:bg-blue-950/5 border border-blue-200/50 dark:border-blue-900/10 flex flex-col gap-3">
                <h3 className="text-base font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
                  <IconSparkles className="text-amber-500 animate-pulse" size={20} /> AI Travel Guide
                </h3>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  Generate activity ideas and dress code guides optimized for {weather.city}'s exact weather conditions.
                </p>
                <button
                  onClick={fetchActivities}
                  disabled={loadingAct}
                  className="btn btn-primary w-full py-3 text-sm font-semibold flex items-center justify-center gap-2 shadow-md shadow-blue-500/10"
                >
                  {loadingAct ? (
                    <>
                      <IconLoader className="animate-spin" size={16} />
                      <span>Analyzing conditions...</span>
                    </>
                  ) : (
                    <span>Generate AI Suggestions</span>
                  )}
                </button>
              </div>

              {activities && (
                <div className="glass-card p-6 flex flex-col gap-5 bg-[var(--bg-card)] animate-fadeIn">
                  
                  {activities.ai_suggestion && (
                    <div className="bg-blue-50/50 dark:bg-blue-950/20 border-l-4 border-[var(--color-primary-500)] p-4 rounded-r-xl text-xs text-[var(--text-secondary)] leading-relaxed font-medium">
                      💡 {activities.ai_suggestion}
                    </div>
                  )}

                  {[
                    { title: 'Recommended Indoor', items: activities.indoor_activities, icon: '🏠', color: 'text-blue-500' },
                    { title: 'Recommended Outdoor', items: activities.outdoor_activities, icon: '🌳', color: 'text-emerald-500' },
                  ].map(({ title, items, icon, color }) => (
                    <div key={title} className="flex flex-col gap-2">
                      <h4 className={`text-xs font-bold ${color} uppercase tracking-wider flex items-center gap-1.5`}>
                        <span className="text-base">{icon}</span> {title}
                      </h4>
                      <div className="flex flex-col gap-2">
                        {(items || []).slice(0, 3).map((act, i) => (
                          <div key={i} className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-xl p-3 shadow-sm">
                            <div className="text-xs font-bold text-[var(--text-primary)] font-heading">{act.name}</div>
                            <div className="text-[10px] text-[var(--text-muted)] mt-1 font-medium">{act.reason}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {activities.what_to_wear && (
                    <div className="pt-4 border-t border-[var(--border-color)]">
                      <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                        <IconShirt size={16} className="text-purple-500" /> Clothes Advisor
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {activities.what_to_wear.map((item, i) => (
                          <span key={i} className="text-[10px] font-bold bg-blue-50 dark:bg-blue-950 text-[var(--color-primary-600)] dark:text-blue-400 px-3 py-1.5 rounded-full border border-blue-100 dark:border-blue-900 uppercase tracking-wider">
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
