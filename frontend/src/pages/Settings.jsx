import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  IconSettings, IconWorld, IconPalette, IconBell, IconLock, IconInfoCircle, 
  IconAlertTriangle, IconCheck, IconTrash, IconDeviceMobile, IconMail, IconDeviceDesktop,
  IconBrandGoogle, IconBrandGithub, IconShieldCheck
} from '@tabler/icons-react';

const CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'AED', 'SGD', 'SAR', 'CHF'];
const LANGUAGES = ['English', 'Hindi', 'French', 'Spanish', 'German', 'Japanese', 'Arabic'];
const THEMES = ['Light', 'Dark', 'Auto'];

const DEFAULT_SETTINGS = {
  currency: 'USD', language: 'English', theme: 'Light',
  notifTripReminders: true, notifWeatherAlerts: true,
  notifBudgetWarnings: true, notifAISuggestions: true,
  notifMarketing: false, notifDeals: true,
  privacyShareData: false, privacyAnalytics: true,
};

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--color-primary-500)] dark:focus:ring-offset-slate-900 ${
        checked ? 'bg-[var(--color-primary-600)]' : 'bg-[var(--border-color)]'
      }`}
    >
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
    </button>
  );
}

function SectionCard({ title, icon, children, borderColor = "border-[var(--border-color)]", bgClasses = "bg-[var(--bg-card)]" }) {
  return (
    <div className={`glass-card p-6 ${bgClasses} border ${borderColor} flex flex-col gap-5`}>
      <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-2">
        {icon} {title}
      </h3>
      <div className="flex flex-col gap-4">{children}</div>
    </div>
  );
}

function Row({ label, sub, children }) {
  return (
    <div className="flex justify-between items-center gap-4">
      <div className="flex-1 pr-4">
        <div className="text-sm font-semibold text-[var(--text-primary)]">{label}</div>
        {sub && <div className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-snug">{sub}</div>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

function Divider() {
  return <div className="h-px bg-[var(--border-color)]" />;
}

// --- Tabs ---

function AccountSettingsTab({ settings, update, confirmClear, setConfirmClear, handleClearCache, handleDeleteAccount }) {
  const selectClass = "px-4 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)] cursor-pointer min-w-[150px]";

  return (
    <div className="flex flex-col gap-6 animate-fadeIn">
      {/* Account Info */}
      <SectionCard title="Regional & Display" icon={<IconWorld size={18} className="text-[var(--color-primary-600)]" />}>
        <Row label="Language" sub="Interface display language">
          <select className={selectClass} value={settings.language} onChange={e => update('language', e.target.value)}>
            {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </Row>
        <Divider />
        <Row label="Default Currency" sub="Used across budget and expense features">
          <select className={selectClass} value={settings.currency} onChange={e => update('currency', e.target.value)}>
            {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </Row>
        <Divider />
        <Row label="Theme" sub="Color scheme for the app">
          <div className="flex gap-2 p-1 bg-[var(--bg-app)] rounded-xl border border-[var(--border-color)]">
            {THEMES.map(t => (
              <button
                key={t}
                onClick={() => update('theme', t)}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  settings.theme === t
                    ? 'bg-white dark:bg-slate-800 text-[var(--color-primary-600)] shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </Row>
      </SectionCard>

      {/* Connected Accounts */}
      <SectionCard title="Connected Accounts" icon={<IconShieldCheck size={18} className="text-emerald-500" />}>
        <Row label="Google" sub="Sign in with Google">
          <button className="text-xs font-bold px-3 py-1.5 rounded-lg bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400 flex items-center gap-1">
             Disconnect
          </button>
        </Row>
        <Divider />
        <Row label="GitHub" sub="Link your GitHub account">
          <button className="text-xs font-bold px-3 py-1.5 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:bg-[var(--border-color)] flex items-center gap-1">
             Connect
          </button>
        </Row>
      </SectionCard>

      {/* Session Management */}
      <SectionCard title="Active Sessions" icon={<IconDeviceDesktop size={18} className="text-purple-500" />}>
        <div className="flex flex-col gap-3">
          <div className="flex items-start justify-between p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-app)]">
            <div className="flex gap-3 items-center">
              <IconDeviceDesktop className="text-[var(--color-primary-500)]" size={24} />
              <div>
                <div className="text-sm font-bold text-[var(--text-primary)]">Windows PC - Chrome</div>
                <div className="text-[10px] text-[var(--text-muted)] font-medium">New York, USA • Active now</div>
              </div>
            </div>
          </div>
          <div className="flex items-start justify-between p-3 rounded-xl border border-[var(--border-color)]">
            <div className="flex gap-3 items-center">
              <IconDeviceMobile className="text-[var(--text-muted)]" size={24} />
              <div>
                <div className="text-sm font-bold text-[var(--text-primary)]">iPhone 14 Pro - Safari</div>
                <div className="text-[10px] text-[var(--text-muted)] font-medium">New York, USA • Last active 2 hours ago</div>
              </div>
            </div>
            <button className="text-[10px] text-red-500 font-bold hover:underline">Revoke</button>
          </div>
        </div>
      </SectionCard>

      {/* Data & Privacy */}
      <SectionCard title="Privacy & Data" icon={<IconLock size={18} className="text-blue-400" />}>
        <Row label="Performance Analytics" sub="Track app performance and error reports">
          <Toggle checked={settings.privacyAnalytics} onChange={v => update('privacyAnalytics', v)} />
        </Row>
        <Divider />
        <Row label="Clear AI Cache" sub="Force refresh recommendations and weather data">
          <button
            onClick={handleClearCache}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold border cursor-pointer transition-all flex items-center gap-1 ${
              confirmClear
                ? 'bg-red-50 dark:bg-red-950/20 border-red-300 dark:border-red-800 text-red-600'
                : 'bg-[var(--bg-app)] border-[var(--border-color)] text-[var(--text-muted)] hover:bg-[var(--border-color)]'
            }`}
          >
            <IconTrash size={14} /> {confirmClear ? 'Confirm?' : 'Clear Cache'}
          </button>
        </Row>
      </SectionCard>

      {/* Danger Zone */}
      <SectionCard 
        title="Danger Zone" 
        icon={<IconAlertTriangle size={18} className="text-red-500" />} 
        bgClasses="bg-red-50/30 dark:bg-red-950/5" 
        borderColor="border-red-200/50 dark:border-red-900/20"
      >
        <Row label="Delete Account" sub="Permanently delete your account and all data">
          <button
            onClick={handleDeleteAccount}
            className="px-4 py-2 rounded-lg text-xs font-bold border border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 bg-transparent hover:bg-red-500 hover:text-white hover:border-red-500 cursor-pointer transition-all"
          >
            Delete Account
          </button>
        </Row>
      </SectionCard>
    </div>
  );
}

