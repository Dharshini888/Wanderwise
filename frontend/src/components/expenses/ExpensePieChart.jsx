import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';

const CATEGORY_COLORS = {
  Accommodation: '#3b82f6',
  Food: '#f59e0b',
  Transport: '#10b981',
  Shopping: '#ec4899',
  Activities: '#8b5cf6',
  Healthcare: '#ef4444',
  Insurance: '#6366f1',
  Emergency: '#dc2626',
  Entertainment: '#06b6d4',
  Misc: '#6b7280',
};

export default function ExpensePieChart({ breakdown = [], currency = 'USD' }) {
  if (!breakdown || breakdown.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-gray-500 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
        No category breakdown available yet.
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-4">
      <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">
        Category Breakdown
      </h3>

      <div className="space-y-3">
        {breakdown.map((item) => {
          const color = CATEGORY_COLORS[item.category] || '#6b7280';
          const amt = parseFloat(item.amount || 0);

          return (
            <div key={item.category} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {item.category}
                </span>
                <span className="font-extrabold text-gray-900 dark:text-white">
                  {formatCurrency(amt, currency)} ({item.percentage}%)
                </span>
              </div>

              <div className="w-full bg-gray-100 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${item.percentage}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
