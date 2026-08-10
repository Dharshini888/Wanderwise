import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { IconMenu2, IconSun, IconMoon } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

export default function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('ww_theme', 'light');
      setIsDark(false);
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('ww_theme', 'dark');
      setIsDark(true);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem('ww_theme');
    if (saved === 'dark') {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    } else if (saved === 'light') {
      document.documentElement.classList.remove('dark');
      setIsDark(false);
    }
  }, []);

  return (
    <div className="flex min-h-screen w-full bg-[var(--bg-app)] text-[var(--text-secondary)] font-sans transition-colors duration-300 relative overflow-x-hidden">
      {/* Sidebar Component with Mobile Responsive Drawer */}
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} isDark={isDark} toggleTheme={toggleTheme} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col w-full lg:ml-[280px] transition-all duration-300 min-h-screen">
        {/* Mobile Header Bar */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-[var(--bg-card)] border-b border-[var(--border-color)] sticky top-0 z-30 shadow-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-2 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-panel)] transition-colors"
              aria-label="Open Navigation Menu"
            >
              <IconMenu2 size={22} />
            </button>
            <Link to="/dashboard" className="flex items-center gap-2 no-underline">
              <span className="text-xl">✈️</span>
              <span className="text-lg font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 font-heading">
                WanderWise
              </span>
            </Link>
          </div>

          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-panel)] transition-colors flex items-center gap-1 text-xs font-bold"
            title="Toggle Light/Dark Theme"
          >
            {isDark ? <IconSun size={18} className="text-amber-400" /> : <IconMoon size={18} className="text-indigo-600" />}
          </button>
        </header>

        {/* Page Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 box-border w-full max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
