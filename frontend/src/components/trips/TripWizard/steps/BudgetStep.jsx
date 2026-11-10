import React from 'react';
import { formatCurrency } from '../../../../utils/currencyFormatter';

const TIER_CONFIG = {
  budget: {
    label: 'Budget',
    desc: 'Economical accommodation, public transit & free activities',
    pcts: { outbound: 25, returnTrans: 25, lodging: 18, food: 14, localTrans: 5, act: 6, fees: 2, contingency: 5 }
  },
  mid_range: {
    label: 'Mid-range',
    desc: 'Standard hotels, balanced dining & cultural attractions',
    pcts: { outbound: 22, returnTrans: 22, lodging: 24, food: 14, localTrans: 5, act: 8, fees: 1, contingency: 4 }
  },
  luxury: {
    label: 'Luxury',
    desc: 'High-comfort hotels, private transfers & fine dining',
    pcts: { outbound: 18, returnTrans: 18, lodging: 32, food: 16, localTrans: 6, act: 7, fees: 1, contingency: 2 }
  },
  ultra_luxury: {
    label: 'Ultra Luxury',
    desc: 'Signature luxury stays, private chauffeurs & VIP access',
    pcts: { outbound: 16, returnTrans: 16, lodging: 38, food: 16, localTrans: 5, act: 6, fees: 1, contingency: 2 }
  }
};

function normalizeTierKey(tier) {
  if (!tier) return 'mid_range';
  const clean = String(tier).toLowerCase().replace(/-/g, '_').trim();
  if (clean.includes('ultra')) return 'ultra_luxury';
  if (clean.includes('luxury')) return 'luxury';
  if (clean.includes('budget') || clean.includes('backpack')) return 'budget';
  return 'mid_range';
}

export default function BudgetStep({ form, onChange, currencyList = [] }) {
  const bAmount = parseFloat(form.budget) || 1000;
  const currCode = form.currency || 'USD';

  const currentTierKey = normalizeTierKey(form.budget_type);
  const activeStrategy = TIER_CONFIG[currentTierKey] || TIER_CONFIG.mid_range;
  const p = activeStrategy.pcts;

  const handleTierSelect = (tierKey) => {
    const label = TIER_CONFIG[tierKey].label;
    onChange({ target: { name: 'budget_type', value: label } });
  };

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
        <div className="flex justify-between items-center mb-1">
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Budget Comfort Tier</label>
          <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400">{activeStrategy.label} Plan</span>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(TIER_CONFIG).map(([key, config]) => {
            const isSelected = currentTierKey === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => handleTierSelect(key)}
                className={`py-2 px-1 text-center rounded-xl text-xs font-bold border transition-all ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 shadow-sm'
                    : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300'
                }`}
              >
                {config.label}
              </button>
            );
          })}
        </div>
        <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 italic">
          {activeStrategy.desc}
        </p>
      </div>

      {/* Door-to-Door Smart Budget Allocation */}
      <div className="p-3 bg-gray-50 dark:bg-gray-800/80 rounded-2xl border border-gray-200 dark:border-gray-700 space-y-2.5">
        <div className="flex justify-between items-center">
          <span className="text-xs font-extrabold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
            Door-to-Door Smart Allocation ({activeStrategy.label})
          </span>
          <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">100% Allocated</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Outbound Travel ({p.outbound}%)</span>
            <span className="font-extrabold text-blue-600 dark:text-blue-400 block mt-0.5">
              {formatCurrency(bAmount * (p.outbound / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Return Travel ({p.returnTrans}%)</span>
            <span className="font-extrabold text-blue-600 dark:text-blue-400 block mt-0.5">
              {formatCurrency(bAmount * (p.returnTrans / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Accommodation ({p.lodging}%)</span>
            <span className="font-extrabold text-indigo-600 dark:text-indigo-400 block mt-0.5">
              {formatCurrency(bAmount * (p.lodging / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Food & Dining ({p.food}%)</span>
            <span className="font-extrabold text-emerald-600 dark:text-emerald-400 block mt-0.5">
              {formatCurrency(bAmount * (p.food / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Local Transit ({p.localTrans}%)</span>
            <span className="font-extrabold text-amber-600 dark:text-amber-400 block mt-0.5">
              {formatCurrency(bAmount * (p.localTrans / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Activities ({p.act}%)</span>
            <span className="font-extrabold text-purple-600 dark:text-purple-400 block mt-0.5">
              {formatCurrency(bAmount * (p.act / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Fees & Baggage ({p.fees}%)</span>
            <span className="font-extrabold text-gray-600 dark:text-gray-300 block mt-0.5">
              {formatCurrency(bAmount * (p.fees / 100), currCode)}
            </span>
          </div>

          <div className="p-2 bg-white dark:bg-gray-700 rounded-xl shadow-xs">
            <span className="text-[10px] text-gray-500 dark:text-gray-400 block">Contingency ({p.contingency}%)</span>
            <span className="font-extrabold text-rose-600 dark:text-rose-400 block mt-0.5">
              {formatCurrency(bAmount * (p.contingency / 100), currCode)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
