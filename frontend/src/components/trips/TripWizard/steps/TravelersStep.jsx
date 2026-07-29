import React from 'react';

export default function TravelersStep({ form, onChange }) {
  const styles = [
    { id: 'solo', label: 'Solo Explorer', desc: 'Independent & flexible travel' },
    { id: 'couple', label: 'Couple / Romantic', desc: 'Romantic spots & dining' },
    { id: 'friends', label: 'Friends Group', desc: 'Social & nightlife focused' },
    { id: 'family', label: 'Family Trip', desc: 'Kid-friendly & relaxed pace' },
    { id: 'backpacking', label: 'Backpacker', desc: 'Budget & adventure heavy' },
    { id: 'luxury', label: 'Luxury Escapes', desc: 'High-end resorts & fine dining' },
  ];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2">Travel Style / Type</label>
        <div className="grid grid-cols-2 gap-2">
          {styles.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onChange({ target: { name: 'travel_style', value: s.id } })}
              className={`p-3 text-left rounded-xl border text-xs transition-all ${
                form.travel_style === s.id
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/40 text-blue-900 dark:text-blue-100 font-bold shadow-sm'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="font-bold">{s.label}</div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{s.desc}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 pt-2">
        <div>
          <label className="block text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">Adults</label>
          <input
            type="number"
            name="adults"
            min="1"
            value={form.adults || 1}
            onChange={onChange}
            className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
        <div>
          <label className="block text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">Children</label>
          <input
            type="number"
            name="children"
            min="0"
            value={form.children || 0}
            onChange={onChange}
            className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
        <div>
          <label className="block text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">Seniors</label>
          <input
            type="number"
            name="seniors"
            min="0"
            value={form.seniors || 0}
            onChange={onChange}
            className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
        <div>
          <label className="block text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">Pets</label>
          <input
            type="number"
            name="pets"
            min="0"
            value={form.pets || 0}
            onChange={onChange}
            className="w-full px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
      </div>
    </div>
  );
}
