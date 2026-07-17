import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD', 'AED', 'CHF'];
const LANGUAGES = ['English', 'Hindi', 'French', 'Spanish', 'German', 'Japanese', 'Arabic'];
const THEMES = ['Light', 'Dark', 'Auto'];
const UNITS = ['Celsius', 'Fahrenheit'];
const DISTANCE_UNITS = ['Kilometers', 'Miles'];

const DEFAULT_SETTINGS = {
  currency: 'USD',
  language: 'English',
  theme: 'Light',
  tempUnit: 'Celsius',
  distanceUnit: 'Kilometers',
  notifTripReminders: true,
  notifWeatherAlerts: true,
  notifBudgetWarnings: true,
  notifAISuggestions: true,
  privacyShareData: false,
  privacyAnalytics: true,
};

function ToggleSwitch({ checked, onChange }) {
  return (
    <div
      onClick={() => onChange(!checked)}
      style={{
        width: '44px', height: '24px', borderRadius: '12px',
        background: checked ? '#185FA5' : '#c8dff0',
        position: 'relative', cursor: 'pointer',
        transition: 'background 0.25s ease', flexShrink: 0,
      }}
    >
      <div style={{
        width: '18px', height: '18px', borderRadius: '50%',
        background: 'white', position: 'absolute',
        top: '3px', left: checked ? '23px' : '3px',
        transition: 'left 0.25s ease',
        boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
      }} />
    </div>
  );
}

