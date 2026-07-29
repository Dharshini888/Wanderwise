import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen w-full bg-[var(--bg-app)] text-[var(--text-secondary)] font-sans transition-colors duration-300">
      {/* Fixed Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <main className="flex-1 ml-[280px] p-6 box-border min-h-screen">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
