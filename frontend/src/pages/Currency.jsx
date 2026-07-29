import { useState, useEffect } from 'react';
import {
  IconCoin,
  IconArrowsExchange,
  IconAlertCircle,
  IconLoader,
  IconWallet,
  IconArrowsRightLeft,
  IconTrendingUp,
} from '@tabler/icons-react';

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

  useEffect(() => {
    convertCurrency();
  }, [from, to]);

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconCoin className="text-emerald-500" size={32} /> Currency Converter
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Real-time exchange rates for smarter budgeting on the go.</p>
      </div>

      <div className="glass-card p-6 sm:p-8 max-w-xl mx-auto w-full bg-[var(--bg-card)] flex flex-col gap-6">
        
        <form onSubmit={convertCurrency} className="flex flex-col gap-5">
          <div>
            <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Amount to Convert</label>
            <input 
              className="w-full px-4 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-base font-extrabold focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-2 focus:ring-[var(--color-primary-500)]/15 font-heading" 
              type="number" 
              step="0.01" 
              value={amount} 
              onChange={e => setAmount(e.target.value)} 
              placeholder="Enter amount..." 
              required 
            />
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">From</label>
              <select 
                className="w-full px-3.5 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm font-semibold focus:outline-none cursor-pointer"
                value={from} 
                onChange={e => setFrom(e.target.value)}
              >
                {COMMON_CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            
            <button 
              type="button" 
              onClick={handleSwap} 
              className="bg-blue-50 dark:bg-blue-950 text-[var(--color-primary-600)] dark:text-blue-400 border border-blue-100 dark:border-blue-900 w-11 h-11 rounded-full flex items-center justify-center cursor-pointer shadow-sm mt-5 hover:bg-[var(--color-primary-600)] hover:text-white dark:hover:bg-blue-600 dark:hover:text-white transition-all transform active:scale-95"
              title="Swap currencies"
            >
              <IconArrowsExchange size={22} />
            </button>
            
            <div className="flex-1">
              <label className="block mb-1.5 text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">To</label>
              <select 
                className="w-full px-3.5 py-3 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm font-semibold focus:outline-none cursor-pointer"
                value={to} 
                onChange={e => setTo(e.target.value)}
              >
                {COMMON_CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          
          <button 
            type="submit" 
            disabled={loading}
            className="btn btn-primary w-full py-4 mt-4 text-sm font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/15 cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <>
                <IconLoader className="animate-spin" size={18} />
                <span>Converting...</span>
              </>
            ) : (
              <>
                <IconArrowsRightLeft size={18} />
                <span>Convert Currency</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-600 dark:text-red-400 text-sm font-semibold flex items-center gap-2">
            <IconAlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="p-6 bg-blue-50/20 dark:bg-blue-950/5 border border-blue-200/50 dark:border-blue-900/10 rounded-2xl text-center flex flex-col gap-2 animate-fadeIn">
            <div className="text-xs text-[var(--text-muted)] font-semibold">
              {parseFloat(amount).toLocaleString()} {from} =
            </div>
            <div className="text-3xl sm:text-4xl font-black text-[var(--color-primary-600)] dark:text-blue-400 font-heading">
              {result.converted_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-lg font-bold text-[var(--text-secondary)]">{to}</span>
            </div>
            <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mt-3 flex items-center justify-center gap-1.5">
              <IconTrendingUp size={12} className="text-emerald-500" /> Exchange Rate: 1 {from} = {result.rate?.toFixed(4)} {to}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
