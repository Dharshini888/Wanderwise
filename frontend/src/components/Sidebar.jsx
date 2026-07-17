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
  { path: '/companion', label: 'My Trips', icon: IconMapPins },
  { path: '/chat', label: 'AI Chat', icon: IconMessageChatbot },
  { path: '/recommendations', label: 'AI Suggestions', icon: IconSparkles },
  { path: '/group-consensus', label: 'Consensus', icon: IconUsersGroup },
  { path: '/weather', label: 'Weather', icon: IconCloudStorm },
  { path: '/transit', label: 'Maps', icon: IconMap },
  { path: '/budget', label: 'Expenses', icon: IconReceipt2 },
  { path: '/smart-budget', label: 'Smart Budget', icon: IconCalculator },
  { path: '/currency', label: 'Currency', icon: IconCoin },
  { path: '/packing', label: 'Packing', icon: IconBackpack },
  { path: '/journal/1', label: 'Journal', icon: IconBook }, // Using 1 as default for now, can be updated later
  { path: '/wishlist', label: 'Wishlist', icon: IconHeart },
  { path: '/safety', label: 'Safety', icon: IconShieldCheck },
  { path: '/health-docs', label: 'Health & Docs', icon: IconStethoscope },
  { path: '/analytics', label: 'Analytics', icon: IconChartBar },
];

const BOTTOM_LINKS = [
  { path: '/settings', label: 'Settings', icon: IconSettings },
  { path: '/profile', label: 'Profile', icon: IconUser },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const NavItem = ({ to, icon: Icon, label }) => {
    // Simple active check, handles nested routes like /journal/1 slightly better if needed
    const isActive = location.pathname.startsWith(to) && (to !== '/' || location.pathname === '/');
    
    return (
      <Link
        to={to}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '10px 14px',
          textDecoration: 'none',
          borderRadius: '10px',
          fontSize: '13px',
          fontWeight: isActive ? 600 : 500,
          color: isActive ? '#185FA5' : '#5a7a9a',
          background: isActive ? 'rgba(24, 95, 165, 0.12)' : 'transparent',
          transition: 'all 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = 'rgba(24, 95, 165, 0.05)';
            e.currentTarget.style.color = '#4a6080';
          }
        }}
        onMouseLeave={(e) => {
          if (!isActive) {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = '#5a7a9a';
          }
        }}
      >
        <Icon size={18} stroke={isActive ? 2.5 : 2} />
        <span>{label}</span>
      </Link>
    );
  };

  return (
    <aside className="glass-panel" style={{
      width: '240px', // slightly wider for breathing room
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      boxSizing: 'border-box',
      zIndex: 100,
    }}>
      {/* Logo */}
      <div style={{ marginBottom: '32px', paddingLeft: '8px' }}>
        <Link to="/dashboard" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '24px' }}>✈️</span>
          <span style={{ fontSize: '20px', fontWeight: 800, color: '#185FA5', letterSpacing: '-0.5px' }}>
            WanderWise
          </span>
        </Link>
      </div>

      {/* Main Navigation */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
        <div className="label-text" style={{ paddingLeft: '14px', marginBottom: '8px', marginTop: '8px' }}>Menu</div>
        {MAIN_LINKS.map((link) => (
          <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
        ))}
      </div>

      {/* Bottom Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(200, 225, 245, 0.6)' }}>
        {BOTTOM_LINKS.map((link) => (
          <NavItem key={link.path} to={link.path} icon={link.icon} label={link.label} />
        ))}
        <button
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: 500,
            color: '#dc2626', // Danger color
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            textAlign: 'left',
            width: '100%',
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(220, 38, 38, 0.08)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <IconLogout size={18} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
