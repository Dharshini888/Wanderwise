import React from 'react';

const AI_OPTS = [
  { id: 'avoid_crowds', title: 'Avoid Crowds', desc: 'Visit attractions during off-peak hours' },
  { id: 'tourist_traps', title: 'Avoid Tourist Traps', desc: 'Prioritize authentic local spots over overpriced venues' },
  { id: 'hidden_gems', title: 'Prioritize Hidden Gems', desc: 'Discover lesser known secret spots' },
  { id: 'instagram_spots', title: 'Instagram Photography', desc: 'Highlight photogenic & scenic viewpoints' },
  { id: 'local_experiences', title: 'Local Culture', desc: 'Workshops, street markets & local interactions' },
];

export default function AiPreferencesStep({ form, onToggleAiPref }) {
  const selectedAi = form.ai_preferences ? form.ai_preferences.split(',').map(s => s.trim()) : [];

  return (
    <div className="space-y-3">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">AI Recommendation Directives</label>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {AI_OPTS.map((a) => {
          const isSel = selectedAi.includes(a.id);
          return (
            <button
              key={a.id}
              type="button"
              onClick={() => onToggleAiPref(a.id)}
              className={`w-full p-3 text-left rounded-xl border text-xs transition-all ${
                isSel
                  ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-900 dark:text-indigo-100 font-bold shadow-sm'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            >
              <div className="font-bold">{a.title}</div>
              <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{a.desc}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
