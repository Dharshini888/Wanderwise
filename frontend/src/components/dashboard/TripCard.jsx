import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { IconTrash, IconChevronRight, IconWallet } from '@tabler/icons-react';

import { formatCurrency } from '../../utils/formatters';

export default function TripCard({ trip, token, getDays, onDelete }) {
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
    <div className="glass-card flex flex-col overflow-hidden group">
      <div className="h-40 w-full relative overflow-hidden bg-slate-200">
        <img 
          src={photo} 
          alt={trip.destination} 
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" 
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
        <div className="absolute top-3 right-3 bg-white/90 dark:bg-slate-900/90 text-[var(--color-primary-600)] dark:text-blue-400 text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wider shadow-sm">
          {trip.travel_type}
        </div>
        <div className="absolute bottom-3 left-3 text-white">
          <div className="text-base font-extrabold tracking-wide font-heading drop-shadow-sm">{trip.destination}</div>
          <div className="text-[10px] font-medium opacity-90 drop-shadow-sm">
            {trip.start_date} — {trip.end_date} ({getDays(trip)} days)
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
