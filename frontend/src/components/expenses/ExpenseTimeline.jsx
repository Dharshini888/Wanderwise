import React from 'react';
import ExpenseCard from './ExpenseCard';
import { IconReceipt } from '@tabler/icons-react';

export default function ExpenseTimeline({ expenses = [], onEdit, onDelete }) {
  if (!expenses || expenses.length === 0) {
    return (
      <div className="p-10 text-center bg-white dark:bg-gray-800 rounded-3xl border border-dashed border-gray-300 dark:border-gray-700/80 shadow-sm space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
          <IconReceipt size={24} />
        </div>
        <h4 className="text-base font-extrabold text-gray-900 dark:text-white font-heading">No expenses yet</h4>
        <p className="text-xs text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
          Add your first expense or scan a receipt with AI OCR to automatically track your trip spending.
        </p>
      </div>
    );
  }


  // Group expenses by date
  const grouped = {};
  expenses.forEach((e) => {
    const dStr = String(e.expense_date);
    if (!grouped[dStr]) grouped[dStr] = [];
    grouped[dStr].push(e);
  });

  const datesSorted = Object.keys(grouped).sort().reverse();

  return (
    <div className="space-y-6">
      {datesSorted.map((dStr) => (
        <div key={dStr} className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-blue-600 text-white shadow-sm">
              {dStr}
            </span>
            <div className="h-px bg-gray-200 dark:bg-gray-700 flex-1" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {grouped[dStr].map((expense) => (
              <ExpenseCard
                key={expense.id}
                expense={expense}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
