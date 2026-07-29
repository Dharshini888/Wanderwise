import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconSearch, IconPlus, IconMapPins, IconChevronLeft, IconChevronRight, IconWorld
} from '@tabler/icons-react';
import TripCard from '../components/trips/TripCard';
import TripWizard from '../components/trips/TripWizard';
import TripStatsHeader from '../components/trips/TripStatsHeader';
import ActiveTripSpotlight from '../components/trips/ActiveTripSpotlight';
import RecentlyViewedChip from '../components/trips/RecentlyViewedChip';
import {
  getPaginatedTrips, getTripStats, getActiveTripSpotlight, getRecentlyViewedTrip,
  createTrip, duplicateTrip, archiveTrip, restoreTrip,
  toggleFavoriteTrip, deleteTrip
} from '../api/trips';

const FILTER_TABS = [
  { id: 'All', label: 'All Trips' },
  { id: 'Upcoming', label: 'Upcoming' },
  { id: 'Active', label: 'Active' },
  { id: 'Completed', label: 'Completed' },
  { id: 'Solo', label: 'Solo' },
  { id: 'Family', label: 'Family' },
  { id: 'Friends', label: 'Friends' },
  { id: 'Business', label: 'Business' },
  { id: 'Favorites', label: 'Favorites' },
  { id: 'Archived', label: 'Archived' },
];

const SORT_OPTIONS = [
  { id: 'upcoming_first', label: 'Upcoming First' },
  { id: 'recently_completed', label: 'Recently Completed' },
  { id: 'budget_high_low', label: 'Budget: High → Low' },
  { id: 'budget_low_high', label: 'Budget: Low → High' },
  { id: 'longest_trip', label: 'Longest Trip' },
  { id: 'shortest_trip', label: 'Shortest Trip' },
];

