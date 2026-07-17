import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '', phone_number: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/auth/register', form);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    }
    setLoading(false);
  };

  const fields = [
    { label: 'Full Name', name: 'name', type: 'text', placeholder: 'John Doe', required: true },
    { label: 'Email Address', name: 'email', type: 'email', placeholder: 'you@example.com', required: true },
    { label: 'Phone Number', name: 'phone_number', type: 'tel', placeholder: '+91 98765 43210', required: false },
    { label: 'Password', name: 'password', type: 'password', placeholder: 'Min. 8 characters', required: true },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ width: '100%', maxWidth: '440px' }}>
        
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
            Create Your Account
          </h2>
          <p className="text-secondary" style={{ margin: '0 0 2rem', fontSize: '0.9rem', textAlign: 'center' }}>
            Join smart travelers around the world
          </p>

          {error && (
            <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', marginBottom: '1.5rem', color: '#dc2626', fontSize: '14px', fontWeight: 500 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {fields.map(({ label, name, type, placeholder, required }) => (
              <div key={name}>
                <label className="text-muted" style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase' }}>
                  {label} {!required && <span style={{ fontWeight: 400, textTransform: 'none' }}>(optional)</span>}
                </label>
                <input
                  type={type}
                  name={name}
                  value={form[name]}
                  placeholder={placeholder}
                  onChange={e => setForm({ ...form, [name]: e.target.value })}
                  required={required}
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
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '2rem', color: '#5a7a9a', fontSize: '14px' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#185FA5', textDecoration: 'none', fontWeight: 600 }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
