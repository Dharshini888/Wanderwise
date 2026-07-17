import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      {/* Fixed Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <main style={{
        flex: 1,
        marginLeft: '240px', // Matches sidebar width
        padding: '1.5rem',
        boxSizing: 'border-box',
        minHeight: '100vh',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
