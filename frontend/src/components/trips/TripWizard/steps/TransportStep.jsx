import React from 'react';

const TRANSPORTS = [
  { id: 'flight', title: 'Flight + Metro', desc: 'Fast long-distance & urban transit' },
  { id: 'train', title: 'Train / High Speed Rail', desc: 'Scenic & comfortable rail travel' },
  { id: 'bus', title: 'Express Bus / Coach', desc: 'Budget intercity transport' },
  { id: 'car', title: 'Car Rental / Self Drive', desc: 'Maximum flexibility & road trips' },
  { id: 'bike', title: 'Motorbike / Bicycle', desc: 'Agile city & coastal exploration' },
  { id: 'walk', title: 'Walking / Pedestrian', desc: 'Compact walkable city centers' },
  { id: 'metro', title: 'Public Metro & Bus', desc: 'Eco-friendly urban transit' },
  { id: 'mixed', title: 'Mixed Transport', desc: 'Optimal combination recommended by AI' },
];

export default function TransportStep({ form, onChange }) {
  return (
    <div className="space-y-3">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Primary Mode of Transport</label>
      <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
        {TRANSPORTS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange({ target: { name: 'transportation', value: t.id } })}
            className={`p-3 text-left rounded-xl border text-xs transition-all ${
              form.transportation === t.id
                ? 'border-amber-600 bg-amber-50 dark:bg-amber-900/40 text-amber-900 dark:text-amber-100 font-bold shadow-sm'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            <div className="font-bold">{t.title}</div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{t.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