function NotificationSettingsTab({ settings, update }) {
  return (
    <div className="flex flex-col gap-6 animate-fadeIn">
      
      <SectionCard title="Travel Alerts" icon={<IconPlane size={18} className="text-[var(--color-primary-600)]" />}>
        <Row label="Trip Reminders" sub="Get reminded before upcoming trips and flights">
          <Toggle checked={settings.notifTripReminders} onChange={v => update('notifTripReminders', v)} />
        </Row>
        <Divider />
        <Row label="Weather Alerts" sub="Receive severe weather warnings for your destination">
          <Toggle checked={settings.notifWeatherAlerts} onChange={v => update('notifWeatherAlerts', v)} />
        </Row>
        <Divider />
        <Row label="Budget Warnings" sub="Alert when spending exceeds 80% of trip budget">
          <Toggle checked={settings.notifBudgetWarnings} onChange={v => update('notifBudgetWarnings', v)} />
        </Row>
      </SectionCard>

      <SectionCard title="AI Features" icon={<IconSparkles size={18} className="text-amber-500" />}>
        <Row label="Proactive Suggestions" sub="Receive personalized travel tips and recommendations">
          <Toggle checked={settings.notifAISuggestions} onChange={v => update('notifAISuggestions', v)} />
        </Row>
      </SectionCard>

      <SectionCard title="Email Preferences" icon={<IconMail size={18} className="text-emerald-500" />}>
        <Row label="Travel Deals" sub="Exclusive discounts and flight price drops">
          <Toggle checked={settings.notifDeals} onChange={v => update('notifDeals', v)} />
        </Row>
        <Divider />
        <Row label="WanderWise Newsletter" sub="Monthly updates, tips, and feature announcements">
          <Toggle checked={settings.notifMarketing} onChange={v => update('notifMarketing', v)} />
        </Row>
      </SectionCard>

    </div>
  );
}

