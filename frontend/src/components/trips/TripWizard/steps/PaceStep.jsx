import React from 'react';

const PACES = [
  { id: 'relaxed', title: 'Relaxed & Slow Travel', desc: '2-3 spots per day with ample coffee breaks' },
  { id: 'balanced', title: 'Balanced & Steady', desc: '4-6 spots per day blending highlights & downtime' },
  { id: 'fast_paced', title: 'Fast-Paced Explorer', desc: '6-8 spots per day maximizing sightseeing' },
  { id: 'packed', title: 'Packed & Action-Filled', desc: '8-10 spots per day covering all landmarks' },
];

export default function PaceStep({ form, onChange }) {
  return (
    <div className="space-y-4">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Daily Sightseeing Pace</label>
      <div className="grid grid-cols-2 gap-3">
        {PACES.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => onChange({ target: { name: 'activity_pace', value: p.id } })}
            className={`p-3.5 text-left rounded-xl border text-xs transition-all ${
              form.activity_pace === p.id
                ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/40 text-purple-900 dark:text-purple-100 font-bold shadow-sm'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            <div className="font-bold text-sm">{p.title}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1">{p.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
