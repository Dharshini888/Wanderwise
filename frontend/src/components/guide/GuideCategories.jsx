import React from 'react';
import {
  IconCompass,
  IconBuildingMonument,
  IconChefHat,
  IconCoffee,
  IconHotelService,
  IconBus,
  IconBuildingHospital,
  IconPill,
  IconShoppingBag,
  IconCreditCard,
  IconShield,
} from '@tabler/icons-react';

const CATEGORY_DEFINITIONS = [
  { id: 'ALL', label: 'All', icon: IconCompass },
  { id: 'ATTRACTIONS', label: 'Attractions', icon: IconBuildingMonument },
  { id: 'RESTAURANTS', label: 'Restaurants', icon: IconChefHat },
  { id: 'CAFES', label: 'Cafés', icon: IconCoffee },
  { id: 'HOTELS', label: 'Hotels', icon: IconHotelService },
  { id: 'TRANSPORT', label: 'Transport', icon: IconBus },
  { id: 'HOSPITALS', label: 'Hospitals', icon: IconBuildingHospital },
  { id: 'PHARMACIES', label: 'Pharmacies', icon: IconPill },
  { id: 'SHOPPING', label: 'Shopping', icon: IconShoppingBag },
  { id: 'ATMS', label: 'ATMs', icon: IconCreditCard },
  { id: 'EMERGENCY', label: 'Emergency', icon: IconShield },
];

export default function GuideCategories({ activeCategory, onCategoryChange, counts = {} }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1 custom-scrollbar w-full">
      {CATEGORY_DEFINITIONS.map((cat) => {
        const IconComponent = cat.icon;
        const isActive = activeCategory === cat.id;
        const count = counts[cat.id];

        return (
          <button
            key={cat.id}
            onClick={() => onCategoryChange(cat.id)}
            className={`px-3.5 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 cursor-pointer border ${
              isActive
                ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20'
                : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:text-[var(--text-primary)] hover:border-blue-500/30'
            }`}
          >
            <IconComponent size={16} className={isActive ? 'text-white' : 'text-blue-500'} />
            <span>{cat.label}</span>
            {count !== undefined && count !== null && count > 0 && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                  isActive ? 'bg-white/20 text-white' : 'bg-[var(--bg-subtle)] text-[var(--text-muted)]'
                }`}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
