import React from 'react';
import { formatCurrency } from '../../../../utils/currencyFormatter';

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
  const dailyBudget = round(budget / days, 2);

  function round(val, dec) {
    return Number(Math.round(val + 'e' + dec) + 'e-' + dec);
  }

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 rounded-2xl text-white shadow-lg space-y-1">
        <span className="text-[10px] uppercase font-bold tracking-widest text-blue-200">Trip Overview</span>
        <h3 className="text-xl font-extrabold">{form.destination || 'Destination'}</h3>
        <p className="text-xs text-blue-100 font-medium">
          {form.start_date} to {form.end_date} • {days} Days • {form.travel_style || 'Solo'} Style
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <span className="text-gray-500 text-[10px] block font-bold uppercase">Total Budget</span>
          <span className="text-base font-extrabold text-emerald-600 dark:text-emerald-400">
            {formatCurrency(budget, currency)}
          </span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <span className="text-gray-500 text-[10px] block font-bold uppercase">Est. Daily Budget</span>
          <span className="text-base font-extrabold text-blue-600 dark:text-blue-400">
            {formatCurrency(dailyBudget, currency)} / day
          </span>
        </div>
      </div>

      <div className="space-y-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/60 p-3.5 rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500">Travelers:</span>
          <span className="font-bold">{form.adults || 1} Adult(s), {form.children || 0} Child(ren)</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500">Accommodation:</span>
          <span className="font-bold capitalize">{form.accommodation_preference || 'Hotel'}</span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500">Transport Mode:</span>
          <span className="font-bold capitalize">{form.transportation || 'Flight'}</span>
        </div>
        <div className="flex justify-between pb-1">
          <span className="font-semibold text-gray-500">Interests Selected:</span>
          <span className="font-bold truncate max-w-[180px]">{form.interests || 'Sightseeing'}</span>
        </div>
      </div>
    </div>
  );
}
