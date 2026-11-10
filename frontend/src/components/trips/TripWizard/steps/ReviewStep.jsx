import React from 'react';
import { formatCurrency } from '../../../../utils/currencyFormatter';

const TRANSPORT_MAP = {
  mixed: 'Mixed Transport',
  flight: 'Flight + Metro',
  train: 'Train / High Speed Rail',
  bus: 'Express Bus / Coach',
  car: 'Car Rental / Self Drive',
  bike: 'Motorbike / Bicycle',
  walk: 'Walking / Pedestrian',
  metro: 'Public Metro & Bus'
};

const AI_DIRECTIVE_MAP = {
  hidden_gems: 'Prioritize Hidden Gems',
  avoid_crowds: 'Avoid Crowds & Peak Hours',
  culture_first: 'Prioritize Local Culture & Heritage',
  outdoor_nature: 'Emphasize Nature & Landscapes',
  foodie_focus: 'Focus on Authentic Cuisine'
};

export default function ReviewStep({ form }) {
  const calculateDays = () => {
    if (!form.start_date || !form.end_date) return 1;
    const s = new Date(form.start_date);
    const e = new Date(form.end_date);
    const diff = Math.ceil((e - s) / (1000 * 60 * 60 * 24)) + 1;
    return diff > 0 ? diff : 1;
  };

  const days = calculateDays();
  const budget = parseFloat(form.budget) || 1000;
  const currency = form.currency || 'USD';
  const dailyBudget = Math.round((budget / days) * 100) / 100;

  const rawTransport = (form.transportation || '').toLowerCase().trim();
  const transportDisplay = TRANSPORT_MAP[rawTransport] || form.transportation || 'Mixed Transport';

  const rawDirectives = form.ai_preferences
    ? form.ai_preferences.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const directiveLabels = rawDirectives.map((d) => AI_DIRECTIVE_MAP[d] || d);

  return (
    <div className="space-y-4">
      {/* Overview Banner */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-4 rounded-2xl text-white shadow-lg space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-[10px] uppercase font-bold tracking-widest text-blue-200">Trip Overview</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-white/20 text-white uppercase tracking-wider">
            {form.budget_type || 'Mid-range'}
          </span>
        </div>
        <h3 className="text-xl font-extrabold">{form.destination || 'Destination'}</h3>
        <p className="text-xs text-blue-100 font-medium">
          From {form.origin_city || 'Origin'} • {form.start_date} to {form.end_date} • {days} Days • {form.travel_style || 'Solo'} Style
        </p>
      </div>

      {/* Financial Key Numbers */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Total Trip Budget</span>
          <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 block mt-0.5">
            {formatCurrency(budget, currency)}
          </span>
          <span className="text-[10px] text-gray-500 block mt-0.5">Includes Outbound + Return Transit</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Est. Daily Budget</span>
          <span className="text-base font-extrabold text-blue-600 dark:text-blue-400 block mt-0.5">
            {formatCurrency(dailyBudget, currency)} / day
          </span>
          <span className="text-[10px] text-gray-500 block mt-0.5">For {days} day(s) duration</span>
        </div>
      </div>

      {/* Structured Parameters Review */}
      <div className="space-y-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/60 p-3.5 rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Travelers:</span>
          <span className="font-bold">{form.adults || 1} Adult(s), {form.children || 0} Child(ren)</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Primary Transportation:</span>
          <span className="font-bold text-amber-600 dark:text-amber-400">{transportDisplay}</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Accommodation:</span>
          <span className="font-bold capitalize">{form.accommodation_preference || 'Hotel'}</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Pace & Routine:</span>
          <span className="font-bold capitalize">{form.activity_pace || 'balanced'} pace • Wake {form.wake_up_time || '08:00'}</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Interests Selected:</span>
          <span className="font-bold truncate max-w-[200px]" title={form.interests}>{form.interests || 'Sightseeing'}</span>
        </div>
        {directiveLabels.length > 0 && (
          <div className="flex justify-between pb-1">
            <span className="font-semibold text-gray-500 dark:text-gray-400">AI Directives:</span>
            <span className="font-bold text-purple-600 dark:text-purple-400 truncate max-w-[200px]">
              {directiveLabels.join(', ')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
