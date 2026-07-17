import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/auth/login', form);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ width: '100%', maxWidth: '400px' }}>
        
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>✈️</span>
            <span style={{ fontSize: '22px', fontWeight: 800, color: '#185FA5', letterSpacing: '-0.5px' }}>
              WanderWise
            </span>
          </Link>
        </div>

        {/* Card */}
        <div className="glass-card" style={{ padding: '2.5rem' }}>
          <h2 className="text-primary-dark" style={{ margin: '0 0 0.5rem', fontSize: '1.5rem', textAlign: 'center' }}>
            Welcome back
          </h2>
          <p className="text-secondary" style={{ margin: '0 0 2rem', fontSize: '0.9rem', textAlign: 'center' }}>
            Sign in to continue your journey
          </p>

          {error && (
            <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', marginBottom: '1.5rem', color: '#dc2626', fontSize: '14px', fontWeight: 500 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {[
              { label: 'Email Address', name: 'email', type: 'email', placeholder: 'you@example.com' },
              { label: 'Password', name: 'password', type: 'password', placeholder: '••••••••' },
            ].map(({ label, name, type, placeholder }) => (
              <div key={name}>
                <label className="text-muted" style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase' }}>
                  {label}
                </label>
                <input
                  type={type}
                  name={name}
                  value={form[name]}
                  placeholder={placeholder}
                  onChange={e => setForm({ ...form, [name]: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '8px',
                    border: '1px solid #c8dff0',
                    background: 'rgba(255,255,255,0.9)',
                    color: '#1a2a3a',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    outline: 'none',
                    transition: 'all 0.2s ease'
                  }}
                  onFocus={e => {
                    e.target.style.border = '1px solid #185FA5';
                    e.target.style.boxShadow = '0 0 0 3px rgba(24, 95, 165, 0.15)';
                  }}
                  onBlur={e => {
                    e.target.style.border = '1px solid #c8dff0';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            ))}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '0.5rem',
                padding: '14px',
                background: '#185FA5',
                border: 'none',
                borderRadius: '10px',
                color: 'white',
                fontSize: '15px',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = '#134B84'; }}
              onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = '#185FA5'; }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '2rem', color: '#5a7a9a', fontSize: '14px' }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#185FA5', textDecoration: 'none', fontWeight: 600 }}>
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
