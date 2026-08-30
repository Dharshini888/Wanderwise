import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { formatCurrency, getStoredUserId } from '../utils/formatters';
import { calculateTripDuration } from '../utils/date_helpers';
import {
  IconSearch, IconBell, IconSparkles, IconPlus, IconMapPin, IconCalendar, IconCash,
  IconSun, IconShieldCheck, IconMessageChatbot, IconCompass,
  IconMap, IconBackpack, IconReceipt2, IconChevronRight, IconTrendingUp,
  IconClock, IconHeart, IconPlane, IconActivity, IconAlertTriangle, IconCheck, IconBus, IconBuildingStore,
  IconWallet, IconTrash, IconX
} from '@tabler/icons-react';

import WeatherWidget from '../components/dashboard/WeatherWidget';
import RiskAnalyzerWidget from '../components/dashboard/RiskAnalyzerWidget';
import LanguageWidget from '../components/dashboard/LanguageWidget';
import PersonalizedWidget from '../components/dashboard/PersonalizedWidget';
import QuickCurrencyWidget from '../components/dashboard/QuickCurrencyWidget';
import TripCard from '../components/dashboard/TripCard';
import DashboardBudgetWidget from '../components/dashboard/DashboardBudgetWidget';
import ActiveTripWorkspace from '../components/dashboard/ActiveTripWorkspace';
import TripReadinessWidget from '../components/dashboard/TripReadinessWidget';
import DocumentsVaultWidget from '../components/dashboard/DocumentsVaultWidget';
import SmartChecklistWidget from '../components/checklist/SmartChecklistWidget';
import TripWizard from '../components/trips/TripWizard';
import { createTrip } from '../api/trips';

const API = 'http://localhost:8000/api';

const CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD'];
const TRAVEL_TYPES = ['leisure', 'adventure', 'business', 'family'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [budgetAlert, setBudgetAlert] = useState(null);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [recentActivities, setRecentActivities] = useState([]);

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : { name: 'Traveler', email: '' };

  const userId = getStoredUserId();

  const [form, setForm] = useState({
    destination: '', origin_city: 'Coimbatore', start_date: '', end_date: '', budget: '',
    travel_type: 'leisure', travel_style: 'solo', interests: 'sightseeing',
    group_size: '1', currency: user.currency || 'USD',
  });

  const [widgetData, setWidgetData] = useState(null);

  const fetchTrips = async () => {
    if (!userId || userId === 'undefined' || String(userId) === 'undefined') { setLoading(false); return; }
    try {
      const [tripsRes, widgetRes, notifRes, actRes] = await Promise.all([
        fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/trips/dashboard-widgets/${userId}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/notifications/unread-count`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/activity/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      if (tripsRes.ok) {
        const data = await tripsRes.json();
        if (Array.isArray(data)) setTrips(data);
      }
      
      if (widgetRes.ok) {
        const wData = await widgetRes.json();
        setWidgetData(wData);
      }
      
      if (notifRes.ok) {
        const notifData = await notifRes.json();
        setUnreadNotifications(notifData.unread_count);
      }
      
      if (actRes.ok) {
        const actData = await actRes.json();
        setRecentActivities(actData);
      }
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  const deleteTrip = async (id) => {
    try {
      await fetch(`${API}/trips/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      setTrips(trips.filter(t => t.id !== id));
    } catch (_) {}
  };

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      setSearchError(null);
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/trips/search?query=${encodeURIComponent(searchQuery.trim())}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data);
        } else {
          setSearchError('Search failed');
        }
      } catch (err) {
        setSearchError('Network error');
      } finally {
        setIsSearching(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, token]);

  useEffect(() => { fetchTrips(); }, []);

  const handleCreateTrip = async (payload) => {
    try {
      const newTrip = await createTrip(payload);
      fetchTrips();
      if (newTrip && newTrip.id) {
        navigate(`/trips/${newTrip.id}`);
      }
    } catch (_) {}
  };

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }));

  const submitTripForm = async (overrides = {}) => {
    setSubmitting(true);
    setBudgetAlert(null);
    try {
      const payload = {
        ...form,
        user_id: Number(userId),
        budget: parseFloat(form.budget),
        group_size: parseInt(form.group_size),
        ...overrides
      };
      const res = await fetch(`${API}/trips/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok && data.requires_confirmation && data.budget_alert) {
        setBudgetAlert(data.budget_alert);
      } else if (res.ok) {
        setShowForm(false);
        fetchTrips();
      }
    } catch (_) {}
    setSubmitting(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submitTripForm();
  };

  const getLocalDateStr = (d = new Date()) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const todayStr = getLocalDateStr();

  const formatDateStr = (dStr) => {
    if (!dStr) return '';
    return String(dStr).slice(0, 10);
  };

  const getDays = (t) => {
    return calculateTripDuration(t.start_date, t.end_date);
  };

  // Dates & Active Trip Tracking
  const activeTrip = trips.find(t => {
    if (!t.start_date || !t.end_date) return false;
    const start = formatDateStr(t.start_date);
    const end = formatDateStr(t.end_date);
    return start <= todayStr && todayStr <= end;
  });

  const upcomingTrips = trips.filter(t => {
    if (!t.start_date) return false;
    return formatDateStr(t.start_date) > todayStr;
  });

  const nextTrip = activeTrip || (upcomingTrips.length > 0 ? upcomingTrips[0] : (trips.length > 0 ? trips[0] : null));
  const displayTrip = activeTrip || nextTrip;
  const isDisplayTripActive = displayTrip && formatDateStr(displayTrip.start_date) <= todayStr && todayStr <= formatDateStr(displayTrip.end_date);

  const getDaysCountdown = (startDateStr) => {
    if (!startDateStr) return 0;
    const start = new Date(formatDateStr(startDateStr) + 'T00:00:00');
    const today = new Date(todayStr + 'T00:00:00');
    const diff = Math.ceil((start - today) / 86400000);
    return Math.max(0, diff);
  };

  const getCurrentDayNumber = (startDateStr) => {
    if (!startDateStr) return 1;
    const start = new Date(formatDateStr(startDateStr) + 'T00:00:00');
    const today = new Date(todayStr + 'T00:00:00');
    const diff = Math.floor((today - start) / 86400000);
    return Math.max(1, diff + 1);
  };

  const initials = user.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U';

  const quickActions = [
    { label: 'AI Itinerary', badge: '✓ Ready', badgeClass: 'bg-emerald-500/20 text-emerald-400', icon: <IconSparkles size={20}/>, path: '/recommendations', color: 'bg-purple-500' },
    { label: 'Transit Guide', badge: '✓ Generated', badgeClass: 'bg-emerald-500/20 text-emerald-400', icon: <IconMap size={20}/>, path: '/transit', color: 'bg-emerald-500' },
    { label: 'Packing Checklist', badge: '🟡 Review', badgeClass: 'bg-amber-500/20 text-amber-400', icon: <IconBackpack size={20}/>, path: '/packing', color: 'bg-amber-500' },
    { label: 'Budget Planner', badge: '✓ Healthy', badgeClass: 'bg-emerald-500/20 text-emerald-400', icon: <IconWallet size={20}/>, path: '/expenses', color: 'bg-blue-500' },
    { label: 'Safety Advisory', badge: '✓ Active', badgeClass: 'bg-emerald-500/20 text-emerald-400', icon: <IconShieldCheck size={20}/>, path: '/safety', color: 'bg-red-500' },
  ];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      {/* 1. TOP HEADER & GREETING BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card p-6 md:p-8 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-xl relative overflow-hidden">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              ✈️ TRAVEL COMMAND CENTER
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-[var(--text-primary)] font-heading tracking-tight">
            Good morning, {user.name || 'Traveler'}
          </h1>
          <p className="text-xs md:text-sm text-[var(--text-muted)] mt-1 font-normal">
            Your intelligent travel journey at a glance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Universal Search Bar */}
          <div className="relative w-full sm:w-64">
            <IconSearch size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search trips, destinations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-xs font-semibold focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            {searchResults && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl shadow-2xl z-50 p-2 max-h-60 overflow-y-auto">
                {searchResults.length > 0 ? (
                  searchResults.map(trip => (
                    <Link
                      key={trip.id}
                      to={`/trips/${trip.id}`}
                      className="p-2 hover:bg-[var(--bg-subtle)] rounded-xl flex items-center gap-2 no-underline"
                    >
                      <IconMapPin size={16} className="text-blue-500 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs font-bold text-[var(--text-primary)] truncate">{trip.destination}</div>
                        <div className="text-[10px] text-[var(--text-muted)]">{getDays(trip)} days</div>
                      </div>
                    </Link>
                  ))
                ) : (
                  <div className="p-3 text-center text-xs text-[var(--text-muted)]">No matching trips found</div>
                )}
              </div>
            )}
          </div>

          {/* New Trip Wizard Button */}
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center gap-2 px-5 py-2.5 text-xs font-bold shrink-0 cursor-pointer shadow-md shadow-blue-500/20"
          >
            <IconPlus size={16} />
            <span>Plan New Trip</span>
          </button>
        </div>
      </div>

      {/* Active Trip Workspace or Next Adventure Banner Card */}
      {(widgetData?.has_active_trip || isDisplayTripActive) ? (
        <ActiveTripWorkspace widgetData={widgetData} onRefresh={fetchTrips} />
      ) : displayTrip ? (
        <>
          <div 
            className="p-6 md:p-8 text-white rounded-3xl shadow-xl relative overflow-hidden animate-fadeIn border-0"
            style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)', color: '#ffffff' }}
          >
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-10">
              <div>
                <div className="inline-flex items-center gap-2 bg-blue-500/20 border border-blue-500/40 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-3 text-blue-300">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span> Next Adventure
                </div>
                <h2 className="text-3xl font-black font-heading text-white">
                  📍 {displayTrip.destination}
                </h2>
                <p className="text-sm mt-2 font-medium text-slate-300 flex items-center gap-3 flex-wrap">
                  <span>📅 {formatDateStr(displayTrip.start_date)} → {formatDateStr(displayTrip.end_date)}</span>
                  <span>•</span>
                  <span>⏱️ {getDays(displayTrip)} Days</span>
                  <span>•</span>
                  <span>💰 {formatCurrency(displayTrip.budget || 100000, displayTrip.currency || 'INR')}</span>
                </p>
              </div>

              <div className="flex items-center gap-4 bg-slate-800/80 border border-slate-700/80 p-4 rounded-2xl backdrop-blur-md">
                <div>
                  <div className="text-[10px] font-extrabold text-blue-400 uppercase tracking-wider">Countdown</div>
                  <div className="text-xl font-black text-white font-mono mt-0.5">
                    Starts in {getDaysCountdown(displayTrip.start_date)} days
                  </div>
                </div>
                <Link to={`/trips/${displayTrip.id}`} className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs shadow-md transition-colors flex items-center gap-1.5 shrink-0">
                  <IconSparkles size={16}/> View Itinerary
                </Link>
              </div>
            </div>
          </div>

          <TripReadinessWidget trip={displayTrip} daysLeft={getDaysCountdown(displayTrip.start_date)} />
          <DashboardBudgetWidget trip={displayTrip} />
        </>
      ) : null}

      {/* Quick Access Cards with Progress Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {quickActions.map((action, i) => (
          <div 
            key={i} 
            onClick={action.onClick ? action.onClick : () => navigate(action.path)}
            className="glass-card p-4 flex flex-col items-center justify-center gap-2.5 cursor-pointer hover:scale-105 transition-transform duration-200 group relative"
          >
            <div className={`w-11 h-11 rounded-xl text-white flex items-center justify-center shadow-md ${action.color} group-hover:shadow-lg transition-shadow`}>
              {action.icon}
            </div>
            <span className="text-xs font-bold text-[var(--text-primary)] text-center">{action.label}</span>
            <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${action.badgeClass}`}>
              {action.badge}
            </span>
          </div>
        ))}
      </div>

      {/* REQUIREMENT 6: Intelligent Budget Alert Modal / Card */}
      {budgetAlert && (
        <div className="glass-card p-6 border-2 border-amber-500 bg-amber-50/50 dark:bg-amber-950/20 rounded-2xl animate-fadeIn flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-amber-500 text-white rounded-xl flex-shrink-0">
              <IconAlertTriangle size={24} />
            </div>
            <div>
              <h3 className="text-lg font-black text-amber-800 dark:text-amber-400 font-heading">
                ⚠️ Budget Alert
              </h3>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Your budget appears lower than the estimated minimum cost for this destination.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 bg-[var(--bg-app)] p-4 rounded-xl border border-[var(--border-color)]">
            <div>
              <span className="text-xs text-[var(--text-muted)] font-bold uppercase">Estimated Minimum</span>
              <div className="text-xl font-black text-amber-600">{budgetAlert.currency} {budgetAlert.estimated_minimum?.toLocaleString()}</div>
            </div>
            <div>
              <span className="text-xs text-[var(--text-muted)] font-bold uppercase">Your Budget</span>
              <div className="text-xl font-black text-red-500">{budgetAlert.currency} {budgetAlert.user_budget?.toLocaleString()}</div>
            </div>
          </div>

          <div>
            <span className="text-xs font-bold uppercase text-[var(--text-muted)] tracking-wider">AI Suggestions</span>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
              {budgetAlert.suggestions?.map((sug, i) => (
                <li key={i} className="text-xs text-[var(--text-secondary)] flex items-center gap-1.5 font-medium">
                  <IconCheck size={14} className="text-emerald-500 flex-shrink-0" /> {sug}
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-3 border-t border-amber-200 dark:border-amber-900">
            <button 
              onClick={() => submitTripForm({ is_budget_friendly: true, force_create: true })}
              className="btn btn-primary bg-emerald-600 hover:bg-emerald-700 text-white py-2.5 px-5 text-xs font-bold flex-1"
            >
              🌱 Generate Budget-Friendly Itinerary
            </button>
            <button 
              onClick={() => submitTripForm({ force_create: true })}
              className="btn btn-outline py-2.5 px-4 text-xs font-bold"
            >
              Proceed with Original Budget
            </button>
            <button 
              onClick={() => setBudgetAlert(null)}
              className="py-2.5 px-4 text-xs text-[var(--text-muted)] hover:text-red-500 font-bold"
            >
              Edit Form
            </button>
          </div>
        </div>
      )}

      {/* 14-Step AI Trip Creation Wizard Modal */}
      <TripWizard
        userId={userId}
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSuccess={handleCreateTrip}
      />


      {/* Travel Statistics Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Trips', value: trips.length, icon: <IconPlane size={20} className="text-blue-500" />, sub: 'Active & past' },
          { label: 'Destinations', value: new Set(trips.map(t => (t.destination || '').split(',')[0])).size, icon: <IconMapPin size={20} className="text-amber-500" />, sub: 'Cities explored' },
          { label: 'Total Budget', value: formatCurrency(trips.reduce((s, t) => s + (t.budget || 0), 0)), icon: <IconCash size={20} className="text-emerald-500" />, sub: 'Planned expense' },
          { label: 'Travel Days', value: trips.reduce((s, t) => s + getDays(t), 0), icon: <IconCalendar size={20} className="text-indigo-500" />, sub: 'Cumulative days' },
        ].map((stat, i) => (
          <div key={i} className="glass-card p-5 flex flex-col justify-between relative overflow-hidden group hover:border-[var(--color-primary-500)] transition-colors">
            <div className="flex justify-between items-start">
              <span className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] group-hover:scale-110 transition-transform shadow-sm">{stat.icon}</span>
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">{stat.sub}</span>
            </div>
            <div className="mt-4">
              <div className="text-2xl font-black text-[var(--text-primary)] font-heading">{stat.value}</div>
              <div className="text-xs text-[var(--text-secondary)] font-semibold">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Dashboard Grid (Main Layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Upcoming & Active Trips */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* REQUIREMENT 8: Upcoming Trips Countdown Section */}
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconCalendar className="text-[var(--color-primary-500)]"/> 
              {activeTrip ? 'Your Itineraries' : 'Upcoming Trips'}
            </h2>
            <Link to="/companion" className="text-sm font-semibold text-[var(--color-primary-600)] hover:underline flex items-center gap-1">
              View All <IconChevronRight size={14}/>
            </Link>
          </div>
          
          {loading ? (
            <div className="h-40 glass-card animate-pulse rounded-2xl flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-[var(--color-primary-500)] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : trips.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {trips.slice(0, 4).map(trip => {
                const daysLeft = getDaysCountdown(trip.start_date);
                const isUpcoming = formatDateStr(trip.start_date) > todayStr;
                return (
                  <div key={trip.id} className="relative">
                    {isUpcoming && daysLeft >= 0 && (
                      <div className="absolute top-3 right-3 z-10 bg-blue-600 text-white text-[10px] font-extrabold px-2.5 py-1 rounded-full shadow-md flex items-center gap-1">
                        <IconClock size={12}/> Starts in {daysLeft} Days
                      </div>
                    )}
                    <TripCard trip={trip} token={token} getDays={getDays} onDelete={deleteTrip} />
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="glass-card p-10 flex flex-col items-center justify-center text-center gap-4 border-dashed border-2">
              <div className="w-16 h-16 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center text-[var(--color-primary-600)] dark:text-blue-400">
                <IconMapPin size={32} />
              </div>
              <div>
                <h3 className="font-bold text-[var(--text-primary)] font-heading text-lg">No trips planned yet</h3>
                <p className="text-sm text-[var(--text-muted)] max-w-xs mx-auto mt-1">Let our AI build the perfect itinerary for your next adventure.</p>
              </div>
              <button onClick={() => setShowForm(true)} className="btn btn-primary mt-2">Plan your first trip</button>
            </div>
          )}

          {/* Contextual Widgets row */}
          {nextTrip && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-2">
              <WeatherWidget trip={nextTrip} />
              <RiskAnalyzerWidget trip={nextTrip} token={token} />
            </div>
          )}

          {/* Lower Widgets row */}
          {nextTrip && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <LanguageWidget trip={nextTrip} token={token} />
              <QuickCurrencyWidget token={token} />
            </div>
          )}
        </div>

        {/* Right Column - Side Panel */}
        <div className="flex flex-col gap-6">
          {/* Personalized Recommendations */}
          <PersonalizedWidget trips={trips} token={token} />
          
          {/* Travel Documents Vault Widget */}
          <DocumentsVaultWidget />
          
          {/* Smart Travel Checklist Widget */}
          {displayTrip && (
            <SmartChecklistWidget
              tripId={displayTrip.id}
              tripTitle={displayTrip.title || displayTrip.destination}
            />
          )}
          
          {/* Recent Activity Timeline */}
          <div className="glass-card p-6 flex flex-col gap-5">
            <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2 flex items-center gap-2">
              <IconActivity size={16}/> Recent Activity
            </h3>
            
            <div className="relative pl-6 border-l-2 border-[var(--border-color)] flex flex-col gap-6">
              {recentActivities.length > 0 ? recentActivities.map((act) => {
                let IconComponent = IconActivity;
                if (act.icon === 'sparkles') IconComponent = IconSparkles;
                if (act.icon === 'map') IconComponent = IconMap;
                if (act.icon === 'receipt') IconComponent = IconReceipt2;
                if (act.icon === 'heart') IconComponent = IconHeart;
                
                let colorClass = 'text-blue-500 bg-blue-50 dark:bg-blue-900/20';
                if (act.color === 'amber') colorClass = 'text-amber-500 bg-amber-50 dark:bg-amber-900/20';
                if (act.color === 'emerald') colorClass = 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20';
                if (act.color === 'red') colorClass = 'text-red-500 bg-red-50 dark:bg-red-950/20';

                const timeAgo = new Date(act.created_at).toLocaleDateString();

                return (
                  <div key={act.id} className="relative">
                    <div className={`absolute -left-[35px] w-7 h-7 rounded-full border-4 border-[var(--bg-card)] flex items-center justify-center ${colorClass}`}>
                      <IconComponent size={14}/>
                    </div>
                    <div className="text-sm font-bold text-[var(--text-primary)]">{act.title}</div>
                    <div className="text-xs text-[var(--text-muted)] font-medium flex items-center gap-1 mt-0.5">
                      <IconClock size={12}/> {timeAgo}
                    </div>
                  </div>
                );
              }) : (
                <div className="text-sm text-[var(--text-muted)] italic">No recent activity</div>
              )}
            </div>
          </div>
          
          {/* Today's Travel Brief (AI Summary) */}
          <div className="glass-card p-6 bg-gradient-to-br from-[var(--bg-card)] to-blue-50/30 dark:to-blue-950/20 border border-blue-100 dark:border-blue-900/30 space-y-3">
            <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
              <IconTrendingUp size={16} className="text-blue-500"/> Today's Travel Brief
            </h3>
            {nextTrip && !isDisplayTripActive ? (
              <>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-semibold">
                  Your next adventure begins in {getDaysCountdown(nextTrip.start_date)} days. Your AI itinerary, transit guidance and packing checklist are ready.
                </p>
                <ul className="text-xs text-[var(--text-muted)] space-y-1 font-medium pt-1">
                  <li className="flex items-center gap-1.5"><span className="text-emerald-500 font-bold">✓</span> Itinerary fully prepared</li>
                  <li className="flex items-center gap-1.5"><span className="text-emerald-500 font-bold">✓</span> Transit guide generated</li>
                  <li className="flex items-center gap-1.5"><span className="text-amber-500 font-bold">🟡</span> Packing checklist pending review</li>
                  <li className="flex items-center gap-1.5"><span className="text-blue-500 font-bold">ℹ</span> Weather will be refreshed before departure</li>
                  <li className="flex items-center gap-1.5"><span className="text-emerald-500 font-bold">✓</span> Budget planner active</li>
                </ul>
              </>
            ) : isDisplayTripActive ? (
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-semibold">
                You're currently exploring {displayTrip.destination.split(',')[0]}! Today's itinerary is ready.
              </p>
            ) : (
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-semibold">
                Welcome back! Your travel journal and memory vault are ready for your past trips.
              </p>
            )}
            <Link to="/chat" className="btn btn-outline w-full justify-center text-xs font-extrabold mt-2">
              <IconMessageChatbot size={16}/> Chat with AI Companion
            </Link>
          </div>
          
        </div>
      </div>
      
    </div>
  );
}