function SectionCard({ title, icon, children }) {
  return (
    <div className="glass-card" style={{ padding: '24px' }}>
      <h3 style={{ margin: '0 0 20px', fontSize: '15px', fontWeight: 700, color: '#1a2a3a', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>{icon}</span> {title}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {children}
      </div>
    </div>
  );
}

function SettingRow({ label, sublabel, children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
      <div>
        <div style={{ fontSize: '14px', fontWeight: 600, color: '#1a2a3a' }}>{label}</div>
        {sublabel && <div style={{ fontSize: '12px', color: '#5a7a9a', marginTop: '2px' }}>{sublabel}</div>}
      </div>
      {children}
    </div>
  );
}

export default function Settings() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('ww_settings');
    if (stored) {
      try { setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(stored) }); } catch (_) {}
    }
  }, []);

  const update = (key, val) => setSettings(prev => ({ ...prev, [key]: val }));

  const handleSave = () => {
    localStorage.setItem('ww_settings', JSON.stringify(settings));
    
    // Apply theme immediately
    if (settings.theme === 'Dark') {
      document.documentElement.classList.add('dark');
    } else if (settings.theme === 'Auto') {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
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
    // Clear AI cache keys
    Object.keys(localStorage).forEach(k => {
      if (k.startsWith('lang_guide_') || k.startsWith('personalized_') || k.startsWith('weather_dash_')) {
        localStorage.removeItem(k);
      }
    });
    setConfirmClear(false);
    alert('AI cache cleared! Widgets will reload fresh data on next visit.');
  };

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure? This will log you out and clear all local data. Your account data on the server will need to be deleted separately.')) {
      localStorage.clear();
      navigate('/login');
    }
  };

  const selectStyle = {
    padding: '8px 12px', borderRadius: '8px', border: '1px solid #c8dff0',
    background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '13px',
    outline: 'none', cursor: 'pointer', minWidth: '140px',
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto' }}>

      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>
          Settings
        </h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>
          Customize your WanderWise experience.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

        {/* ── Regional Preferences ── */}
        <SectionCard title="Regional Preferences" icon="🌍">
          <SettingRow label="Default Currency" sublabel="Used across budget and expense features">
            <select style={selectStyle} value={settings.currency} onChange={e => update('currency', e.target.value)}>
              {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </SettingRow>
          <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)' }} />
          <SettingRow label="Language" sublabel="Interface display language">
            <select style={selectStyle} value={settings.language} onChange={e => update('language', e.target.value)}>
              {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </SettingRow>
          <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)' }} />
          <SettingRow label="Temperature Unit" sublabel="Shown in weather widgets">
            <select style={selectStyle} value={settings.tempUnit} onChange={e => update('tempUnit', e.target.value)}>
              {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </SettingRow>
          <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)' }} />
          <SettingRow label="Distance Unit" sublabel="Shown in transit and maps">
            <select style={selectStyle} value={settings.distanceUnit} onChange={e => update('distanceUnit', e.target.value)}>
              {DISTANCE_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </SettingRow>
        </SectionCard>

        {/* ── Appearance ── */}
        <SectionCard title="Appearance" icon="🎨">
          <SettingRow label="Theme" sublabel="Color scheme for the app">
            <div style={{ display: 'flex', gap: '8px' }}>
              {THEMES.map(t => (
                <button
                  key={t}
                  onClick={() => update('theme', t)}
                  style={{
                    padding: '7px 14px', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                    border: settings.theme === t ? '2px solid var(--accent)' : '1px solid var(--card-border)',
                    background: settings.theme === t ? 'var(--accent-light)' : 'var(--input-bg)',
                    color: settings.theme === t ? 'var(--accent)' : 'var(--text-muted)',
                    transition: 'all 0.2s',
                  }}
                >
                  {t}
                </button>
              ))}
            </div>
          </SettingRow>
        </SectionCard>

        {/* ── Notifications ── */}
        <SectionCard title="Notifications" icon="🔔">
          {[
            { key: 'notifTripReminders', label: 'Trip Reminders', sub: 'Get reminded before upcoming trips' },
            { key: 'notifWeatherAlerts', label: 'Weather Alerts', sub: 'Receive severe weather warnings for destinations' },
            { key: 'notifBudgetWarnings', label: 'Budget Warnings', sub: 'Alert when spending exceeds 80% of budget' },
            { key: 'notifAISuggestions', label: 'AI Suggestions', sub: 'Proactive tips from WanderWise AI' },
          ].map(({ key, label, sub }, i) => (
            <div key={key}>
              {i > 0 && <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)', marginBottom: '16px' }} />}
              <SettingRow label={label} sublabel={sub}>
                <ToggleSwitch checked={settings[key]} onChange={v => update(key, v)} />
              </SettingRow>
            </div>
          ))}
        </SectionCard>

        {/* ── Privacy ── */}
        <SectionCard title="Privacy & Data" icon="🔒">
          <SettingRow label="Share Anonymous Usage Data" sublabel="Help improve WanderWise with anonymous analytics">
            <ToggleSwitch checked={settings.privacyShareData} onChange={v => update('privacyShareData', v)} />
          </SettingRow>
          <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)' }} />
          <SettingRow label="Performance Analytics" sublabel="Track app performance and error reports">
            <ToggleSwitch checked={settings.privacyAnalytics} onChange={v => update('privacyAnalytics', v)} />
          </SettingRow>
          <div style={{ height: '1px', background: 'rgba(200,225,245,0.6)' }} />
          <SettingRow label="Clear AI Widget Cache" sublabel="Force refresh language guide, recommendations & weather">
            <button
              onClick={handleClearCache}
              style={{
                padding: '8px 16px', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                border: `1px solid ${confirmClear ? '#dc2626' : '#c8dff0'}`,
                background: confirmClear ? 'rgba(220,38,38,0.08)' : 'rgba(255,255,255,0.9)',
                color: confirmClear ? '#dc2626' : '#5a7a9a',
                transition: 'all 0.2s', whiteSpace: 'nowrap',
              }}
            >
              {confirmClear ? '⚠️ Confirm Clear' : '🗑️ Clear Cache'}
            </button>
          </SettingRow>
        </SectionCard>

        {/* ── About ── */}
        <SectionCard title="About" icon="ℹ️">
          {[
            { label: 'App Version', val: 'WanderWise v2.0.0' },
            { label: 'AI Provider', val: 'Gemini + Groq (fallback)' },
            { label: 'Weather Data', val: 'Open-Meteo (free, no key)' },
            { label: 'Maps Data', val: 'OpenStreetMap' },
          ].map(({ label, val }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: '#5a7a9a' }}>{label}</span>
              <span style={{ fontWeight: 600, color: '#1a2a3a' }}>{val}</span>
            </div>
          ))}
        </SectionCard>

        {/* ── Danger Zone ── */}
        <div className="glass-card" style={{ padding: '24px', border: '1px solid rgba(220,38,38,0.2)', background: 'rgba(220,38,38,0.02)' }}>
          <h3 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 700, color: '#dc2626' }}>⚠️ Danger Zone</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#1a2a3a' }}>Clear All Local Data</div>
              <div style={{ fontSize: '12px', color: '#5a7a9a', marginTop: '2px' }}>Clears all cached data and logs you out</div>
            </div>
            <button
              onClick={handleDeleteAccount}
              style={{
                padding: '9px 18px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                border: '1px solid #dc2626', background: 'transparent', color: '#dc2626',
                cursor: 'pointer', transition: 'all 0.2s',
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(220,38,38,0.08)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
            >
              Clear & Logout
            </button>
          </div>
        </div>

        {/* Save Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingBottom: '2rem' }}>
          <button
            onClick={() => navigate(-1)}
            style={{ padding: '12px 24px', borderRadius: '10px', border: '1px solid #c8dff0', background: 'transparent', color: '#5a7a9a', fontWeight: 600, fontSize: '14px', cursor: 'pointer' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '12px 32px', borderRadius: '10px', border: 'none',
              background: saved ? '#16a34a' : '#185FA5', color: 'white',
              fontWeight: 700, fontSize: '14px', cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(24,95,165,0.25)',
              transition: 'all 0.3s ease',
            }}
          >
            {saved ? '✓ Saved!' : 'Save Settings'}
          </button>
        </div>

      </div>
    </div>
  );
}
