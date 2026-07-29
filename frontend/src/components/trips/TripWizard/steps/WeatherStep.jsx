import React from 'react';

const WEATHER_MODES = [
  { id: 'mix', title: 'Balanced Mix', desc: 'Mix of outdoor sights & indoor cafes/museums' },
  { id: 'indoor', title: 'Indoor Preferred', desc: 'Prioritize museums, galleries & covered arcades' },
  { id: 'outdoor', title: 'Outdoor Preferred', desc: 'Prioritize parks, beaches & open-air viewpoints' },
  { id: 'heat_sensitive', title: 'Heat Sensitive', desc: 'Avoid midday sun, prioritize air-conditioned spots' },
  { id: 'rain_backup', title: 'Rain Backup Included', desc: 'Generate indoor backup alternatives for every outdoor spot' },
];

export default function WeatherStep({ form, onChange }) {
  return (
    <div className="space-y-3">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Weather & Climate Sensitivity</label>
      <div className="space-y-2">
        {WEATHER_MODES.map((w) => (
          <button
            key={w.id}
            type="button"
            onClick={() => onChange({ target: { name: 'weather_preference', value: w.id } })}
            className={`w-full p-3 text-left rounded-xl border text-xs transition-all ${
              form.weather_preference === w.id
                ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/40 text-blue-900 dark:text-blue-100 font-bold shadow-sm'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            <div className="font-bold">{w.title}</div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{w.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