// --- Main Settings Component ---

export default function Settings() {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [activeTab, setActiveTab] = useState('account');

  useEffect(() => {
    let base = { ...DEFAULT_SETTINGS };
    const stored = localStorage.getItem('ww_settings');
    if (stored) {
      try { base = { ...base, ...JSON.parse(stored) }; } catch (_) {}
    }
    if (user) {
      if (user.currency) base.currency = user.currency;
      if (user.languages) base.language = user.languages;
    }
    setSettings(base);
  }, [user]);

  const update = (key, val) => setSettings(prev => ({ ...prev, [key]: val }));

  const handleSave = async () => {
    localStorage.setItem('ww_settings', JSON.stringify(settings));
    if (updateUser) {
      try {
        await updateUser({
          currency: settings.currency,
          languages: settings.language,
        });
      } catch (_) {}
    }
    if (settings.theme === 'Dark') {
      document.documentElement.classList.add('dark');
    } else if (settings.theme === 'Auto') {
      if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    } else {
      document.documentElement.classList.remove('dark');
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleClearCache = () => {
    if (!confirmClear) { setConfirmClear(true); return; }
    Object.keys(localStorage).forEach(k => {
      if (k.startsWith('lang_guide_') || k.startsWith('personalized_') || k.startsWith('weather_dash_')) {
        localStorage.removeItem(k);
      }
    });
    setConfirmClear(false);
    alert('AI cache cleared! Widgets will reload fresh data on next visit.');
  };

  const handleDeleteAccount = () => {
    if (window.confirm('This will permanently delete your account and all local data. Continue?')) {
      localStorage.clear();
      navigate('/login');
    }
  };

  const tabs = [
    { id: 'account', label: 'Account & Security', icon: <IconLock size={18} /> },
    { id: 'notifications', label: 'Notifications', icon: <IconBell size={18} /> },
  ];

  return (
    <div className="flex flex-col gap-6 pb-20 max-w-3xl mx-auto">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          Settings
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Manage your account settings and preferences.</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-[var(--border-color)] mb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
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
      <div className="min-h-[500px]">
        {activeTab === 'account' && (
          <AccountSettingsTab 
            settings={settings} 
            update={update} 
            confirmClear={confirmClear} 
            setConfirmClear={setConfirmClear}
            handleClearCache={handleClearCache}
            handleDeleteAccount={handleDeleteAccount}
          />
        )}
        {activeTab === 'notifications' && (
          <NotificationSettingsTab settings={settings} update={update} />
        )}
      </div>

      {/* Sticky Action Row */}
      <div className="fixed bottom-0 left-0 right-0 sm:left-[280px] p-4 bg-[var(--bg-card)]/90 backdrop-blur-md border-t border-[var(--border-color)] flex justify-end gap-3 z-50">
        <button
          onClick={() => navigate(-1)}
          className="px-5 py-2.5 rounded-xl border border-[var(--border-color)] text-sm font-semibold text-[var(--text-muted)] hover:bg-[var(--bg-app)] cursor-pointer transition-all"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className={`px-8 py-2.5 rounded-xl text-sm font-bold text-white shadow-md cursor-pointer transition-all flex items-center gap-1.5 ${
            saved
              ? 'bg-emerald-500 shadow-emerald-500/20 hover:-translate-y-0.5'
              : 'bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] shadow-blue-500/15 hover:-translate-y-0.5'
          }`}
        >
          {saved ? <><IconCheck size={16} /> Saved Successfully</> : 'Save Settings'}
        </button>
      </div>

    </div>
  );
}
