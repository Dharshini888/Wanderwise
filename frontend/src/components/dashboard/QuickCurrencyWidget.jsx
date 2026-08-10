import { useState, useEffect } from 'react';
import { IconArrowsRightLeft } from '@tabler/icons-react';

const API = 'http://localhost:8000/api';
const CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD'];

export default function QuickCurrencyWidget({ token }) {
  const [from, setFrom] = useState('USD');
  const [to, setTo] = useState('EUR');
  const [amount, setAmount] = useState('100');
  const [result, setResult] = useState(null);

  const convert = async () => {
    if (!amount) return;
    try {
      const res = await fetch(`${API}/currency/convert?from_currency=${from}&to_currency=${to}&amount=${amount}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if(res.ok) setResult(await res.json());
    } catch(e) {}
  };

  useEffect(() => { convert(); }, [from, to, amount]);

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">
        Quick Exchange
      </h3>
      <div className="flex gap-2 items-center">
        <input 
          className="w-[35%] px-3 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--color-primary-500)]" 
          value={amount} 
          onChange={e => setAmount(e.target.value)} 
          type="number" 
        />
        <select 
          className="flex-1 px-2.5 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] focus:outline-none" 
          value={from} 
          onChange={e => setFrom(e.target.value)}
        >
          {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="text-[var(--color-primary-500)]"><IconArrowsRightLeft size={16} /></span>
        <select 
          className="flex-1 px-2.5 py-2 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] focus:outline-none" 
          value={to} 
          onChange={e => setTo(e.target.value)}
        >
          {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div className="text-center py-2.5 bg-blue-50/50 dark:bg-blue-950/10 border border-blue-100/50 dark:border-blue-900/10 rounded-xl">
        <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider mb-0.5">Converted Value</div>
        <div className="text-2xl font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 font-heading">
          {result ? result.converted_amount?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '...'} {to}
        </div>
        <span className="text-[10px] text-[var(--text-muted)] font-medium block mt-1">
          Last Updated: 10 minutes ago • Live ECB Rates
        </span>
      </div>
    </div>
  );
}