export default function TripList() {
  const navigate = useNavigate();

  const [trips, setTrips] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeSpotlight, setActiveSpotlight] = useState(null);
  const [recentlyViewed, setRecentlyViewed] = useState(null);

  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('upcoming_first');
  const [page, setPage] = useState(1);
  const [limit] = useState(12);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const [showWizard, setShowWizard] = useState(false);

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : {};

  let userId = user.id;
  try {
    if (!userId && token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub || payload.user_id || payload.id;
    }
  } catch (_) {}

  const loadOverviewStats = useCallback(async () => {
    if (!userId) return;
    try {
      const [sData, spotData, recData] = await Promise.all([
        getTripStats(userId).catch(() => null),
        getActiveTripSpotlight(userId).catch(() => null),
        getRecentlyViewedTrip(userId).catch(() => null),
      ]);
      setStats(sData);
      setActiveSpotlight(spotData && spotData.id ? spotData : null);
      setRecentlyViewed(recData && recData.id ? recData : null);
    } catch (_) {}
  }, [userId]);

  const loadTripsData = useCallback(async () => {
    if (!userId) { setLoading(false); return; }
    setLoading(true);
    try {
      const params = {
        user_id: userId,
        page,
        limit,
        search: searchQuery.trim() || undefined,
        status: ['Solo', 'Family', 'Friends', 'Business'].includes(activeTab) ? undefined : activeTab,
        travel_style: ['Solo', 'Family', 'Friends', 'Business'].includes(activeTab) ? activeTab : undefined,
        sort: sortBy,
        paginated: true,
      };

      const res = await getPaginatedTrips(params);
      if (res && Array.isArray(res.trips)) {
        setTrips(res.trips);
        setTotalPages(res.total_pages || 1);
        setTotalCount(res.total || res.trips.length);
      } else if (Array.isArray(res)) {
        setTrips(res);
        setTotalPages(1);
        setTotalCount(res.length);
      }
    } catch (_) {}
    setLoading(false);
  }, [userId, page, limit, searchQuery, activeTab, sortBy]);

  useEffect(() => {
    loadOverviewStats();
  }, [loadOverviewStats]);

  useEffect(() => {
    loadTripsData();
  }, [loadTripsData]);

  const handleCreateTrip = async (payload) => {
    const newTrip = await createTrip(payload);
    loadOverviewStats();
    loadTripsData();
    if (newTrip && newTrip.id) {
      navigate(`/trips/${newTrip.id}`);
    }
  };

  const handleFavorite = async (id) => {
    setTrips(prev => prev.map(t => t.id === id ? { ...t, is_favorite: !t.is_favorite } : t));
    await toggleFavoriteTrip(id);
    loadOverviewStats();
    loadTripsData();
  };

  const handleArchive = async (id) => {
    const target = trips.find(t => t.id === id);
    if (target?.is_archived) {
      await restoreTrip(id);
    } else {
      await archiveTrip(id);
    }
    loadOverviewStats();
    loadTripsData();
  };

  const handleDuplicate = async (id) => {
    await duplicateTrip(id, userId);
    loadOverviewStats();
    loadTripsData();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this trip itinerary?')) return;
    setTrips(prev => prev.filter(t => t.id !== id));
    await deleteTrip(id);
    loadOverviewStats();
    loadTripsData();
  };

  return (
    <div className="flex flex-col gap-5 pb-10">
      {/* Top Banner Header Bar matching Dashboard header scale */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-card p-4 rounded-2xl">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--color-primary-600)] dark:text-blue-400">
            <IconMapPins size={16} /> My Travel Itineraries
          </div>
          <h1 className="text-xl font-bold font-heading text-[var(--text-primary)] mt-0.5">
            My Trips Dashboard
          </h1>
        </div>

        <button
          onClick={() => setShowWizard(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--color-primary-600)] text-white hover:bg-blue-700 font-extrabold text-xs transition-all shadow-md shrink-0"
        >
          <IconPlus size={16} /> Plan New Trip
        </button>
      </div>

      {/* Statistics Header Section */}
      <TripStatsHeader stats={stats} loading={!stats && loading} />

      {/* Recently Viewed Banner Chip */}
      {recentlyViewed && <RecentlyViewedChip recentTrip={recentlyViewed} />}

      {/* Single Active Trip Spotlight Hero Card */}
      {activeSpotlight && <ActiveTripSpotlight activeTrip={activeSpotlight} />}

      {/* Filter, Search & Sorting Control Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 glass-card p-2.5 rounded-2xl">
        {/* Category & Status Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 custom-scrollbar shrink-0">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setPage(1); }}
              className={`px-3 py-1.5 rounded-xl text-xs font-extrabold transition-all shrink-0 ${
                activeTab === tab.id
                  ? 'bg-[var(--color-primary-600)] text-white shadow-sm'
                  : 'bg-[var(--bg-app)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:bg-[var(--bg-card)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Sort Dropdown */}
        <div className="flex flex-col sm:flex-row items-center gap-2">
          {/* Search Input */}
          <div className="relative w-full sm:w-56">
            <IconSearch size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search city, destination..."
              className="w-full pl-8 pr-3 py-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-xl text-xs font-semibold focus:outline-none focus:border-[var(--color-primary-500)]"
            />
          </div>

          {/* Sort Selector */}
          <div className="relative w-full sm:w-auto shrink-0">
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              className="w-full sm:w-auto px-3 py-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] rounded-xl text-xs font-bold focus:outline-none focus:border-[var(--color-primary-500)] cursor-pointer"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  Sort: {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Trip Cards Grid List - Responsive 3-column grid matching Dashboard */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-60 glass-card rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : trips.length === 0 ? (
        <div className="glass-card p-10 text-center rounded-2xl border-dashed border-2 border-[var(--border-color)] space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center mx-auto">
            <IconWorld size={28} />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-base font-bold font-heading text-[var(--text-primary)]">🌍 No Trips Found</h3>
            <p className="text-xs text-[var(--text-muted)]">
              {searchQuery ? `No itineraries match "${searchQuery}".` : `Plan your next adventure to see it here.`}
            </p>
          </div>
          <button
            onClick={() => setShowWizard(true)}
            className="px-4 py-2 rounded-xl bg-[var(--color-primary-600)] text-white font-bold text-xs shadow-md hover:bg-blue-700 transition-all inline-flex items-center gap-1.5"
          >
            <IconPlus size={15} /> Plan First Adventure
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                onFavorite={handleFavorite}
                onArchive={handleArchive}
                onDuplicate={handleDuplicate}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Server-Side Pagination Bar */}
          {totalPages > 1 && (
            <div className="glass-card flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl text-xs text-[var(--text-muted)]">
              <div>
                Showing <span className="font-bold text-[var(--text-primary)]">{trips.length}</span> of <span className="font-bold text-[var(--text-primary)]">{totalCount}</span> trips
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  className="p-1 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] disabled:opacity-40 hover:bg-[var(--bg-card)] transition-colors"
                >
                  <IconChevronLeft size={16} />
                </button>
                <span className="font-extrabold text-[var(--text-primary)] px-2">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  className="p-1 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] disabled:opacity-40 hover:bg-[var(--bg-card)] transition-colors"
                >
                  <IconChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Creation Wizard Modal */}
      <TripWizard
        userId={userId}
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        onSuccess={handleCreateTrip}
      />
    </div>
  );
}
