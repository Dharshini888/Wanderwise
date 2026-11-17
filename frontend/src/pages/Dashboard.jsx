import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { formatCurrency, getStoredUserId } from '../utils/formatters';
import { calculateTripDuration, getTripStatusInfo, formatLocalDate } from '../utils/date_helpers';
import {
  IconSearch, IconSparkles, IconPlus, IconMapPin, IconCalendar, IconCash,
  IconClock, IconHeart, IconPlane, IconActivity, IconAlertTriangle, IconCheck,
  IconReceipt2, IconMap, IconCompass, IconChevronRight, IconTrendingUp,
  IconX, IconShieldCheck, IconMessageChatbot, IconBuildingStore
} from '@tabler/icons-react';

import HeroTripBanner from '../components/dashboard/HeroTripBanner';
import TodayOverviewWidget from '../components/dashboard/TodayOverviewWidget';
import QuickAccessModules from '../components/dashboard/QuickAccessModules';
import TripCard from '../components/dashboard/TripCard';
import WeatherWidget from '../components/dashboard/WeatherWidget';
import RiskAnalyzerWidget from '../components/dashboard/RiskAnalyzerWidget';
import LanguageWidget from '../components/dashboard/LanguageWidget';
import PersonalizedWidget from '../components/dashboard/PersonalizedWidget';
import QuickCurrencyWidget from '../components/dashboard/QuickCurrencyWidget';
import DocumentsVaultWidget from '../components/dashboard/DocumentsVaultWidget';
import SmartChecklistWidget from '../components/checklist/SmartChecklistWidget';
import TripWizard from '../components/trips/TripWizard';
import { createTrip } from '../api/trips';
import api from '../api/axios';

