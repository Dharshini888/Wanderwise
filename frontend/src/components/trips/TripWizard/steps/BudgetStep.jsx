import React from 'react';
import { formatCurrency } from '../../../../utils/currencyFormatter';

export default function BudgetStep({ form, onChange, currencyList = [] }) {
  const bAmount = parseFloat(form.budget) || 1000;
  const currCode = form.currency || 'USD';

  // Dynamic travel style allocation calculation
  const getAllocationPercentages = (style) => {
    const s = (style || '').toLowerCase();
    if (s.includes('luxury')) return { lodg: 55, food: 20, trans: 10, act: 10, emerg: 5 };
    if (s.includes('backpack')) return { lodg: 25, food: 25, trans: 25, act: 20, emerg: 5 };
    if (s.includes('family')) return { lodg: 40, food: 25, trans: 15, act: 15, emerg: 5 };
    if (s.includes('business')) return { lodg: 45, trans: 25, food: 15, act: 10, emerg: 5 };
    return { lodg: 40, food: 20, trans: 20, act: 15, emerg: 5 };
  };

  const p = getAllocationPercentages(form.travel_style);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Total Trip Budget *</label>
          <input
            type="number"
            name="budget"
            required
            min="50"
            value={form.budget}
            onChange={onChange}
            className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Currency *</label>
          <select
            name="currency"
            value={form.currency}
            onChange={onChange}
            className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          >
            {currencyList.length > 0 ? (
              currencyList.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} ({c.symbol}) - {c.country || c.name}
                </option>
              ))
            ) : (
              ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'AED', 'SGD', 'CHF'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))
            )}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Budget Comfort Tier</label>
        <div className="grid grid-cols-4 gap-2">
          {['Budget', 'Mid-range', 'Luxury', 'Ultra Luxury'].map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => onChange({ target: { name: 'budget_type', value: tier } })}
              className={`py-2 px-1 text-center rounded-xl text-xs font-bold border transition-all ${
                form.budget_type === tier
                  ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200'
                  : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Pre-calculated Category Allocations */}
      <div className="p-3 bg-gray-50 dark:bg-gray-800/80 rounded-2xl border border-gray-200 dark:border-gray-700 space-y-2">
        <span className="text-xs font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
          Smart Budget Allocation ({form.travel_style || 'Standard'})
        </span>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl">
            <span className="text-[10px] text-gray-500 block">Lodging ({p.lodg}%)</span>
            <span className="font-extrabold text-blue-600 dark:text-blue-400">{formatCurrency(bAmount * (p.lodg / 100), currCode)}</span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl">
            <span className="text-[10px] text-gray-500 block">Food ({p.food}%)</span>
            <span className="font-extrabold text-emerald-600 dark:text-emerald-400">{formatCurrency(bAmount * (p.food / 100), currCode)}</span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl">
            <span className="text-[10px] text-gray-500 block">Transport ({p.trans}%)</span>
            <span className="font-extrabold text-amber-600 dark:text-amber-400">{formatCurrency(bAmount * (p.trans / 100), currCode)}</span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl">
            <span className="text-[10px] text-gray-500 block">Activities ({p.act}%)</span>
            <span className="font-extrabold text-indigo-600 dark:text-indigo-400">{formatCurrency(bAmount * (p.act / 100), currCode)}</span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl">
            <span className="text-[10px] text-gray-500 block">Emergency ({p.emerg}%)</span>
            <span className="font-extrabold text-rose-600 dark:text-rose-400">{formatCurrency(bAmount * (p.emerg / 100), currCode)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
