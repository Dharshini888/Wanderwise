import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconSparkles, IconMap, IconWallet, IconSun,
  IconBackpack, IconShieldCheck, IconChevronRight
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/formatters';

export default function QuickAccessModules({ heroTrip, widgetData }) {
  const navigate = useNavigate();

  const temp = widgetData?.weather?.current?.temperature;
  const weatherLabel = temp != null ? `${Math.round(temp)}°C Open-Meteo` : 'Live Weather';

  const budgetLabel = heroTrip?.budget
    ? formatCurrency(heroTrip.budget, heroTrip.currency || 'USD')
    : 'Budget Tracker';

  const modules = [
    {
      id: 'itinerary',
      title: 'AI Itinerary',
      description: 'Personalized multi-day schedules with verified landmarks',
      badge: heroTrip ? 'Itinerary Ready' : 'AI Planner',
      badgeClass: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/25',
      icon: <IconSparkles size={20} />,
      colorClass: 'bg-purple-600 text-white shadow-purple-500/20',
      path: heroTrip ? `/trips/${heroTrip.id}` : '/recommendations'
    },
    {
      id: 'transit',
      title: 'Maps & Transit',
      description: 'OSRM road transit & 3-state provenance classification',
      badge: '3-State Provenance',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25',
      icon: <IconMap size={20} />,
      colorClass: 'bg-emerald-600 text-white shadow-emerald-500/20',
      path: '/transit'
    },
    {
      id: 'budget',
      title: 'Budget Planner',
      description: 'Canonical budget tracking & expense categorization',
      badge: budgetLabel,
      badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/25 font-mono',
      icon: <IconWallet size={20} />,
      colorClass: 'bg-blue-600 text-white shadow-blue-500/20',
      path: heroTrip ? `/expenses/${heroTrip.id}` : '/expenses'
    },
    {
      id: 'weather',
      title: 'Weather Advisor',
      description: 'Open-Meteo live telemetry & context-aware warnings',
      badge: weatherLabel,
      badgeClass: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/25',
      icon: <IconSun size={20} />,
      colorClass: 'bg-amber-600 text-white shadow-amber-500/20',
      path: '/weather'
    },
    {
      id: 'packing',
      title: 'Packing Checklist',
      description: 'Smart checklist tailored to weather & trip duration',
      badge: 'Checklist Ready',
      badgeClass: 'bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/25',
      icon: <IconBackpack size={20} />,
      colorClass: 'bg-teal-600 text-white shadow-teal-500/20',
      path: '/packing'
    },
    {
      id: 'safety',
      title: 'Safety Advisory',
      description: 'Destination risk analyzer & emergency assistance',
      badge: 'Advisory Active',
      badgeClass: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/25',
      icon: <IconShieldCheck size={20} />,
      colorClass: 'bg-rose-600 text-white shadow-rose-500/20',
      path: '/safety'
    }
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-extrabold uppercase tracking-wider text-[var(--text-muted)] font-heading">
          Quick Access Modules
        </h3>
        <span className="text-[11px] font-semibold text-[var(--text-muted)]">
          Core Research Capabilities (IEEE NMIC-2026)
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {modules.map((mod) => (
          <div
            key={mod.id}
            onClick={() => navigate(mod.path)}
            className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:border-blue-500/40 hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between group"
          >
            <div className="flex items-start justify-between">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-md ${mod.colorClass} group-hover:scale-105 transition-transform`}>
                {mod.icon}
              </div>
              <IconChevronRight size={14} className="text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-0.5" />
            </div>

            <div className="mt-3.5 space-y-1">
              <h4 className="text-xs font-black text-[var(--text-primary)] font-heading truncate">
                {mod.title}
              </h4>
              <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full truncate max-w-full ${mod.badgeClass}`}>
                {mod.badge}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

