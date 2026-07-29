import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconActivity, IconMapPin, IconCalendar, IconChevronRight,
  IconSun, IconWalk, IconChecklist, IconSparkles
} from '@tabler/icons-react';

export default function ActiveTripSpotlight({ activeTrip }) {
  const navigate = useNavigate();

  if (!activeTrip || !activeTrip.id) return null;

  const currentDay = activeTrip.current_trip_day || 1;
  const totalDays = activeTrip.duration_days || 1;
  const coverImg = activeTrip.cover_image || activeTrip.image_url || 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=80';

  return (
    <div className="glass-card p-4 sm:p-5 rounded-2xl border-l-4 border-l-emerald-500 relative overflow-hidden group">
      {/* Background Cover Overlay */}
      <div className="absolute inset-0 z-0 opacity-15 dark:opacity-25 group-hover:scale-105 transition-transform duration-700">
        <img src={coverImg} alt={activeTrip.destination} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--bg-card)] via-[var(--bg-card)]/90 to-transparent" />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Left Spotlight Information */}
        <div className="space-y-1 max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span>Active Journey • Day {currentDay} of {totalDays}</span>
          </div>

          <h2 className="text-xl sm:text-2xl font-extrabold font-heading text-[var(--text-primary)] tracking-tight">
            {activeTrip.title || `Live in ${activeTrip.destination}`}
          </h2>

          <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-secondary)] font-medium pt-0.5">
            <span className="flex items-center gap-1">
              <IconMapPin size={14} className="text-blue-500" />
              {activeTrip.destination}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <IconCalendar size={14} className="text-indigo-500" />
              {activeTrip.start_date} to {activeTrip.end_date}
            </span>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={() => navigate(`/trips/${activeTrip.id}`)}
          className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs transition-all shadow-md shrink-0"
        >
          Resume Journey <IconChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
