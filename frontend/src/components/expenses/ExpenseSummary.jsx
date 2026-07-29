import React from 'react';
import { formatCurrency } from '../../utils/currencyFormatter';
import {
  IconCash, IconReceipt, IconWallet, IconCalendarTime,
  IconTrendingUp, IconShieldCheck, IconAlertTriangle, IconSparkles
} from '@tabler/icons-react';

export default function ExpenseSummary({ budget, analytics, insights }) {
  const currency = budget?.currency || 'USD';
  const totalBudget = parseFloat(budget?.total_budget || 0);
  const spent = parseFloat(budget?.spent || 0);
  const remaining = parseFloat(budget?.remaining || 0);
  const dailyLimit = parseFloat(budget?.daily_limit || 0);
  const projected = parseFloat(analytics?.projected_final_spend || 0);
  const health = insights?.health || 'Healthy';
  const score = insights?.budget_score || 88;

  const getHealthBadge = () => {
    if (health === 'Healthy') return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300';
    if (health === 'On Track') return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300';
    if (health === 'Warning') return 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300';
    return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300';
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* 1. Total Budget */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Total Budget</span>
          <IconWallet size={18} className="text-blue-500" />
        </div>
        <div className="text-lg font-extrabold text-gray-900 dark:text-white">
          {formatCurrency(totalBudget, currency)}
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">Planned Allowance</span>
      </div>

      {/* 2. Total Spent */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Total Spent</span>
          <IconReceipt size={18} className="text-amber-500" />
        </div>
        <div className="text-lg font-extrabold text-amber-600 dark:text-amber-400">
          {formatCurrency(spent, currency)}
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">
          {budget?.budget_used_percentage || 0}% used
        </span>
      </div>

      {/* 3. Remaining Budget */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Remaining</span>
          <IconCash size={18} className="text-emerald-500" />
        </div>
        <div className={`text-lg font-extrabold ${remaining >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
          {formatCurrency(remaining, currency)}
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">Available Balance</span>
      </div>

      {/* 4. Daily Limit */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Daily Limit</span>
          <IconCalendarTime size={18} className="text-indigo-500" />
        </div>
        <div className="text-lg font-extrabold text-indigo-600 dark:text-indigo-400">
          {formatCurrency(dailyLimit, currency)}
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">Rec. Daily Pace</span>
      </div>

      {/* 5. Projected Spend */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Projected Final</span>
          <IconTrendingUp size={18} className="text-purple-500" />
        </div>
        <div className="text-lg font-extrabold text-purple-600 dark:text-purple-400">
          {formatCurrency(projected, currency)}
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">Est. Trip Cost</span>
      </div>

      {/* 6. Budget Score */}
      <div className="p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-gray-500">Budget Score</span>
          <IconSparkles size={18} className="text-amber-500" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-lg font-black text-gray-900 dark:text-white">{score}/100</span>
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${getHealthBadge()}`}>
            {health}
          </span>
        </div>
        <span className="text-[10px] text-gray-400 block font-medium">AI Health Rating</span>
      </div>
    </div>
  );
}
