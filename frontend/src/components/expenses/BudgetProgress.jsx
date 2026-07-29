import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';

export default function BudgetProgress({ budget }) {
  const currency = budget?.currency || 'USD';
  const total = parseFloat(budget?.total_budget || 0);
  const spent = parseFloat(budget?.spent || 0);
  const remaining = parseFloat(budget?.remaining || 0);
  const emergency = parseFloat(budget?.emergency_reserve || 0);
  const pct = Math.min(100, Math.round(budget?.budget_used_percentage || 0));

  const getBarColor = () => {
    if (pct < 60) return 'bg-emerald-500';
    if (pct < 85) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">
          Budget Consumption
        </h3>
        <span className="text-xs font-black text-blue-600 dark:text-blue-400">{pct}%</span>
      </div>

      <div className="w-full bg-gray-100 dark:bg-gray-700 h-3 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getBarColor()}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs pt-1">
        <div className="p-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <span className="text-gray-400 text-[10px] uppercase font-bold block">Spent / Total</span>
          <span className="font-extrabold text-gray-900 dark:text-white">
            {formatCurrency(spent, currency)} / {formatCurrency(total, currency)}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <span className="text-gray-400 text-[10px] uppercase font-bold block">Emergency Reserve</span>
          <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
            {formatCurrency(emergency, currency)}
          </span>
        </div>
      </div>
    </div>
  );
}
