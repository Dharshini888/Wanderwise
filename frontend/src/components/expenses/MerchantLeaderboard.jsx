import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';
import { IconBuildingStore, IconTrophy } from '@tabler/icons-react';

export default function MerchantLeaderboard({ merchants = [], currency = 'USD' }) {
  if (!merchants || merchants.length === 0) return null;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
          <IconTrophy size={16} className="text-amber-500" /> Top Merchants
        </h3>
        <span className="text-[10px] text-gray-400 font-bold uppercase">Normalized Spend</span>
      </div>

      <div className="space-y-2">
        {merchants.map((item, idx) => (
          <div key={item.merchant} className="flex items-center justify-between p-2.5 rounded-xl bg-gray-50 dark:bg-gray-700/50 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 font-black text-[10px] flex items-center justify-center">
                {idx + 1}
              </span>
              <span className="font-bold text-gray-800 dark:text-gray-200">{item.merchant}</span>
              <span className="text-[10px] text-gray-400">({item.count} transaction{item.count > 1 ? 's' : ''})</span>
            </div>
            <span className="font-extrabold text-gray-900 dark:text-white">
              {formatCurrency(parseFloat(item.total_amount || 0), currency)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
