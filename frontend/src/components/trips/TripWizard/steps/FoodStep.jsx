import React from 'react';

const FOOD_PREFS = [
  'Vegetarian', 'Vegan', 'Halal', 'Jain', 'Kosher', 'Seafood',
  'Street Food', 'Fine Dining', 'Local Delicacies', 'Cafes & Bakeries'
];

export default function FoodStep({ form, onChange, onToggleFood }) {
  const selectedFood = form.food_preferences ? form.food_preferences.split(',').map(s => s.trim()) : [];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2">Dietary & Dining Preferences</label>
        <div className="grid grid-cols-2 gap-2">
          {FOOD_PREFS.map((fp) => {
            const isSel = selectedFood.includes(fp);
            return (
              <button
                key={fp}
                type="button"
                onClick={() => onToggleFood(fp)}
                className={`p-2.5 rounded-xl border text-xs text-left transition-all ${
                  isSel
                    ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-900/40 text-emerald-900 dark:text-emerald-100 font-bold'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                }`}
              >
                {fp}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Food Allergies & Restrictions</label>
        <input
          type="text"
          name="food_allergies"
          value={form.food_allergies || ''}
          onChange={onChange}
          placeholder="e.g. Peanuts, Gluten, Dairy, Shellfish"
          className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
        />
      </div>
    </div>
  );
}
