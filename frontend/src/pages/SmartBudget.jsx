import {
  IconUsers,
  IconReceipt,
  IconArrowsRightLeft,
  IconScan,
  IconArrowRight,
  IconCash,
  IconAlertCircle,
  IconUser,
  IconWallet,
} from '@tabler/icons-react';

export default function SmartBudget() {
  const splits = [
    { from: 'Alice', to: 'Bob', amount: 45.50 },
    { from: 'Charlie', to: 'Bob', amount: 12.00 }
  ];

  return (
    <div className="flex flex-col gap-6 pb-12">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconUsers className="text-[var(--color-primary-600)]" size={32} /> Smart Group Budget
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Split bills, scan receipts, and balance expenses with travelers.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start max-w-5xl">
        
        {/* Settlement Suggestions */}
        <div className="glass-card p-6 flex flex-col gap-5 bg-[var(--bg-card)]">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)] font-heading mb-1 flex items-center gap-2">
              <IconArrowsRightLeft size={20} className="text-blue-500" /> Settle-Up Suggestions
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-medium">Optimized transactions to balance the group ledger.</p>
          </div>
          
          <div className="flex flex-col gap-3">
            {splits.map((s, idx) => (
              <div key={idx} className="flex justify-between items-center p-4 bg-[var(--bg-app)] border border-[var(--border-color)] rounded-xl">
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-full bg-blue-100 dark:bg-blue-950 text-[var(--color-primary-600)] dark:text-blue-400 flex items-center justify-center font-bold text-xs shadow-sm">
                    {s.from[0]}
                  </div>
                  <span className="text-[var(--text-muted)]"><IconArrowRight size={16} /></span>
                  <div className="w-9 h-9 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-xs shadow-sm">
                    {s.to[0]}
                  </div>
                  <div className="text-xs font-semibold text-[var(--text-secondary)] pl-1">
                    {s.from} pays {s.to}
                  </div>
                </div>
                <div className="text-base font-black text-[var(--text-primary)] font-heading">${s.amount.toFixed(2)}</div>
              </div>
            ))}
          </div>

          <button className="btn btn-primary w-full py-3.5 mt-2 text-sm font-semibold shadow-md shadow-blue-500/10 cursor-pointer">
            Settle All Balances
          </button>
        </div>

        {/* Auto Categorization OCR */}
        <div className="glass-card p-6 flex flex-col gap-6 bg-[var(--bg-card)]">
          <div>
            <h2 className="text-lg font-bold text-[var(--text-primary)] font-heading mb-1 flex items-center gap-2">
              <IconReceipt size={20} className="text-emerald-500" /> Add Splitted Expense
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-medium">Scan receipts with OCR or type entries manually.</p>
          </div>

          {/* OCR Box */}
          <div className="border-2 border-dashed border-[var(--color-primary-500)]/30 rounded-xl p-8 text-center bg-blue-50/5 dark:bg-blue-950/5 hover:bg-blue-50/10 dark:hover:bg-blue-950/10 transition-colors cursor-pointer group flex flex-col items-center justify-center gap-2">
            <span className="text-4xl text-[var(--color-primary-500)] group-hover:scale-110 transition-transform"><IconScan size={36} /></span>
            <div className="text-xs font-bold text-[var(--color-primary-600)] dark:text-blue-400">Scan Bill Receipt</div>
            <p className="text-[10px] text-[var(--text-muted)] max-w-[180px] leading-relaxed">AI will automatically analyze photo, extract totals, and categorize merchant.</p>
          </div>
          
          <div className="flex flex-col gap-4">
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Amount</label>
              <input 
                type="text" 
                placeholder="$ 0.00" 
                className="w-full px-3.5 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[var(--color-primary-500)]" 
              />
            </div>
            <div>
              <label className="block mb-1 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Split Type</label>
              <select className="w-full px-3 py-2.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm focus:outline-none cursor-pointer">
                <option>Split Equally</option>
                <option>Exact Amounts</option>
                <option>Percentage Split</option>
              </select>
            </div>
            <button className="btn btn-primary w-full py-3.5 text-sm font-semibold shadow-md shadow-blue-500/10 cursor-pointer">
              Add Expense
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
