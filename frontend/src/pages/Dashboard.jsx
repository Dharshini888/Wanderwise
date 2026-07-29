import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { formatCurrency } from '../utils/formatters';
import {
  IconSearch, IconBell, IconSparkles, IconPlus, IconMapPin, IconCalendar, IconCash,
  IconSun, IconShieldCheck, IconMessageChatbot, IconCompass,
  IconMap, IconBackpack, IconReceipt2, IconChevronRight, IconTrendingUp,
  IconClock, IconHeart, IconPlane, IconActivity, IconAlertTriangle, IconCheck, IconBus, IconBuildingStore
} from '@tabler/icons-react';

import WeatherWidget from '../components/dashboard/WeatherWidget';
import RiskAnalyzerWidget from '../components/dashboard/RiskAnalyzerWidget';
import LanguageWidget from '../components/dashboard/LanguageWidget';
import PersonalizedWidget from '../components/dashboard/PersonalizedWidget';
import QuickCurrencyWidget from '../components/dashboard/QuickCurrencyWidget';
import TripCard from '../components/dashboard/TripCard';
import DashboardBudgetWidget from '../components/dashboard/DashboardBudgetWidget';
import ActiveTripWorkspace from '../components/dashboard/ActiveTripWorkspace';
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
  const [submitting, setSubmitting] = useState(false);
  const [budgetAlert, setBudgetAlert] = useState(null);

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : { name: 'Traveler', email: '' };
  
  let userId = null;
  try {
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub || payload.user_id || payload.id;
    }
  } catch (_) {}

  const [form, setForm] = useState({
    destination: '', origin_city: 'Coimbatore', start_date: '', end_date: '', budget: '',
    travel_type: 'leisure', travel_style: 'solo', interests: 'sightseeing',
    group_size: '1', currency: user.currency || 'USD',
  });

  const [widgetData, setWidgetData] = useState(null);

  const fetchTrips = async () => {
    if (!userId) { setLoading(false); return; }
    try {
      const res = await fetch(`${API}/trips/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok && Array.isArray(data)) setTrips(data);

      const widgetRes = await fetch(`${API}/trips/dashboard-widgets/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (widgetRes.ok) {
        const wData = await widgetRes.json();
        setWidgetData(wData);
      }
    } catch (_) {}
    setLoading(false);
  };


  const deleteTrip = async (id) => {
    if (!window.confirm("Are you sure you want to delete this trip itinerary?")) return;
    // Optimistic UI update
    setTrips(prev => prev.filter(t => t.id !== id));
    try {
      let res = await fetch(`${API}/trips/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        res = await fetch(`${API}/trips/delete/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      fetchTrips();
    } catch (_) {
      fetchTrips();
    }
  };

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
    if (!t || !t.start_date || !t.end_date) return 0;
    const start = new Date(formatDateStr(t.start_date) + 'T00:00:00');
    const end = new Date(formatDateStr(t.end_date) + 'T00:00:00');
    return Math.max(1, Math.round((end - start) / 86400000) + 1);
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
    { label: 'Create Trip', icon: <IconPlus size={20}/>, path: '#', onClick: () => setShowForm(true), color: 'bg-blue-500' },
    { label: 'Plan with AI', icon: <IconSparkles size={20}/>, path: '/recommendations', color: 'bg-purple-500' },
    { label: 'Transit Guide', icon: <IconMap size={20}/>, path: '/transit', color: 'bg-emerald-500' },
    { label: 'Packing Checklist', icon: <IconBackpack size={20}/>, path: '/packing', color: 'bg-amber-500' },
    { label: 'Safety & Emergency', icon: <IconShieldCheck size={20}/>, path: '/safety', color: 'bg-red-500' },
  ];

  return (
    <div className="flex flex-col gap-8 pb-10">
      
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-card p-4 rounded-2xl sticky top-4 z-40 bg-[var(--bg-card)]/80 backdrop-blur-xl border border-[var(--border-color)]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary-500)] to-[var(--color-primary-700)] text-white flex items-center justify-center font-bold text-sm shadow-md">
            {initials}
          </div>
          <div>
            <h1 className="text-lg font-bold text-[var(--text-primary)] font-heading leading-tight">
              Hello, {user.name?.split(' ')[0] || 'Traveler'} 👋
            </h1>
            <p className="text-xs text-[var(--text-muted)] font-medium">Ready for your next adventure?</p>
          </div>
        </div>
        
        <div className="flex flex-1 max-w-md items-center gap-2">
          <div className="relative flex-1">
            <IconSearch size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input 
              type="text" 
              placeholder="Search destinations, guides..." 
              className="w-full pl-9 pr-4 py-2.5 bg-[var(--bg-app)] border border-[var(--border-color)] rounded-xl text-sm focus:outline-none focus:border-[var(--color-primary-500)] transition-colors"
            />
          </div>
          <button className="p-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-secondary)] hover:text-[var(--color-primary-600)] transition-colors relative">
            <IconBell size={18} />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-[var(--bg-app)]"></span>
          </button>
          <Link to="/chat" className="p-2.5 rounded-xl bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] transition-colors shadow-md shadow-blue-500/20 flex items-center gap-1.5">
            <IconSparkles size={16} />
            <span className="text-sm font-semibold hidden sm:inline">Ask AI</span>
          </Link>
        </div>
      </div>

      {/* Active Trip Workspace or Generic Active Trip Banner */}
      {(widgetData?.has_active_trip || isDisplayTripActive) ? (
        <ActiveTripWorkspace widgetData={widgetData} onRefresh={fetchTrips} />
      ) : displayTrip ? (
        <>
          <div 
            className="p-6 text-white rounded-3xl shadow-xl relative overflow-hidden animate-fadeIn border-0"
            style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #4338ca 50%, #6d28d9 100%)', color: '#ffffff' }}
          >
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-10">
              <div>
                <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-2 text-white" style={{ color: '#ffffff' }}>
                  <span className="w-2 h-2 rounded-full bg-blue-400"></span> Upcoming Trip
                </div>
                <h2 className="text-2xl sm:text-3xl font-black font-heading flex items-center gap-2 text-white !text-white" style={{ color: '#ffffff' }}>
                  🗓️ Upcoming: {displayTrip.destination}
                </h2>
                <p className="text-sm mt-1 font-medium text-white/90 !text-white/90" style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                  {formatDateStr(displayTrip.start_date)} to {formatDateStr(displayTrip.end_date)}
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link to={`/trips/${displayTrip.id}`} className="px-5 py-2.5 rounded-xl bg-white text-blue-700 font-bold text-xs shadow-md hover:bg-blue-50 transition-colors flex items-center gap-1.5" style={{ backgroundColor: '#ffffff', color: '#1d4ed8' }}>
                  <IconSparkles size={16}/> View Itinerary
                </Link>
              </div>
            </div>
          </div>
          <DashboardBudgetWidget trip={displayTrip} />
        </>
      ) : null}


      {/* Quick Access Cards */}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {quickActions.map((action, i) => (
          <div 
            key={i} 
            onClick={action.onClick ? action.onClick : () => navigate(action.path)}
            className="glass-card p-4 flex flex-col items-center justify-center gap-3 cursor-pointer hover:scale-105 transition-transform duration-200 group"
          >
            <div className={`w-12 h-12 rounded-xl text-white flex items-center justify-center shadow-md ${action.color} group-hover:shadow-lg transition-shadow`}>
              {action.icon}
            </div>
            <span className="text-xs font-bold text-[var(--text-primary)] text-center">{action.label}</span>
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
          
          {/* Recent Activity Timeline */}
          <div className="glass-card p-6 flex flex-col gap-5">
            <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2 flex items-center gap-2">
              <IconActivity size={16}/> Recent Activity
            </h3>
            
            <div className="relative pl-6 border-l-2 border-[var(--border-color)] flex flex-col gap-6">
              {[
                { title: nextTrip ? `Planned Trip to ${nextTrip.destination.split(',')[0]}` : 'Explored Recommendations', time: 'Recently', icon: <IconPlane size={14}/>, color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20' },
                { title: 'AI Itinerary & Transit Generated', time: 'Today', icon: <IconSparkles size={14}/>, color: 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' },
                { title: 'Preferences Updated', time: 'Active Profile', icon: <IconHeart size={14}/>, color: 'text-red-500 bg-red-50 dark:bg-red-950/20' },
                { title: 'Budget Analysis Verified', time: 'Active', icon: <IconReceipt2 size={14}/>, color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' },
              ].map((act, i) => (
                <div key={i} className="relative">
                  <div className={`absolute -left-[35px] w-7 h-7 rounded-full border-4 border-[var(--bg-card)] flex items-center justify-center ${act.color}`}>
                    {act.icon}
                  </div>
                  <div className="text-sm font-bold text-[var(--text-primary)]">{act.title}</div>
                  <div className="text-xs text-[var(--text-muted)] font-medium flex items-center gap-1 mt-0.5">
                    <IconClock size={12}/> {act.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Today's Travel Brief (AI Summary) */}
          <div className="glass-card p-6 bg-gradient-to-br from-[var(--bg-card)] to-blue-50/30 dark:to-blue-950/20 border border-blue-100 dark:border-blue-900/30">
            <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3 flex items-center gap-2">
              <IconTrendingUp size={16} className="text-blue-500"/> Today's Travel Brief
            </h3>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-4">
              {nextTrip 
                ? `You're exploring ${nextTrip.destination.split(',')[0]}! Check your personalized itinerary, transit steps, and budget updates.` 
                : "No active trip right now. Enter a destination above or try AI Discover to find top attractions & hidden gems!"}
            </p>
            <Link to="/chat" className="btn btn-outline w-full justify-center text-sm">
              <IconMessageChatbot size={16}/> Chat with AI Assistant
            </Link>
          </div>
          
        </div>
      </div>
      
    </div>
  );
}
