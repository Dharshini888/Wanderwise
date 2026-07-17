import { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';

const COMMON_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'AUD', 'CAD', 'SGD', 'CHF', 'CNY'];

export default function Currency() {
  const [from, setFrom] = useState('USD');
  const [to, setTo] = useState('EUR');
  const [amount, setAmount] = useState('100');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const token = localStorage.getItem('token');

  const convertCurrency = async (e) => {
    if (e) e.preventDefault();
    if (!amount || isNaN(amount)) return;
    
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await fetch(`${API}/currency/convert?from_curr=${from}&to_curr=${to}&amount=${amount}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (res.ok) setResult(data);
      else setError(data.detail || 'Could not fetch exchange rates');
    } catch (_) { setError('Network error'); }
    setLoading(false);
  };

  const handleSwap = () => {
    setFrom(to);
    setTo(from);
  };

  const inputStyle = { width: '100%', padding: '14px 16px', borderRadius: '10px', border: '1px solid #c8dff0', background: 'rgba(255,255,255,0.9)', color: '#1a2a3a', fontSize: '16px', outline: 'none', boxSizing: 'border-box', fontWeight: 600 };
  const labelStyle = { display: 'block', marginBottom: '8px', fontSize: '12px', fontWeight: 600, color: '#5a7a9a', textTransform: 'uppercase' };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 className="text-primary-dark" style={{ margin: '0 0 4px', fontSize: '1.8rem', letterSpacing: '-0.5px' }}>💱 Currency Converter</h1>
        <p className="text-secondary" style={{ margin: 0, fontSize: '14px' }}>Real-time exchange rates for smarter travel.</p>
      </div>

      <div className="glass-card" style={{ padding: '32px', maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        <form onSubmit={convertCurrency} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={labelStyle}>Amount</label>
            <input style={inputStyle} type="number" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="Enter amount..." required />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>From</label>
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={from} onChange={e => setFrom(e.target.value)}>
                {COMMON_CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            
            <button type="button" onClick={handleSwap} style={{ background: 'rgba(24, 95, 165, 0.1)', border: 'none', width: '48px', height: '48px', borderRadius: '50%', color: '#185FA5', fontSize: '20px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '24px', transition: 'all 0.2s', boxShadow: '0 2px 8px rgba(24, 95, 165, 0.1)' }} onMouseEnter={e => e.currentTarget.style.background = 'rgba(24, 95, 165, 0.2)'} onMouseLeave={e => e.currentTarget.style.background = 'rgba(24, 95, 165, 0.1)'}>
              ⇄
            </button>
            
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>To</label>
              <select style={{ ...inputStyle, cursor: 'pointer' }} value={to} onChange={e => setTo(e.target.value)}>
                {COMMON_CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          
          <button type="submit" disabled={loading}
            style={{ width: '100%', padding: '16px', background: '#185FA5', border: 'none', borderRadius: '10px', color: 'white', fontWeight: 600, fontSize: '15px', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, transition: 'all 0.2s', boxShadow: '0 4px 14px rgba(24, 95, 165, 0.2)', marginTop: '8px' }}
            onMouseEnter={e => { if(!loading) e.currentTarget.style.transform = 'translateY(-2px)' }}
            onMouseLeave={e => { if(!loading) e.currentTarget.style.transform = 'translateY(0)' }}>
            {loading ? 'Converting...' : 'Convert Currency'}
          </button>
        </form>

        {error && <div style={{ background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', padding: '12px', color: '#dc2626', fontSize: '14px', fontWeight: 500 }}>⚠️ {error}</div>}

        {result && (
          <div style={{ marginTop: '16px', padding: '24px', background: 'rgba(24, 95, 165, 0.05)', borderRadius: '12px', border: '1px solid rgba(200, 225, 245, 0.5)', textAlign: 'center' }}>
            <div className="text-secondary" style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
              {parseFloat(amount).toLocaleString()} {from} =
            </div>
            <div className="text-primary-dark" style={{ fontSize: '42px', fontWeight: 800, color: '#185FA5', lineHeight: 1, letterSpacing: '-1px' }}>
              {result.converted_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span style={{ fontSize: '20px', fontWeight: 600, color: '#4a6080' }}>{to}</span>
            </div>
            <div className="text-muted" style={{ fontSize: '12px', marginTop: '12px' }}>
              Exchange Rate: 1 {from} = {result.rate?.toFixed(4)} {to}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
