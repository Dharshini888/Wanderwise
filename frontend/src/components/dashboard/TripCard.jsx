import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { IconTrash, IconChevronRight, IconWallet } from '@tabler/icons-react';

import { formatCurrency } from '../../utils/formatters';

export default function TripCard({ trip, getDays, onDelete }) {
  const [photo, setPhoto] = useState('https://placehold.co/400x200/2563EB/FFFFFF?text=WanderWise');

  useEffect(() => {
    const fetchPhoto = async () => {
      try {
        const dest = trip.destination.split(',')[0];
        const res = await fetch(`https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=400&titles=${encodeURIComponent(dest)}&origin=*`);
        const data = await res.json();
        const pages = data.query.pages;
        const pageId = Object.keys(pages)[0];
        if (pages[pageId].thumbnail) {
          setPhoto(pages[pageId].thumbnail.source);
        }
      } catch (e) {}
    };
    fetchPhoto();
  }, [trip]);

  return (
    <div className="travel-card travel-card-hover flex flex-col overflow-hidden group rounded-3xl border border-[var(--border-color)]">
      <div className="h-44 w-full relative overflow-hidden bg-slate-200">
        <img 
          src={photo} 
          alt={trip.destination} 
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent" />
        <div className="absolute top-3.5 right-3.5 bg-white/90 dark:bg-slate-900/90 text-blue-600 dark:text-blue-400 text-[10px] px-3 py-1 rounded-full font-extrabold uppercase tracking-wider shadow-sm">
          {trip.travel_type || 'Adventure'}
        </div>
        <div className="absolute bottom-3.5 left-4 text-white">
          <div className="text-lg font-black tracking-tight font-heading drop-shadow-md">{trip.destination}</div>
          <div className="text-xs font-semibold opacity-90 drop-shadow-sm mt-0.5">
            {trip.start_date?.split('T')[0]} — {trip.end_date?.split('T')[0]} ({getDays ? getDays(trip) : 1} days)
          </div>
        </div>
      </div>
      <div className="p-5 flex flex-col flex-1 gap-4">
        <div className="flex justify-between items-center mt-auto">
          <div>
            <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider">Total Budget</div>
            <div className="text-base font-extrabold text-[var(--color-primary-600)] dark:text-blue-400">
              {formatCurrency(trip.budget || 0, trip.currency)}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onDelete && (
              <button 
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDelete(trip.id); }}
                className="p-2 text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors"
                title="Delete Trip"
              >
                <IconTrash size={16} />
              </button>
            )}
            <Link 
              to={`/expenses/${trip.id}`} 
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 px-2.5 py-2 rounded-lg flex items-center gap-1 hover:bg-emerald-600 hover:text-white transition-all shadow-sm"
              title="Manage Expenses"
            >
              <IconWallet size={14} />
              Expenses
            </Link>
            <Link 
              to={`/trips/${trip.id}`} 
              state={{ initialTrip: trip }}
              className="text-xs font-semibold text-[var(--color-primary-600)] dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 px-3.5 py-2 rounded-lg flex items-center gap-1 group/btn hover:bg-[var(--color-primary-600)] hover:text-white dark:hover:bg-blue-600 dark:hover:text-white transition-all shadow-sm"
            >
              Details
              <IconChevronRight size={14} className="transform transition-transform group-hover/btn:translate-x-0.5" />
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}
