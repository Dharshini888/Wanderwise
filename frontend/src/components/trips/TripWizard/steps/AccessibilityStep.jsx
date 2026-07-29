import React from 'react';

const ACCESS_OPTIONS = [
  'Wheelchair Accessible', 'Senior Friendly', 'Kid Friendly',
  'Avoid Steep Hills', 'Avoid Long Walking', 'Elevator Access Required'
];

export default function AccessibilityStep({ form, onToggleAccess }) {
  const selectedAccess = form.accessibility ? form.accessibility.split(',').map(s => s.trim()) : [];

  return (
    <div className="space-y-4">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Accessibility & Comfort Requirements</label>
      <div className="grid grid-cols-2 gap-2">
        {ACCESS_OPTIONS.map((opt) => {
          const isSel = selectedAccess.includes(opt);
          return (
            <button
              key={opt}
              type="button"
              onClick={() => onToggleAccess(opt)}
              className={`p-3 rounded-xl border text-xs text-left transition-all ${
                isSel
                  ? 'border-cyan-600 bg-cyan-50 dark:bg-cyan-900/40 text-cyan-900 dark:text-cyan-100 font-bold'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}
