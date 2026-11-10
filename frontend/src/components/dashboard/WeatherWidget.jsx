import { useState, useEffect } from 'react';
import { IconWind, IconDroplet, IconCloudRain } from '@tabler/icons-react';

const API = 'http://localhost:8000/api';
const WMO_ICONS = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌧️', 55: '🌧️',
  61: '🌧️', 63: '🌧️', 65: '🌊',
  71: '❄️', 73: '❄️', 75: '🌨️',
  80: '🌦️', 81: '⛈️', 82: '⛈️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
};

export default function WeatherWidget({ trip }) {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip) { setLoading(false); return; }
    const dest = trip.destination.split(',')[0];
    const cacheKey = `weather_dash_${dest}`;

    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed._ts < 30 * 60 * 1000) {
          setWeather(parsed); setLoading(false);
        }
      } catch (_) {}
    }

    const dateParam = trip.start_date ? `?date_str=${encodeURIComponent(String(trip.start_date).split('T')[0])}` : '';
    fetch(`${API}/weather/${encodeURIComponent(dest)}${dateParam}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && data.current) {
          data._ts = Date.now();
          setWeather(data);
          localStorage.setItem(cacheKey, JSON.stringify(data));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [trip]);

  if (!trip) return null;

  if (loading) return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <div className="w-5 h-5 rounded-full border-2 border-[var(--color-primary-500)] border-t-transparent animate-spin"></div>
        <span>Analyzing forecast...</span>
      </div>
    </div>
  );

  if (!weather || !weather.current) return (
    <div className="glass-card p-6">
      <div className="text-sm text-[var(--text-muted)] flex items-center gap-2">
        <IconCloudRain size={20} />
        <span>Weather currently unavailable for {trip.destination.split(',')[0]}</span>
      </div>
    </div>
  );

  const cur = weather.current;
  const icon = WMO_ICONS[cur.weather_code] || '🌡️';

  const todayStr = new Date().toISOString().split('T')[0];
  const startStr = trip?.start_date ? String(trip.start_date).split('T')[0] : null;
  const endStr = trip?.end_date ? String(trip.end_date).split('T')[0] : null;
  const isActive = startStr && endStr && (startStr <= todayStr && todayStr <= endStr);

  const tripMonth = startStr ? new Date(startStr + 'T00:00:00').toLocaleDateString('en-US', { month: 'long' }) : 'your trip';

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-0.5">
            {isActive ? 'Live Trip Weather' : 'Current Destination Weather (Today)'}
          </h3>
          <div className="text-lg font-bold text-[var(--text-primary)] font-heading">{weather.city}, {weather.country}</div>
          {!isActive && (
            <span className="text-[11px] text-amber-500 font-semibold block mt-0.5">
              * Expected weather during your travel in {tripMonth} may differ.
            </span>
          )}
        </div>
        <span className="text-4xl">{icon}</span>
      </div>

      <div className="flex items-baseline gap-3 my-1">
        <div className="text-4xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 font-heading">
          {cur.temperature?.toFixed(0)}°C
        </div>
        <div>
          <div className="text-sm font-semibold text-[var(--text-primary)] capitalize">{cur.description}</div>
          <div className="text-xs text-[var(--text-muted)]">Feels like {cur.feels_like?.toFixed(0)}°C</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {[
          { icon: <IconDroplet size={16} className="text-blue-500" />, label: 'Humidity', val: `${cur.humidity}%` },
          { icon: <IconWind size={16} className="text-teal-500" />, label: 'Wind', val: `${cur.wind_speed?.toFixed(0)} km/h` },
          { icon: <IconCloudRain size={16} className="text-indigo-500" />, label: 'Precip', val: `${cur.precipitation ?? 0} mm` },
        ].map(({ icon, label, val }) => (
          <div key={label} className="bg-[var(--bg-app)] border border-[var(--border-color)] rounded-xl p-2.5 flex flex-col items-center justify-center text-center">
            <div>{icon}</div>
            <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mt-1 mb-0.5">{label}</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">{val}</div>
          </div>
        ))}
      </div>

            {weather.forecast && (
        <div className="flex gap-2 pt-2 border-t border-[var(--border-color)]">
          {weather.forecast.slice(0, 3).map((day, i) => (
            <div key={i} className="flex-1 text-center py-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl">
              <div className="text-[10px] text-[var(--text-muted)] font-semibold mb-1">
                {i === 0 ? 'Today' : new Date(day.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' })}
              </div>
              <div className="text-lg">{WMO_ICONS[day.weather_code] || '🌤️'}</div>
              <div className="text-xs font-extrabold text-[var(--text-primary)] mt-1">{day.max_temp?.toFixed(0)}°</div>
            </div>
          ))}
        </div>
      )}

      {/* Provider & Timestamp Telemetry Footer */}
      <div className="pt-2 border-t border-[var(--border-color)] flex items-center justify-between text-[10px] text-[var(--text-muted)] font-medium">
        <span className="flex items-center gap-1">
          📡 <span>{weather.provider || 'Open-Meteo Weather Service'}</span>
        </span>
        <span>{weather.timestamp ? `Updated: ${weather.timestamp}` : 'Live Telemetry'}</span>
      </div>
    </div>
  );;
}
