import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  IconLayoutDashboard,
  IconMapPins,
  IconMessageChatbot,
  IconSparkles,
  IconMap,
  IconCloudStorm,
  IconBackpack,
  IconFileText,
  IconReceipt2,
  IconCoin,
  IconChartBar,
  IconBook,
  IconHeart,
  IconShieldCheck,
  IconSettings,
  IconUser,
  IconLogout,
  IconSun,
  IconMoon,
  IconX,
  IconPlaneDeparture,
  IconChecklist,
  IconCompass
} from '@tabler/icons-react';
import { useAuth } from '../context/AuthContext';

const NAV_GROUPS = [
  {
    title: 'MAIN',
    links: [
      { path: '/dashboard', label: 'Dashboard', icon: IconLayoutDashboard },
      { path: '/trips', label: 'My Trips', icon: IconMapPins },
      { path: '/chat', label: 'AI Chat', icon: IconMessageChatbot },
      { path: '/recommendations', label: 'AI Suggestions', icon: IconSparkles },
    ]
  },
  {
    title: 'TRAVEL',
    links: [
      { path: '/checklist', label: 'Smart Checklist', icon: IconChecklist },
      { path: '/guide', label: 'Local Travel Guide', icon: IconCompass },
      { path: '/transit', label: 'Maps & Transit', icon: IconMap },
      { path: '/weather', label: 'Weather', icon: IconCloudStorm },
      { path: '/packing', label: 'Packing', icon: IconBackpack },
      { path: '/documents', label: 'Documents Vault', icon: IconFileText },
    ]
  },
  {
    title: 'MONEY',
    links: [
      { path: '/budget', label: 'Expenses', icon: IconReceipt2 },
      { path: '/currency', label: 'Currency', icon: IconCoin },
      { path: '/analytics', label: 'Analytics', icon: IconChartBar },
    ]
  },
  {
    title: 'MEMORIES',
    links: [
      { path: '/journal/1', label: 'Journal', icon: IconBook },
      { path: '/wishlist', label: 'Wishlist', icon: IconHeart },
    ]
  },
  {
    title: 'SAFETY',
    links: [
      { path: '/safety', label: 'Safety', icon: IconShieldCheck },
    ]
  }
];

const BOTTOM_LINKS = [
  { path: '/settings', label: 'Settings', icon: IconSettings },
  { path: '/profile', label: 'Profile', icon: IconUser },
];

export default function Sidebar({ mobileOpen, setMobileOpen, isDark, toggleTheme }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const NavItem = ({ to, icon: Icon, label }) => {
    const isActive = location.pathname === to || (to !== '/' && to !== '/dashboard' && location.pathname.startsWith(to));
    
    return (
      <Link
        to={to}
        onClick={() => setMobileOpen && setMobileOpen(false)}
        className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
          isActive 
            ? 'bg-blue-600/10 text-blue-600 dark:text-blue-400 font-bold border border-blue-500/20 shadow-xs' 
            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-subtle)] hover:text-[var(--text-primary)]'
        }`}
      >
        <Icon size={18} stroke={isActive ? 2.2 : 1.8} className={isActive ? 'text-blue-600 dark:text-blue-400' : 'text-[var(--text-muted)]'} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-300"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside className={`fixed top-0 left-0 w-[260px] h-screen flex flex-col p-5 z-50 bg-[var(--bg-card)] border-r border-[var(--border-color)] transition-transform duration-300 ease-in-out ${
        mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full lg:translate-x-0'
      }`}>
        {/* Brand Header */}
        <div className="mb-6 pl-1.5 flex items-center justify-between">
          <Link to="/dashboard" onClick={() => setMobileOpen && setMobileOpen(false)} className="flex items-center gap-2.5 no-underline">
            <div className="p-2 rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20 flex items-center justify-center">
              <IconPlaneDeparture size={20} />
            </div>
            <div>
              <span className="text-lg font-black text-[var(--text-primary)] tracking-tight font-heading block leading-none">
                WanderWise
              </span>
              <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest block mt-0.5">
                Travel OS
              </span>
            </div>
          </Link>

          {/* Close button for mobile drawer */}
          <button
            onClick={() => setMobileOpen && setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] transition-colors"
            aria-label="Close Navigation"
          >
            <IconX size={18} />
          </button>
        </div>

        {/* Navigation Groups */}
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="text-[10px] font-extrabold text-[var(--text-muted)] uppercase tracking-wider pl-3 mb-1">
                {group.title}
              </div>
              {group.links.map((link) => (
                <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
              ))}
            </div>
          ))}
        </div>

        {/* Bottom Actions & Theme Toggle */}
        <div className="flex flex-col gap-1 mt-4 pt-3 border-t border-[var(--border-color)]">
          {toggleTheme && (
            <button
              onClick={toggleTheme}
              className="flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-semibold text-[var(--text-secondary)] bg-[var(--bg-subtle)] border border-[var(--border-color)] hover:text-[var(--text-primary)] transition-all cursor-pointer mb-1"
            >
              <span className="flex items-center gap-2">
                {isDark ? <IconSun size={16} className="text-amber-400" /> : <IconMoon size={16} className="text-indigo-600" />}
                <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
              </span>
            </button>
          )}

          {BOTTOM_LINKS.map((link) => (
            <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
          ))}

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-all w-full text-left cursor-pointer mt-0.5"
          >
            <IconLogout size={16} stroke={2} />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
