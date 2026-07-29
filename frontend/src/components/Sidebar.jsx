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
  IconUsersGroup,
  IconStethoscope,
  IconSparkles,
  IconCalculator,
  IconCoin,
} from '@tabler/icons-react';

const MAIN_LINKS = [
  { path: '/dashboard', label: 'Dashboard', icon: IconLayoutDashboard },
  { path: '/trips', label: 'My Trips', icon: IconMapPins },
  { path: '/chat', label: 'AI Chat', icon: IconMessageChatbot },

  { path: '/recommendations', label: 'AI Suggestions', icon: IconSparkles },
  { path: '/weather', label: 'Weather', icon: IconCloudStorm },
  { path: '/transit', label: 'Maps', icon: IconMap },
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

import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
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
        className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
          isActive 
            ? 'bg-blue-50 dark:bg-blue-900/30 text-[var(--color-primary-600)] dark:text-blue-400 font-semibold shadow-sm' 
            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-app)] hover:text-[var(--text-primary)]'
        }`}
      >
        <Icon size={20} stroke={isActive ? 2.5 : 2} className={isActive ? 'text-[var(--color-primary-600)] dark:text-blue-400' : 'text-[var(--text-muted)]'} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <aside className="glass-panel fixed top-0 left-0 w-[280px] h-screen flex flex-col p-6 z-50 bg-[var(--bg-card)] border-r border-[var(--border-color)]">
      {/* Logo */}
      <div className="mb-8 pl-2 flex items-center gap-3">
        <Link to="/dashboard" className="flex items-center gap-3 no-underline">
          <span className="text-3xl">✈️</span>
          <span className="text-2xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 tracking-tight font-heading">
            WanderWise
          </span>
        </Link>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 flex flex-col gap-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider pl-3 mb-2 mt-2">
          Menu
        </div>
        {MAIN_LINKS.map((link) => (
          <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="flex flex-col gap-1 mt-6 pt-5 border-t border-[var(--border-color)]">
        {BOTTOM_LINKS.map((link) => (
          <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
        ))}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200 w-full text-left"
        >
          <IconLogout size={20} stroke={2} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
