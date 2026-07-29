import React from 'react';
import { formatCurrency } from '../../utils/formatters';
import { IconCash, IconWallet, IconUsers, IconCalendarStats } from '@tabler/icons-react';

import { Link } from 'react-router-dom';

export default function BudgetSummaryCard({ trip }) {
  if (!trip) return null;

  const currency = trip.currency || 'USD';
  const totalBudget = trip.budget || 0;
  const dailyBudget = trip.estimated_daily_budget || (totalBudget / Math.max(1, trip.number_of_days || 1));
  const perPerson = trip.budget_per_person || (totalBudget / Math.max(1, trip.group_size || 1));
  const remaining = trip.total_budget_remaining !== undefined ? trip.total_budget_remaining : totalBudget;

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700/80 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200 uppercase tracking-wider flex items-center gap-2">
          <IconCash className="text-emerald-500" size={18} /> Budget Summary
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
            {currency} Currency
          </span>
          <Link
            to={`/expenses/${trip.id}`}
            className="text-xs font-bold px-3 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 shadow-sm transition-all"
          >
            <IconWallet size={15} /> Manage Expenses
          </Link>
        </div>
      </div>


      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <div className="text-xs text-gray-500 dark:text-gray-400">Total Budget</div>
          <div className="text-base font-extrabold text-gray-900 dark:text-white mt-1">
            {formatCurrency(totalBudget, currency)}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <div className="text-xs text-gray-500 dark:text-gray-400">Daily Budget</div>
          <div className="text-base font-extrabold text-blue-600 dark:text-blue-400 mt-1">
            {formatCurrency(dailyBudget, currency)}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <div className="text-xs text-gray-500 dark:text-gray-400">Per Person ({trip.group_size || 1})</div>
          <div className="text-base font-extrabold text-purple-600 dark:text-purple-400 mt-1">
            {formatCurrency(perPerson, currency)}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <div className="text-xs text-gray-500 dark:text-gray-400">Remaining Balance</div>
          <div className="text-base font-extrabold text-emerald-600 dark:text-emerald-400 mt-1">
            {formatCurrency(remaining, currency)}
          </div>
        </div>
      </div>
    </div>
  );
}
