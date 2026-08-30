import React, { useState, useEffect } from 'react';
import {
  IconDownload,
  IconCheck,
  IconCloudCheck,
  IconAlertTriangle,
  IconX,
  IconMapPin,
  IconShield,
  IconBackpack,
  IconRoute
} from '@tabler/icons-react';

export default function OfflinePackageModal({ trip, isOpen, onClose }) {
  const [isCached, setIsCached] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [cacheTime, setCacheTime] = useState(null);

  const storageKey = `ww_offline_trip_${trip?.id || 'default'}`;

  useEffect(() => {
    if (trip?.id) {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setIsCached(true);
          setCacheTime(parsed.cached_at);
        } catch (e) {
          setIsCached(false);
        }
      }
    }
  }, [trip?.id]);

  if (!isOpen || !trip) return null;

  const handleDownload = () => {
    setDownloading(true);
    setTimeout(() => {
      const packageData = {
        trip_id: trip.id,
        title: trip.title || trip.destination,
        destination: trip.destination,
        start_date: trip.start_date,
        end_date: trip.end_date,
        budget: trip.budget,
        itinerary: trip.itinerary || [],
        transit: trip.transit_summary || null,
        emergency_contacts: [
          { label: 'Local Police', number: '112 / 999 / 911' },
          { label: 'Ambulance / Medical', number: '112 / 999 / 911' },
          { label: 'Embassy Advisory', number: '+1-800-WW-SAFETY' },
        ],
        checklist: ['Passport', 'Insurance Copy', 'Hotel Booking', 'Flight Ticket'],
        packing_list: ['Universal Adapter', 'Prescription Meds', 'Comfortable Shoes'],
        cached_at: new Date().toLocaleString(),
      };

      try {
        localStorage.setItem(storageKey, JSON.stringify(packageData));
        setIsCached(true);
        setCacheTime(packageData.cached_at);
      } catch (err) {
        console.error('Failed to store offline package:', err);
      } finally {
        setDownloading(false);
      }
    }, 1200);
  };

  const handleClearCache = () => {
    localStorage.removeItem(storageKey);
    setIsCached(false);
    setCacheTime(null);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="glass-modal max-w-lg w-full p-6 rounded-3xl space-y-6 relative border border-[var(--border-color)] bg-[var(--bg-card)]">
        
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-500/20 rounded-2xl text-emerald-600 dark:text-emerald-400">
              <IconCloudCheck size={28} />
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase text-emerald-600 dark:text-emerald-400 tracking-wider">
                Offline Toolkit
              </div>
              <h3 className="text-xl font-black text-[var(--text-primary)] font-heading">
                Download Trip for Offline Use
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-app)] transition-colors"
          >
            <IconX size={20} />
          </button>
        </div>

        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
          Cache complete trip itineraries, offline maps data, emergency contacts, packing checklists, and document details onto your local device memory for access without an internet connection.
        </p>

        {/* Offline Cache Status Badge */}
        <div className="p-4 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-color)] space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-[var(--text-primary)]">Offline Package Status</span>
            {isCached ? (
              <span className="text-[10px] font-extrabold bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/30 px-3 py-1 rounded-full flex items-center gap-1">
                🟢 Trip available offline
              </span>
            ) : (
              <span className="text-[10px] font-extrabold bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-500/30 px-3 py-1 rounded-full">
                ⚠️ Not Cached Yet
              </span>
            )}
          </div>

          {cacheTime && (
            <div className="text-[10px] text-[var(--text-muted)]">
              Last Synced: <span className="font-bold text-[var(--text-primary)]">{cacheTime}</span>
            </div>
          )}
        </div>

        {/* Contents Checklist */}
        <div className="space-y-2 text-xs">
          <div className="font-bold text-[var(--text-primary)] mb-1">Package Contents:</div>
          <div className="grid grid-cols-2 gap-2 text-[11px] text-[var(--text-secondary)]">
            <div className="flex items-center gap-1.5"><IconRoute size={14} className="text-purple-500" /> Full Itinerary</div>
            <div className="flex items-center gap-1.5"><IconMapPin size={14} className="text-indigo-500" /> Transit Routing</div>
            <div className="flex items-center gap-1.5"><IconShield size={14} className="text-emerald-500" /> Emergency Numbers</div>
            <div className="flex items-center gap-1.5"><IconBackpack size={14} className="text-amber-500" /> Packing & Documents</div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          {!isCached ? (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-xs shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {downloading ? 'Caching Trip Data…' : <><IconDownload size={18} /> Download Trip for Offline Use</>}
            </button>
          ) : (
            <>
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="flex-1 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <IconDownload size={18} /> Update Offline Cache
              </button>
              <button
                onClick={handleClearCache}
                className="py-3 px-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40 hover:bg-rose-100 font-bold text-xs transition-all cursor-pointer"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
