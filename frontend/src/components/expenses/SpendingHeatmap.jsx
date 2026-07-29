import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';
import { IconFlame } from '@tabler/icons-react';

export default function SpendingHeatmap({ heatmap = [], currency = 'USD' }) {
  if (!heatmap || heatmap.length === 0) return null;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
          <IconFlame size={16} className="text-amber-500" /> Daily Spending Heatmap
        </h3>
        <span className="text-[10px] text-gray-400 font-bold uppercase">Daily Intensity</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
        {heatmap.map((item) => {
          const amt = parseFloat(item.amount || 0);
          let bgClass = 'bg-gray-50 dark:bg-gray-700/40 border-gray-200 dark:border-gray-700 text-gray-500';
          if (item.intensity === 'high') {
            bgClass = 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 font-extrabold';
          } else if (item.intensity === 'medium') {
            bgClass = 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 font-bold';
          }

          return (
            <div key={item.date} className={`p-2.5 rounded-xl border text-center space-y-0.5 ${bgClass}`}>
              <span className="text-[10px] uppercase block opacity-75">Day {item.day_number}</span>
              <span className="text-xs block font-black">{formatCurrency(amt, currency)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
