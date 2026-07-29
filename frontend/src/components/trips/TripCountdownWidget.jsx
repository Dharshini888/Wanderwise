import React from 'react';
import { IconPlaneDeparture, IconClock } from '@tabler/icons-react';

export default function TripCountdownWidget({ startDate, countdownText, daysLeft }) {
  if (daysLeft === undefined || daysLeft === null) return null;

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md">
      <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
        <IconPlaneDeparture size={22} className="animate-bounce" />
      </div>
      <div>
        <div className="text-xs uppercase tracking-wider font-semibold opacity-90">Countdown</div>
        <div className="text-sm font-extrabold font-heading">
          {daysLeft > 0 ? `${daysLeft} Days to Departure` : countdownText || 'Trip Active'}
        </div>
      </div>
    </div>
  );
}
