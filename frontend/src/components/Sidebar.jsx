import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  IconLayoutDashboard,
  IconMapPins,
  IconMessageChatbot,
  IconCloudStorm,
  IconMap,
  IconReceipt2,
  IconBackpack,
  IconBook,
  IconHeart,
  IconShieldCheck,
  IconChartBar,
  IconSettings,
  IconUser,
  IconLogout,
  IconSparkles,
  IconCoin,
  IconSun,
  IconMoon,
  IconX
} from '@tabler/icons-react';
import { useAuth } from '../context/AuthContext';

const MAIN_LINKS = [
  { path: '/dashboard', label: 'Dashboard', icon: IconLayoutDashboard },
  { path: '/trips', label: 'My Trips', icon: IconMapPins },
  { path: '/chat', label: 'AI Chat', icon: IconMessageChatbot },
  { path: '/recommendations', label: 'AI Suggestions', icon: IconSparkles },
  { path: '/weather', label: 'Weather', icon: IconCloudStorm },
  { path: '/transit', label: 'Maps & Transit', icon: IconMap },
  { path: '/budget', label: 'Expenses', icon: IconReceipt2 },
  { path: '/currency', label: 'Currency', icon: IconCoin },
  { path: '/packing', label: 'Packing', icon: IconBackpack },
  { path: '/journal/1', label: 'Journal', icon: IconBook },
  { path: '/wishlist', label: 'Wishlist', icon: IconHeart },
  { path: '/safety', label: 'Safety', icon: IconShieldCheck },
  { path: '/analytics', label: 'Analytics', icon: IconChartBar },
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
    const isActive = location.pathname.startsWith(to) && (to !== '/' || location.pathname === '/');
    
    return (
      <Link
        to={to}
        onClick={() => setMobileOpen && setMobileOpen(false)}
        className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
          isActive 
            ? 'bg-blue-50 dark:bg-blue-900/30 text-[var(--color-primary-600)] dark:text-blue-400 font-semibold shadow-sm border border-blue-200/50 dark:border-blue-800/40' 
            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)]'
        }`}
      >
        <Icon size={20} stroke={isActive ? 2.5 : 2} className={isActive ? 'text-[var(--color-primary-600)] dark:text-blue-400' : 'text-[var(--text-muted)]'} />
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
      <aside className={`glass-panel fixed top-0 left-0 w-[280px] h-screen flex flex-col p-6 z-50 bg-[var(--bg-card)] border-r border-[var(--border-color)] transition-transform duration-300 ease-in-out ${
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        {/* Logo & Mobile Close */}
        <div className="mb-6 pl-2 flex items-center justify-between">
          <Link to="/dashboard" onClick={() => setMobileOpen && setMobileOpen(false)} className="flex items-center gap-3 no-underline">
            <span className="text-3xl">✈️</span>
            <span className="text-2xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 tracking-tight font-heading">
              WanderWise
            </span>
          </Link>

          {/* Close button for mobile drawer */}
          <button
            onClick={() => setMobileOpen && setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-app)] transition-colors"
            aria-label="Close Navigation"
          >
            <IconX size={20} />
          </button>
        </div>

        {/* Main Navigation List */}
        <div className="flex-1 flex flex-col gap-1 overflow-y-auto pr-2 custom-scrollbar">
          <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider pl-3 mb-2 mt-1">
            Main Navigation
          </div>
          {MAIN_LINKS.map((link) => (
            <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
          ))}
        </div>

        {/* Bottom Actions & Theme Toggle */}
        <div className="flex flex-col gap-1.5 mt-4 pt-4 border-t border-[var(--border-color)]">
          {/* Theme Toggle Button */}
          {toggleTheme && (
            <button
              onClick={toggleTheme}
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-[var(--text-secondary)] bg-[var(--bg-app)] border border-[var(--border-color)] hover:text-[var(--text-primary)] transition-all"
            >
              <span className="flex items-center gap-2">
                {isDark ? <IconSun size={18} className="text-amber-400" /> : <IconMoon size={18} className="text-indigo-600" />}
                <span>{isDark ? 'Light Theme' : 'Dark Theme'}</span>
              </span>
              <span className="text-[10px] font-bold uppercase text-[var(--text-muted)]">{isDark ? 'DARK' : 'LIGHT'}</span>
            </button>
          )}

          {BOTTOM_LINKS.map((link) => (
            <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
          ))}

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3.5 py-2 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all w-full text-left mt-1"
          >
            <IconLogout size={18} stroke={2} />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
