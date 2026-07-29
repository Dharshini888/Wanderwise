import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { formatCurrency } from '../../utils/currencyFormatter';
import {
  IconWallet, IconCash, IconReceipt, IconTrendingUp,
  IconShieldCheck, IconChevronRight, IconSparkles
} from '@tabler/icons-react';
import { getTripBudget, getAIExpenseInsights } from '../../api/expenses';

export default function DashboardBudgetWidget({ trip }) {
  const [budget, setBudget] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!trip || !trip.id) return;
    setLoading(true);
    Promise.all([
      getTripBudget(trip.id).catch(() => null),
      getAIExpenseInsights(trip.id).catch(() => null),
    ]).then(([bData, iData]) => {
      if (bData) setBudget(bData);
      if (iData) setInsights(iData);
      setLoading(false);
    });
  }, [trip]);

  if (!trip) return null;

  const currency = budget?.currency || trip.currency || 'USD';
  const totalBudget = parseFloat(budget?.total_budget || trip.budget || 0);
  const spent = parseFloat(budget?.spent || 0);
  const remaining = parseFloat(budget?.remaining || totalBudget);
  const health = insights?.health || 'Healthy';
  const pct = Math.min(100, Math.round(budget?.budget_used_percentage || 0));

  const getHealthBadgeClass = () => {
    if (health === 'Healthy') return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300';
    if (health === 'On Track') return 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300';
    if (health === 'Warning') return 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300';
    return 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300';
  };

  const getBarColor = () => {
    if (pct < 60) return 'bg-emerald-500';
    if (pct < 85) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400">
            <IconWallet size={20} />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
              Trip Budget Summary — {trip.destination}
            </h3>
            <p className="text-[10px] text-[var(--text-muted)]">Live spending & budget health tracker</p>
          </div>
        </div>

        <Link
          to={`/expenses/${trip.id}`}
          className="flex items-center gap-1 text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline"
        >
          Expense Dashboard <IconChevronRight size={14} />
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* 1. Total Budget */}
        <div className="p-3 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">Total Budget</span>
          <span className="text-base font-black text-[var(--text-primary)] block mt-0.5">
            {formatCurrency(totalBudget, currency)}
          </span>
        </div>

        {/* 2. Total Spent */}
        <div className="p-3 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">Total Spent</span>
          <span className="text-base font-black text-amber-600 dark:text-amber-400 block mt-0.5">
            {formatCurrency(spent, currency)}
          </span>
        </div>

        {/* 3. Remaining Budget */}
        <div className="p-3 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">Remaining</span>
          <span className={`text-base font-black block mt-0.5 ${remaining >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
            {formatCurrency(remaining, currency)}
          </span>
        </div>

        {/* 4. Budget Health */}
        <div className="p-3 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)]">
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">Budget Health</span>
          <div className="mt-1">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${getHealthBadgeClass()}`}>
              {health}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar Widget */}
      <div className="space-y-1.5 pt-1">
        <div className="flex justify-between text-xs font-semibold text-[var(--text-secondary)]">
          <span>Budget Usage</span>
          <span>{pct}% ({formatCurrency(spent, currency)} / {formatCurrency(totalBudget, currency)})</span>
        </div>
        <div className="w-full bg-gray-100 dark:bg-gray-700 h-2.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${getBarColor()}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
