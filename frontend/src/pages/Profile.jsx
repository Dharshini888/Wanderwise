import { useState, useEffect } from 'react';

export default function Profile() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) setUser(JSON.parse(userStr));
  }, []);

  const inputStyle = { width: '100%', padding: '12px 14px', borderRadius: '8px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.6)', color: '#4a6080', fontSize: '14px', outline: 'none', boxSizing: 'border-box' };
  const labelStyle = { display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  if (!user) return <div style={{ padding: '2rem' }}>Loading profile...</div>;

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>My Profile</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Manage your account settings and preferences.</p>
      </div>

      <div className="glass-card" style={{ padding: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '32px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#185FA5', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', fontWeight: 800 }}>
            {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <h2 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '20px' }}>{user.name}</h2>
            <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>{user.email}</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={labelStyle}>Full Name</label>
            <input style={inputStyle} value={user.name} readOnly />
          </div>
          <div>
            <label style={labelStyle}>Email Address</label>
            <input style={inputStyle} value={user.email} readOnly />
          </div>
          <div>
            <label style={labelStyle}>Phone Number</label>
            <input style={inputStyle} value={user.phone_number || 'Not provided'} readOnly />
          </div>
        </div>

        <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid rgba(200, 225, 245, 0.6)' }}>
          <button style={{ padding: '12px 24px', background: 'transparent', border: '1px solid #185FA5', borderRadius: '8px', color: '#185FA5', fontWeight: 600, cursor: 'pointer', fontSize: '14px', width: '100%', transition: 'all 0.2s' }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(24, 95, 165, 0.05)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            Edit Profile
          </button>
        </div>
      </div>
    </div>
  );
}