export default function Dashboard() {
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [widgetData, setWidgetData] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);

  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : { name: 'Traveler', email: '' };
  const userId = getStoredUserId();

  const getGreeting = () => {
    const hr = new Date().getHours();
    if (hr < 12) return 'Good morning';
    if (hr < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const fetchDashboardData = async () => {
    if (!userId || userId === 'undefined' || String(userId) === 'undefined') {
      setLoading(false);
      return;
    }
    try {
      const [tripsRes, widgetRes, actRes] = await Promise.allSettled([
        api.get(`/api/trips/user/${userId}`),
        api.get(`/api/trips/dashboard-widgets/${userId}`),
        api.get(`/api/activity/user/${userId}`)
      ]);

      if (tripsRes.status === 'fulfilled' && Array.isArray(tripsRes.value.data)) {
        setTrips(tripsRes.value.data);
      }

      if (widgetRes.status === 'fulfilled' && widgetRes.value.data) {
        setWidgetData(widgetRes.value.data);
      }

      if (actRes.status === 'fulfilled' && Array.isArray(actRes.value.data)) {
        setRecentActivities(actRes.value.data);
      }
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  const deleteTrip = async (id) => {
    try {
      await api.delete(`/api/trips/${id}`);
      setTrips(prev => prev.filter(t => t.id !== id));
      fetchDashboardData();
    } catch (_) {}
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Universal Search Debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setIsSearching(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await api.get(`/api/trips/search?query=${encodeURIComponent(searchQuery.trim())}`);
        setSearchResults(res.data);
      } catch (_) {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleCreateTrip = async (payload) => {
    const newTrip = await createTrip(payload);
    fetchDashboardData();
    if (newTrip && newTrip.id) {
      navigate(`/trips/${newTrip.id}`);
    }
    return newTrip;
  };

  // Safe Dynamic Trip Partitioning
  const ongoingTrips = trips.filter(t => getTripStatusInfo(t.start_date, t.end_date).status === 'Ongoing');
  const upcomingTrips = trips
    .filter(t => getTripStatusInfo(t.start_date, t.end_date).status === 'Upcoming')
    .sort((a, b) => String(a.start_date).localeCompare(String(b.start_date)));
  const completedTrips = trips
    .filter(t => getTripStatusInfo(t.start_date, t.end_date).status === 'Completed')
    .sort((a, b) => String(b.end_date).localeCompare(String(a.end_date)));

  // Hero Trip determination: Ongoing > Next Upcoming > Most Recent Completed > First > None
  const heroTrip = ongoingTrips[0] || upcomingTrips[0] || completedTrips[0] || trips[0] || null;
  const heroStatusInfo = heroTrip ? getTripStatusInfo(heroTrip.start_date, heroTrip.end_date) : null;
  const heroStatus = heroStatusInfo ? heroStatusInfo.status : 'No Trip';

  // Overall Statistics Metrics
  const totalTripsCount = trips.length;
  const uniqueDestinationsCount = new Set(trips.map(t => (t.destination || '').split(',')[0].trim()).filter(Boolean)).size;
  const totalPlannedBudget = trips.reduce((sum, t) => sum + (parseFloat(t.budget) || 0), 0);
  const totalTravelDays = trips.reduce((sum, t) => sum + calculateTripDuration(t.start_date, t.end_date), 0);
  const userCurrency = heroTrip?.currency || user.currency || 'USD';

  return (
    <div className="space-y-8 pb-16 animate-fadeIn max-w-7xl mx-auto px-4 sm:px-6">

      {/* ===================================================================== */}
      {/* SECTION 1: WELCOME HEADER                                             */}
      {/* ===================================================================== */}
      <section className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-5 md:p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              ✈️ WanderWise Command Center
            </span>
            <span className="text-xs text-[var(--text-muted)] font-medium hidden sm:inline">
              • Smart AI Travel Companion
            </span>
          </div>

          <h1 className="text-xl md:text-2xl font-black text-[var(--text-primary)] font-heading tracking-tight">
            {getGreeting()}, {user.name || 'Traveler'}
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 font-medium">
            {totalTripsCount > 0 ? (
              <span>
                You have <strong className="text-[var(--text-primary)]">{totalTripsCount} travel plan{totalTripsCount !== 1 ? 's' : ''}</strong> across <strong className="text-[var(--text-primary)]">{uniqueDestinationsCount} destination{uniqueDestinationsCount !== 1 ? 's' : ''}</strong> ({totalTravelDays} days total).
              </span>
            ) : (
              <span>Welcome to WanderWise. Create your first verified AI itinerary below.</span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          {/* Universal Search Bar */}
          <div className="relative flex-1 md:w-64">
            <IconSearch size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search trips, cities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-8 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-xs font-semibold focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder:text-[var(--text-muted)]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                <IconX size={14} />
              </button>
            )}

            {/* Live Search Results Popover */}
            {searchResults && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl shadow-xl z-50 p-2 max-h-60 overflow-y-auto">
                {searchResults.length > 0 ? (
                  searchResults.map(t => (
                    <Link
                      key={t.id}
                      to={`/trips/${t.id}`}
                      className="p-2 hover:bg-[var(--bg-subtle)] rounded-xl flex items-center gap-2.5 no-underline transition-colors"
                      onClick={() => setSearchQuery('')}
                    >
                      <IconMapPin size={15} className="text-blue-500 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs font-bold text-[var(--text-primary)] truncate">{t.destination}</div>
                        <div className="text-[10px] text-[var(--text-muted)]">
                          {formatLocalDate(t.start_date, { day: 'numeric', month: 'short' })} • {calculateTripDuration(t.start_date, t.end_date)} Days
                        </div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="p-3 text-center text-xs text-[var(--text-muted)]">No matching trips found</div>
                )}
              </div>
            )}
          </div>

          {/* Plan New Trip Primary Action */}
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center gap-1.5 px-4 py-2 text-xs font-extrabold shrink-0 cursor-pointer shadow-md shadow-blue-500/20"
          >
            <IconPlus size={15} />
            <span>Plan Trip</span>
          </button>
        </div>
      </section>

      {/* ===================================================================== */}
      {/* SECTION 2: ACTIVE OR UPCOMING TRIP (HERO CARD)                        */}
      {/* ===================================================================== */}
      <section aria-label="Hero Trip">
        <HeroTripBanner
          trip={heroTrip}
          statusInfo={heroStatusInfo}
          onPlanTrip={() => setShowForm(true)}
        />
      </section>

      {/* ===================================================================== */}
      {/* SECTION 3: TODAY'S TRAVEL OVERVIEW                                    */}
      {/* ===================================================================== */}
      <section aria-label="Today Travel Overview">
        <TodayOverviewWidget
          widgetData={widgetData}
          heroTrip={heroTrip}
          heroStatus={heroStatus}
          statusInfo={heroStatusInfo}
          onRefresh={fetchDashboardData}
          onPlanTrip={() => setShowForm(true)}
        />
      </section>

      {/* ===================================================================== */}
      {/* SECTION 4: QUICK ACCESS MODULES                                       */}
      {/* ===================================================================== */}
      <section aria-label="Quick Access Modules">
        <QuickAccessModules heroTrip={heroTrip} widgetData={widgetData} />
      </section>

      {/* ===================================================================== */}
      {/* SECTION 5: MY TRAVEL PLANS                                            */}
      {/* ===================================================================== */}
      <section className="space-y-4" aria-label="My Travel Plans">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-black text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconCalendar size={18} className="text-blue-500" />
              <span>My Travel Plans</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20">
                {trips.length}
              </span>
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Saved itineraries with dynamic status and real-time budget tracking
            </p>
          </div>

          <button
            onClick={() => setShowForm(true)}
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 cursor-pointer"
          >
            <IconPlus size={13} />
            <span>New Itinerary</span>
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(n => (
              <div key={n} className="h-64 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] animate-pulse p-4 flex flex-col justify-between" />
            ))}
          </div>
        ) : trips.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {trips.map(trip => (
              <TripCard
                key={trip.id}
                trip={trip}
                onDelete={deleteTrip}
              />
            ))}
          </div>
        ) : (
          <div className="glass-card p-10 rounded-3xl border border-dashed border-[var(--border-color)] text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center mx-auto">
              <IconPlane size={24} />
            </div>
            <h4 className="text-sm font-bold text-[var(--text-primary)]">No itineraries created yet</h4>
            <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto">
              Click "Plan Trip" above to build your first personalized itinerary.
            </p>
            <button onClick={() => setShowForm(true)} className="btn-primary text-xs font-bold px-4 py-2 mt-2">
              Start Planning
            </button>
          </div>
        )}
      </section>

      {/* ===================================================================== */}
      {/* SECTION 6: CONTEXT-AWARE TRAVEL SUPPORT                               */}
      {/* ===================================================================== */}
      <section className="space-y-4" aria-label="Context Aware Support">
        <div>
          <h3 className="text-base font-black text-[var(--text-primary)] font-heading flex items-center gap-2">
            <IconShieldCheck size={18} className="text-emerald-500" />
            <span>Context-Aware Travel Support</span>
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
              Live Toolkit
            </span>
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Specialized travel assistance modules tailored to your destination context
          </p>
        </div>

        {/* 3-Column Responsive Supporting Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* 1. Dynamic Weather & Activity Advisor */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <WeatherWidget trip={heroTrip} />
          </div>

          {/* 2. Safety Risk Analyzer */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <RiskAnalyzerWidget trip={heroTrip} />
          </div>

          {/* 3. Personalized Destination Recommendations */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <PersonalizedWidget trips={trips} />
          </div>

          {/* 4. Quick Currency Converter */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <QuickCurrencyWidget />
          </div>

          {/* 5. Destination Language & Audio Phrasebook */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <LanguageWidget trip={heroTrip} />
          </div>

          {/* 6. Travel Documents Vault */}
          <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-sm">
            <DocumentsVaultWidget />
          </div>
        </div>

        {/* Smart Checklist Widget (Full-width card below) */}
        {heroTrip && (
          <div className="pt-2">
            <SmartChecklistWidget
              tripId={heroTrip.id}
              tripTitle={heroTrip.title || heroTrip.destination}
            />
          </div>
        )}
      </section>

      {/* ===================================================================== */}
      {/* SECTION 7: RECENT ACTIVITY AND TRAVEL INSIGHTS                        */}
      {/* ===================================================================== */}
      <section className="space-y-4" aria-label="Recent Activity and Insights">
        <div>
          <h3 className="text-base font-black text-[var(--text-primary)] font-heading flex items-center gap-2">
            <IconTrendingUp size={18} className="text-blue-500" />
            <span>Recent Activity and Travel Insights</span>
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Verified usage telemetry and audit trail from your active travel profile
          </p>
        </div>

        {/* 4-Stat Metric Summary Bar */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          {[
            { label: 'Total Trips', value: totalTripsCount, sub: 'Active & archive', icon: <IconPlane size={18} className="text-blue-500" /> },
            { label: 'Destinations', value: uniqueDestinationsCount, sub: 'Cities mapped', icon: <IconMapPin size={18} className="text-amber-500" /> },
            { label: 'Total Budget', value: formatCurrency(totalPlannedBudget, userCurrency), sub: 'Canonical allocation', icon: <IconCash size={18} className="text-emerald-500" /> },
            { label: 'Travel Days', value: totalTravelDays, sub: 'Cumulative schedule', icon: <IconCalendar size={18} className="text-indigo-500" /> },
          ].map((stat, i) => (
            <div key={i} className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] flex flex-col justify-between shadow-sm">
              <div className="flex justify-between items-start">
                <span className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">{stat.icon}</span>
                <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">{stat.sub}</span>
              </div>
              <div className="mt-3">
                <div className="text-xl font-black text-[var(--text-primary)] font-heading truncate">{stat.value}</div>
                <div className="text-xs text-[var(--text-muted)] font-semibold mt-0.5">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity Timeline & AI Travel Brief */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Activity Log */}
          <div className="glass-card p-5 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-2">
              <IconActivity size={15} /> Recent Activity Timeline
            </h4>

            <div className="relative pl-5 border-l-2 border-[var(--border-color)] space-y-4">
              {recentActivities.length > 0 ? (
                recentActivities.slice(0, 4).map((act) => (
                  <div key={act.id} className="relative">
                    <div className="absolute -left-[27px] top-0.5 w-5 h-5 rounded-full border-2 border-[var(--bg-card)] bg-blue-500 text-white flex items-center justify-center text-[10px]">
                      •
                    </div>
                    <div className="text-xs font-bold text-[var(--text-primary)]">{act.title}</div>
                    <div className="text-[10px] text-[var(--text-muted)] flex items-center gap-1 mt-0.5">
                      <IconClock size={11} />
                      <span>{new Date(act.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short' })}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-[var(--text-muted)] italic">
                  No recent activity logged. Completed itinerary actions will appear here.
                </div>
              )}
            </div>
          </div>

          {/* AI Travel Assistant Brief Card */}
          <div className="glass-card p-5 rounded-2xl border border-blue-500/20 bg-gradient-to-br from-[var(--bg-card)] via-blue-950/10 to-transparent space-y-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
                  <IconSparkles size={15} className="text-blue-500" />
                  <span>AI Travel Assistant Summary</span>
                </h4>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-500 border border-blue-500/20">
                  Verified Engine
                </span>
              </div>

              <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
                {heroTrip ? (
                  <span>
                    Your travel profile is currently optimized for <strong className="text-[var(--text-primary)]">{heroTrip.destination}</strong>. All POIs are validated with physical coordinates, door-to-door transit routes include verified travel buffers, and budget tracking is active.
                  </span>
                ) : (
                  <span>
                    WanderWise crafts realistic, conflict-free travel itineraries with verified landmarks, accurate transit times, and smart budget tracking worldwide.
                  </span>
                )}
              </p>
            </div>

            <Link
              to="/chat"
              className="btn-outline w-full justify-center text-xs font-bold py-2 flex items-center gap-2 cursor-pointer"
            >
              <IconMessageChatbot size={15} />
              <span>Consult Travel Companion</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Simplified Trip Wizard Modal */}
      <TripWizard
        userId={userId}
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSuccess={handleCreateTrip}
      />
    </div>
  );
}
