import React from 'react';

export default function HealthAndDocs() {
  const documents = [
    { id: 1, type: 'Passport', expiry: '2027-03-15', status: 'Valid' },
    { id: 2, type: 'Japan e-Visa', expiry: '2023-10-01', status: 'Expired' }
  ];

  return (
    <div style={{ minHeight: '100vh', padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f4f7fa' }}>
      <h1 className="text-primary-dark" style={{ marginBottom: '1rem' }}>Health & Documents Vault</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', width: '100%', maxWidth: '1000px' }}>
        
        {/* Visa & Docs Section */}
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem', color: '#185FA5' }}>Digital Vault</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {documents.map(doc => (
              <div key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(255,255,255,0.5)', borderRadius: '12px', borderLeft: doc.status === 'Valid' ? '4px solid #52c41a' : '4px solid #ff4d4f' }}>
                <div>
                  <strong>{doc.type}</strong>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>Expires: {doc.expiry}</div>
                </div>
                <span style={{ fontSize: '0.8rem', padding: '4px 8px', borderRadius: '8px', background: doc.status === 'Valid' ? '#e6f7ff' : '#fff1f0', color: doc.status === 'Valid' ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
          <button style={{ marginTop: '1.5rem', padding: '10px 20px', width: '100%', background: '#185FA5', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer' }}>
            + Upload Document
          </button>
        </div>

        {/* Health & Dietary Section */}
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem', color: '#185FA5' }}>Dietary & Allergy Scanner</h2>
          <div style={{ padding: '2rem', border: '2px dashed #cbd5e1', borderRadius: '12px', textAlign: 'center', background: 'rgba(255,255,255,0.4)', cursor: 'pointer', transition: 'background 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.8)'} onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.4)'}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📷</div>
            <p style={{ color: '#666', margin: 0 }}>Scan Menu</p>
          </div>
          
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#fff1f0', borderRadius: '12px', border: '1px solid #ffccc7' }}>
            <h4 style={{ color: '#cf1322', margin: '0 0 0.5rem 0' }}>⚠ Alert</h4>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#cf1322' }}>Based on your profile, the last scanned menu contained <strong>peanuts</strong>. Please verify with staff.</p>
          </div>
        </div>

      </div>
    </div>
  );
}
