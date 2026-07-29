import { useState, useEffect } from 'react';
import {
  IconUser, IconMail, IconPhone, IconCheck, IconPlane, IconMapPin, IconCalendar,
  IconEdit, IconSettings, IconShieldLock, IconCamera, IconDeviceFloppy,
  IconX, IconHeart, IconCurrencyDollar, IconWalk, IconTent, IconBuildingSkyscraper
} from '@tabler/icons-react';

// --- Tab Components ---

function OverviewTab({ user, stats }) {
  const initials = user.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U';

  return (
    <div className="flex flex-col gap-6 animate-fadeIn">
      {/* Avatar + Name Card */}
      <div className="glass-card p-6 bg-gradient-to-r from-[var(--bg-card)] to-blue-50/30 dark:to-blue-950/20 flex flex-col sm:flex-row items-center sm:items-start gap-6 relative overflow-hidden border border-blue-100 dark:border-blue-900/30">
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-[var(--color-primary-500)] to-[var(--color-primary-700)] text-white flex items-center justify-center text-3xl font-black font-heading shadow-xl shadow-blue-500/30 flex-shrink-0 relative group">
          {initials}
          <div className="absolute inset-0 bg-black/40 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
            <IconCamera size={24} className="text-white" />
          </div>
        </div>
        <div className="flex-1 min-w-0 text-center sm:text-left flex flex-col justify-center h-24">
          <h2 className="text-2xl font-black text-[var(--text-primary)] font-heading truncate">{user.name || 'Traveler'}</h2>
          <p className="text-sm font-medium text-[var(--text-muted)] truncate">{user.email}</p>
          <div className="mt-auto">
            <span className="inline-flex items-center gap-1 mt-2 text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 px-2.5 py-1 rounded-full border border-emerald-200 dark:border-emerald-900 shadow-sm">
              <IconCheck size={12} /> Verified Member
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {stats.map((s, i) => (
          <div key={i} className="glass-card p-5 flex flex-col items-center justify-center gap-2 text-center hover:border-[var(--color-primary-500)] transition-colors group">
            <div className="p-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] group-hover:scale-110 transition-transform">
              {s.icon}
            </div>
            <div>
              <div className="text-2xl font-black text-[var(--text-primary)] font-heading leading-tight">{s.value}</div>
              <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mt-1">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Badges & Achievements */}
      <div className="glass-card p-6 flex flex-col gap-4">
        <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
          🏆 Travel Badges
        </h3>
        <div className="flex flex-wrap gap-3">
          {['Globetrotter', 'Early Adopter', 'Planner Pro'].map(badge => (
            <div key={badge} className="px-4 py-2 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-500 shadow-sm">
              🌟 {badge}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EditProfileTab({ user, onSave }) {
  const [formData, setFormData] = useState({
    firstName: user.name?.split(' ')[0] || '',
    lastName: user.name?.split(' ').slice(1).join(' ') || '',
    email: user.email || '',
    phone: user.phone_number || '',
    dob: '',
    country: 'United States',
    city: '',
    bio: '',
    emergencyContact: ''
  });

  const handleChange = (e) => setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ ...user, name: `${formData.firstName} ${formData.lastName}`.trim(), email: formData.email, phone_number: formData.phone });
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card p-6 flex flex-col gap-6 animate-fadeIn border-t-4 border-t-[var(--color-primary-500)]">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        
        {/* Personal Info */}
        <div className="sm:col-span-2 border-b border-[var(--border-color)] pb-2 mb-2">
          <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">Personal Information</h3>
        </div>
        
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">First Name *</label>
          <input required name="firstName" value={formData.firstName} onChange={handleChange} className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Last Name *</label>
          <input required name="lastName" value={formData.lastName} onChange={handleChange} className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Email Address *</label>
          <input required type="email" name="email" value={formData.email} onChange={handleChange} className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Phone Number</label>
          <input type="tel" name="phone" value={formData.phone} onChange={handleChange} className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all" />
        </div>
        
        {/* Location & Bio */}
        <div className="sm:col-span-2 border-b border-[var(--border-color)] pb-2 mb-2 mt-4">
          <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">Location & Bio</h3>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Country</label>
          <select name="country" value={formData.country} onChange={handleChange} className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] transition-all">
            <option>United States</option>
            <option>United Kingdom</option>
            <option>Canada</option>
            <option>Australia</option>
            <option>India</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">City</label>
          <input name="city" value={formData.city} onChange={handleChange} placeholder="e.g. New York" className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] transition-all" />
        </div>
        <div className="sm:col-span-2 flex flex-col gap-1.5">
          <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Short Bio</label>
          <textarea name="bio" value={formData.bio} onChange={handleChange} rows={3} placeholder="Tell us about your travel style..." className="w-full px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] transition-all resize-none"></textarea>
        </div>

      </div>
      
      {/* Action Buttons */}
      <div className="flex justify-end gap-3 mt-4 pt-6 border-t border-[var(--border-color)]">
        <button type="button" className="px-5 py-2.5 rounded-xl border border-[var(--border-color)] text-sm font-semibold text-[var(--text-muted)] hover:bg-[var(--bg-app)] transition-colors">
          Discard Changes
        </button>
        <button type="submit" className="btn btn-primary px-6 py-2.5 text-sm flex items-center gap-2 shadow-md shadow-blue-500/20">
          <IconDeviceFloppy size={18} /> Save Profile
        </button>
      </div>
    </form>
  );
}

function TravelPreferencesTab() {
  const token = localStorage.getItem('token');
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [prefs, setPrefs] = useState({
    style: 'Solo',
    budget: 'Mid-range ($50–150/day)',
    climate: 'Beach 🏖️',
    currency: 'USD',
    diet: 'No Preference',
    language: 'English',
    activities: ['Photography', 'Sightseeing', 'Food & Dining'],
  });

  useEffect(() => {
    const fetchPrefs = async () => {
      if (!token) return;
      try {
        const res = await fetch('http://localhost:8000/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setPrefs({
            style: data.travel_styles ? data.travel_styles.split(',')[0].trim() : 'Solo',
            budget: data.preferred_budget || 'Mid-range ($50–150/day)',
            climate: data.preferred_climate || 'Beach 🏖️',
            currency: data.currency || 'USD',
            diet: data.dietary_preferences || 'No Preference',
            language: data.languages || 'English',
            activities: data.preferred_activities ? data.preferred_activities.split(',').map(a=>a.trim()) : ['Photography', 'Sightseeing'],
          });
        }
      } catch (_) {}
    };
    fetchPrefs();
  }, [token]);

  const toggleActivity = (act) => {
    setPrefs(p => ({
      ...p, 
      activities: p.activities.includes(act) 
        ? p.activities.filter(a => a !== act)
        : [...p.activities, act]
    }));
  };

  const handleSave = async () => {
    setLoading(true); setSaved(false);
    try {
      const res = await fetch('http://localhost:8000/api/auth/me/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          preferred_budget: prefs.budget,
          currency: prefs.currency,
          travel_styles: prefs.style,
          preferred_climate: prefs.climate,
          preferred_activities: prefs.activities.join(', '),
          languages: prefs.language,
          dietary_preferences: prefs.diet,
        })
      });
      if (res.ok) {
        setSaved(true);
        const data = await res.json();
        localStorage.setItem('user', JSON.stringify(data));
      }
    } catch (_) {}
    setLoading(false);
  };

  return (
    <div className="glass-card p-6 flex flex-col gap-8 animate-fadeIn border-t-4 border-t-amber-500">
      
      {saved && (
        <div className="bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 p-3.5 rounded-xl text-xs font-bold flex items-center gap-2">
          <IconCheck size={16}/> Preferences saved successfully! Your AI recommendations will automatically adapt.
        </div>
      )}

      <div>
        <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-1 flex items-center gap-2">
          <IconPlane size={18} className="text-[var(--color-primary-500)]" /> Primary Travel Style
        </h3>
        <p className="text-xs text-[var(--text-muted)] mb-4">How do you usually like to travel?</p>
        <div className="flex flex-wrap gap-2.5">
          {['Solo', 'Couple', 'Family', 'Friends', 'Business', 'Adventure', 'Luxury', 'Backpacking', 'Food & Dining'].map(style => (
            <button 
              key={style}
              type="button"
              onClick={() => setPrefs({...prefs, style})}
              className={`px-4 py-2 rounded-full text-xs font-bold border transition-all ${
                prefs.style === style 
                  ? 'bg-blue-50 dark:bg-blue-900/30 border-[var(--color-primary-500)] text-[var(--color-primary-600)] dark:text-blue-400 shadow-sm' 
                  : 'bg-[var(--bg-app)] border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--color-primary-500)]'
              }`}
            >
              {style}
            </button>
          ))}
        </div>
      </div>

      <div className="border-t border-[var(--border-color)] pt-6">
        <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-4 flex items-center gap-2">
          <IconCurrencyDollar size={18} className="text-emerald-500" /> Budget Range & Currency
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase">Budget Category</label>
            <select 
              value={prefs.budget} 
              onChange={e => setPrefs({...prefs, budget: e.target.value})}
              className="w-full p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none"
            >
              <option value="Budget (<$50/day)">Budget (&lt;$50/day)</option>
              <option value="Mid-range ($50–150/day)">Mid-range ($50–150/day)</option>
              <option value="Comfort ($150–350/day)">Comfort ($150–350/day)</option>
              <option value="Luxury ($350+/day)">Luxury ($350+/day)</option>
            </select>
          </div>
          <div>
            <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase">Preferred Currency</label>
            <select 
              value={prefs.currency} 
              onChange={e => setPrefs({...prefs, currency: e.target.value})}
              className="w-full p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-sm focus:outline-none"
            >
              {['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="border-t border-[var(--border-color)] pt-6">
        <h3 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-1 flex items-center gap-2">
          <IconWalk size={18} className="text-amber-500" /> Favorite Activities
        </h3>
        <p className="text-xs text-[var(--text-muted)] mb-4">Select all that apply to tailor AI recommendations.</p>
        <div className="flex flex-wrap gap-2">
          {['Nature', 'Beaches', 'Mountains', 'Historical', 'Food & Dining', 'Shopping', 'Museums & Arts', 'Adventure Sports', 'Nightlife', 'Photography'].map(act => (
            <button 
              key={act}
              type="button"
              onClick={() => toggleActivity(act)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-1.5 ${
                prefs.activities.includes(act) 
                  ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-500 text-amber-700 dark:text-amber-500 shadow-sm' 
                  : 'bg-[var(--bg-app)] border-[var(--border-color)] text-[var(--text-secondary)] hover:bg-[var(--border-color)]'
              }`}
            >
              {prefs.activities.includes(act) && <IconCheck size={14} />} {act}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-3 mt-2 pt-6 border-t border-[var(--border-color)]">
        <button 
          onClick={handleSave} 
          disabled={loading}
          className="btn btn-primary px-6 py-2.5 text-sm shadow-md flex items-center gap-2"
        >
          <IconDeviceFloppy size={18} /> {loading ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>

    </div>
  );
}

// --- Main Component ---

export default function Profile() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) setUser(JSON.parse(userStr));
    else setUser({ name: 'Guest User', email: 'guest@example.com', created_at: new Date().toISOString() });
  }, []);

  if (!user) return null;

  const stats = [
    { label: 'Trips Planned', value: user.trip_count || '12', icon: <IconPlane size={24} className="text-[var(--color-primary-600)]" /> },
    { label: 'Countries',     value: user.country_count || '5', icon: <IconMapPin size={24} className="text-emerald-500" /> },
    { label: 'Member Since',  value: user.created_at ? new Date(user.created_at).getFullYear() : '2023', icon: <IconCalendar size={24} className="text-amber-500" /> },
  ];

  const handleSaveProfile = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
    alert('Profile saved successfully!');
    setActiveTab('overview');
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <IconUser size={18} /> },
    { id: 'edit', label: 'Edit Profile', icon: <IconEdit size={18} /> },
    { id: 'prefs', label: 'Travel Preferences', icon: <IconHeart size={18} /> },
  ];

  return (
    <div className="flex flex-col gap-6 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          My Profile
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Manage your personal information and travel preferences.</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-[var(--border-color)] mb-2 overflow-x-auto custom-scrollbar pb-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-[var(--color-primary-600)] text-[var(--color-primary-600)] dark:text-blue-400'
                : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)] rounded-t-lg'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && <OverviewTab user={user} stats={stats} />}
        {activeTab === 'edit' && <EditProfileTab user={user} onSave={handleSaveProfile} />}
        {activeTab === 'prefs' && <TravelPreferencesTab />}
      </div>
    </div>
  );
}
