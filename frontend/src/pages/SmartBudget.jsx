import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  IconUsers,
  IconReceipt,
  IconArrowsRightLeft,
  IconPlus,
  IconTrash,
  IconArrowRight,
  IconCheck,
  IconWallet,
  IconCoin,
  IconSparkles,
  IconRefresh
} from '@tabler/icons-react';

const INITIAL_MEMBERS = ['Alice', 'Bob', 'Charlie'];

const INITIAL_EXPENSES = [
  { id: 1, title: 'Group Dinner', paidBy: 'Bob', amount: 90.0, sharedBy: ['Alice', 'Bob', 'Charlie'] },
  { id: 2, title: 'Taxi to Hotel', paidBy: 'Alice', amount: 24.0, sharedBy: ['Alice', 'Bob', 'Charlie'] },
  { id: 3, title: 'Museum Tickets', paidBy: 'Charlie', amount: 45.0, sharedBy: ['Alice', 'Charlie'] }
];

export default function SmartBudget() {
  const [currency, setCurrency] = useState('USD');
  const [members, setMembers] = useState(INITIAL_MEMBERS);
  const [newMemberName, setNewMemberName] = useState('');
  const [expenses, setExpenses] = useState(INITIAL_EXPENSES);

  // Form state
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [paidBy, setPaidBy] = useState(INITIAL_MEMBERS[0]);
  const [selectedShare, setSelectedShare] = useState([...INITIAL_MEMBERS]);
  const [settledNotice, setSettledNotice] = useState(false);

  // Add a new member
  const handleAddMember = (e) => {
    e.preventDefault();
    const name = newMemberName.trim();
    if (name && !members.includes(name)) {
      setMembers([...members, name]);
      setSelectedShare([...selectedShare, name]);
      setNewMemberName('');
    }
  };

  // Remove a member
  const handleRemoveMember = (name) => {
    if (members.length <= 2) return;
    setMembers(members.filter((m) => m !== name));
    setSelectedShare(selectedShare.filter((m) => m !== name));
    setExpenses(expenses.filter((exp) => exp.paidBy !== name).map((exp) => ({
      ...exp,
      sharedBy: exp.sharedBy.filter((m) => m !== name)
    })));
  };

  // Add an expense
  const handleAddExpense = (e) => {
    e.preventDefault();
    const parsedAmt = parseFloat(amount);
    if (!title.trim() || isNaN(parsedAmt) || parsedAmt <= 0 || selectedShare.length === 0) return;

    const newExp = {
      id: Date.now(),
      title: title.trim(),
      paidBy: paidBy || members[0],
      amount: parsedAmt,
      sharedBy: [...selectedShare]
    };
    setExpenses([newExp, ...expenses]);
    setTitle('');
    setAmount('');
    setSettledNotice(false);
  };

  // Delete an expense
  const handleDeleteExpense = (id) => {
    setExpenses(expenses.filter((exp) => exp.id !== id));
  };

  // Toggle member in share list
  const toggleShareMember = (name) => {
    if (selectedShare.includes(name)) {
      if (selectedShare.length > 1) {
        setSelectedShare(selectedShare.filter((m) => m !== name));
      }
    } else {
      setSelectedShare([...selectedShare, name]);
    }
  };

  // Compute Net Balances
  const balances = useMemo(() => {
    const bal = {};
    members.forEach((m) => { bal[m] = 0; });

    expenses.forEach((exp) => {
      const shareCount = exp.sharedBy.length;
      if (shareCount === 0) return;
      const splitAmount = exp.amount / shareCount;

      // Payer gets credit
      bal[exp.paidBy] = (bal[exp.paidBy] || 0) + exp.amount;

      // Each consumer gets debit
      exp.sharedBy.forEach((person) => {
        bal[person] = (bal[person] || 0) - splitAmount;
      });
    });

    return bal;
  }, [members, expenses]);

  // Compute Simplified Settle-Up Transactions (Greedy Debt Settlement)
  const settlements = useMemo(() => {
    const debtors = [];
    const creditors = [];

    Object.entries(balances).forEach(([name, amount]) => {
      const rounded = Math.round(amount * 100) / 100;
      if (rounded < -0.01) {
        debtors.push({ name, amount: -rounded });
      } else if (rounded > 0.01) {
        creditors.push({ name, amount: rounded });
      }
    });

    const result = [];
    let i = 0;
    let j = 0;

    while (i < debtors.length && j < creditors.length) {
      const debit = debtors[i].amount;
      const credit = creditors[j].amount;
      const settled = Math.min(debit, credit);

      if (settled > 0.01) {
        result.push({
          from: debtors[i].name,
          to: creditors[j].name,
          amount: settled
        });
      }

      debtors[i].amount -= settled;
      creditors[j].amount -= settled;

      if (debtors[i].amount <= 0.01) i++;
      if (creditors[j].amount <= 0.01) j++;
    }

    return result;
  }, [balances]);

  const totalExpenseSum = useMemo(() => {
    return expenses.reduce((sum, e) => sum + e.amount, 0);
  }, [expenses]);

  const handleSettleAll = () => {
    setExpenses([]);
    setSettledNotice(true);
    setTimeout(() => setSettledNotice(false), 4000);
  };

  return (
    <div className="flex flex-col gap-6 pb-16 max-w-6xl mx-auto px-4">
      {/* Top Navigation Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-transparent border border-blue-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-400">
            Smart Group Travel Tools
          </span>
          <h2 className="text-base font-black text-[var(--text-primary)]">
            Splitting costs with travel companions?
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Calculate fair shares, track who paid what, and generate minimal debt-settlement transactions.
          </p>
        </div>
        <Link
          to="/budget"
          className="btn btn-primary text-xs font-bold py-2.5 px-4 shrink-0 flex items-center gap-2 cursor-pointer"
        >
          <IconWallet size={16} />
          <span>Trip Expense Tracker</span>
        </Link>
      </div>

      {/* Main Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[var(--text-primary)] tracking-tight font-heading flex items-center gap-2">
            <IconUsers className="text-blue-500" size={28} />
            <span>Smart Group Budget & Split Ledger</span>
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Total Group Spending: <strong className="text-[var(--text-primary)] font-bold">{currency} {totalExpenseSum.toFixed(2)}</strong> across {expenses.length} expense{expenses.length !== 1 ? 's' : ''}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-[var(--text-muted)]">Currency:</label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-xs font-bold text-[var(--text-primary)] cursor-pointer"
          >
            {['USD', 'EUR', 'GBP', 'INR', 'SGD', 'JPY', 'CAD', 'AUD'].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Group Members Row */}
      <div className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-[var(--text-muted)]">
            Travel Companions ({members.length})
          </h3>
          <span className="text-[11px] text-[var(--text-muted)]">Minimum 2 travelers</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {members.map((m) => (
            <div
              key={m}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs font-bold text-[var(--text-primary)]"
            >
              <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px]">
                {m[0].toUpperCase()}
              </div>
              <span>{m}</span>
              {members.length > 2 && (
                <button
                  onClick={() => handleRemoveMember(m)}
                  className="text-gray-400 hover:text-red-500 transition-colors ml-1"
                  title={`Remove ${m}`}
                >
                  ×
                </button>
              )}
            </div>
          ))}

          <form onSubmit={handleAddMember} className="flex items-center gap-1.5">
            <input
              type="text"
              placeholder="Add companion..."
              value={newMemberName}
              onChange={(e) => setNewMemberName(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-xs text-[var(--text-primary)] placeholder-gray-400 focus:outline-none focus:border-blue-500 w-36"
            />
            <button
              type="submit"
              disabled={!newMemberName.trim()}
              className="px-2.5 py-1.5 rounded-xl bg-blue-600 disabled:opacity-50 text-white text-xs font-bold hover:bg-blue-700 transition-colors cursor-pointer"
            >
              <IconPlus size={14} />
            </button>
          </form>
        </div>
      </div>

      {/* Two Column Layout: Add Expense & Settle-Up Suggestions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Left: Add Expense Form */}
        <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm space-y-4">
          <div>
            <h2 className="text-base font-black text-[var(--text-primary)] font-heading flex items-center gap-2">
              <IconReceipt size={20} className="text-emerald-500" />
              <span>Log Shared Expense</span>
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-medium">Record a bill and select who participated.</p>
          </div>

          <form onSubmit={handleAddExpense} className="space-y-4">
            <div>
              <label className="block mb-1 text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                Expense Description
              </label>
              <input
                type="text"
                placeholder="e.g. Marina Bay Sands Lunch, Airport Taxi..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-semibold focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block mb-1 text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  Amount ({currency})
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-bold focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block mb-1 text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                  Paid By
                </label>
                <select
                  value={paidBy}
                  onChange={(e) => setPaidBy(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs font-bold focus:outline-none cursor-pointer"
                >
                  {members.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block mb-1.5 text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
                Split Equally Among:
              </label>
              <div className="flex flex-wrap gap-2">
                {members.map((m) => {
                  const isSelected = selectedShare.includes(m);
                  return (
                    <button
                      type="button"
                      key={m}
                      onClick={() => toggleShareMember(m)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 ${
                        isSelected
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-[var(--border-color)] hover:border-blue-500/50'
                      }`}
                    >
                      {isSelected && <IconCheck size={12} />}
                      <span>{m}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              type="submit"
              disabled={!title.trim() || !amount}
              className="btn btn-primary w-full py-3 text-xs font-bold shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
            >
              Add Shared Expense
            </button>
          </form>
        </div>

        {/* Right: Settle-Up Suggestions */}
        <div className="space-y-4">
          <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-black text-[var(--text-primary)] font-heading flex items-center gap-2">
                  <IconArrowsRightLeft size={20} className="text-blue-500" />
                  <span>Optimal Settle-Up Plan</span>
                </h2>
                <p className="text-xs text-[var(--text-muted)] font-medium">
                  Minimal transactions required to balance the ledger.
                </p>
              </div>

              {settlements.length > 0 && (
                <button
                  onClick={handleSettleAll}
                  className="px-3 py-1.5 rounded-xl border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-bold hover:bg-emerald-500/10 transition-colors cursor-pointer"
                >
                  Settle All
                </button>
              )}
            </div>

            {settledNotice && (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 text-xs font-bold flex items-center gap-2">
                <IconCheck size={16} /> All balances settled!
              </div>
            )}

            {settlements.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto">
                  <IconCheck size={20} />
                </div>
                <p className="text-xs font-bold text-[var(--text-primary)]">All Balances are Even!</p>
                <p className="text-[11px] text-[var(--text-muted)]">No outstanding debts among companions.</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {settlements.map((s, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center p-3.5 bg-[var(--bg-app)] border border-[var(--border-color)] rounded-2xl"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-xs">
                        {s.from[0]}
                      </div>
                      <IconArrowRight size={14} className="text-[var(--text-muted)]" />
                      <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-xs">
                        {s.to[0]}
                      </div>
                      <div className="text-xs font-semibold text-[var(--text-primary)]">
                        <strong>{s.from}</strong> pays <strong>{s.to}</strong>
                      </div>
                    </div>
                    <div className="text-xs font-black text-blue-500 font-mono">
                      {currency} {s.amount.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Member Net Balances */}
          <div className="glass-card p-4 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2.5">
            <h4 className="text-[11px] font-extrabold uppercase tracking-wider text-[var(--text-muted)]">
              Net Balance Per Person
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(balances).map(([name, net]) => {
                const isPos = net > 0.01;
                const isNeg = net < -0.01;
                return (
                  <div key={name} className="p-2.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)]">
                    <p className="text-[11px] font-bold text-[var(--text-primary)] truncate">{name}</p>
                    <p className={`text-xs font-extrabold font-mono mt-0.5 ${
                      isPos ? 'text-emerald-500' : isNeg ? 'text-rose-500' : 'text-gray-400'
                    }`}>
                      {isPos ? '+' : ''}{currency} {net.toFixed(2)}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Expense History Table */}
      <div className="glass-card p-6 rounded-3xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-sm space-y-4">
        <h3 className="text-sm font-black text-[var(--text-primary)] font-heading">
          Logged Shared Expenses ({expenses.length})
        </h3>

        {expenses.length === 0 ? (
          <p className="text-xs text-[var(--text-muted)] py-4 text-center">No expenses logged yet. Add one above.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[var(--border-color)] text-[var(--text-muted)]">
                  <th className="pb-2 font-bold uppercase text-[10px]">Description</th>
                  <th className="pb-2 font-bold uppercase text-[10px]">Paid By</th>
                  <th className="pb-2 font-bold uppercase text-[10px]">Split Among</th>
                  <th className="pb-2 font-bold uppercase text-[10px] text-right">Amount</th>
                  <th className="pb-2 font-bold uppercase text-[10px] text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {expenses.map((exp) => (
                  <tr key={exp.id} className="hover:bg-[var(--bg-app)] transition-colors">
                    <td className="py-2.5 font-bold text-[var(--text-primary)]">{exp.title}</td>
                    <td className="py-2.5 text-[var(--text-secondary)]">{exp.paidBy}</td>
                    <td className="py-2.5 text-[var(--text-muted)]">{exp.sharedBy.join(', ')}</td>
                    <td className="py-2.5 text-right font-black font-mono text-[var(--text-primary)]">
                      {currency} {exp.amount.toFixed(2)}
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        onClick={() => handleDeleteExpense(exp.id)}
                        className="text-gray-400 hover:text-rose-500 transition-colors p-1"
                        title="Delete expense"
                      >
                        <IconTrash size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
