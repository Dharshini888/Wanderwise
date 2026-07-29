import React, { useState, useEffect } from 'react';
import { IconX, IconSparkles, IconUpload, IconCheck, IconAlertTriangle } from '@tabler/icons-react';
import { uploadReceiptOCR } from '../../api/expenses';

const CATEGORIES = [
  'Accommodation', 'Food', 'Transport', 'Shopping',
  'Activities', 'Healthcare', 'Insurance', 'Emergency', 'Misc'
];

const PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking'];

export default function AddExpenseModal({ isOpen, onClose, onSubmit, initialData = null, defaultCurrency = 'USD' }) {
  const [scanning, setScanning] = useState(false);
  const [ocrData, setOcrData] = useState(null);

  const getLocalDateStr = (d = new Date()) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [form, setForm] = useState({
    title: '',
    amount: '',
    currency: defaultCurrency,
    category: 'Food',
    payment_method: 'Cash',
    expense_date: getLocalDateStr(),
    location_name: '',
    notes: '',
    expense_source: 'MANUAL',
    receipt_metadata: null
  });

  useEffect(() => {
    if (initialData) {
      setForm({
        id: initialData.id,
        title: initialData.title || '',
        amount: initialData.amount || '',
        currency: initialData.currency || defaultCurrency,
        category: initialData.category || 'Food',
        payment_method: initialData.payment_method || 'Cash',
        expense_date: String(initialData.expense_date || getLocalDateStr()),
        location_name: initialData.location_name || '',
        notes: initialData.notes || '',
        expense_source: initialData.expense_source || 'MANUAL',
        receipt_metadata: initialData.receipt_metadata || null
      });
    } else {
      setForm({
        title: '',
        amount: '',
        currency: defaultCurrency,
        category: 'Food',
        payment_method: 'Cash',
        expense_date: getLocalDateStr(),
        location_name: '',
        notes: '',
        expense_source: 'MANUAL',
        receipt_metadata: null
      });
    }
  }, [initialData, isOpen, defaultCurrency]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setScanning(true);
    try {
      const res = await uploadReceiptOCR(file);
      if (res) {
        setOcrData(res);
        setForm((prev) => ({
          ...prev,
          title: res.merchant || prev.title,
          amount: res.amount ? String(res.amount) : prev.amount,
          category: res.category || prev.category,
          currency: res.currency || prev.currency,
          expense_source: 'OCR',
          receipt_metadata: {
            filename: file.name,
            ocr_status: 'Completed',
            ocr_confidence: res.confidence || 0.95
          }
        }));
      }
    } catch (_) {}
    setScanning(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title || !form.amount) return;
    onSubmit({
      ...form,
      amount: parseFloat(form.amount)
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-gray-200 dark:border-gray-700 my-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-700 pb-3">
          <h3 className="text-base font-extrabold text-gray-900 dark:text-white flex items-center gap-2">
            <IconSparkles className="text-blue-600" size={18} />
            {initialData ? 'Edit Expense Item' : 'Add New Expense'}
          </h3>
          <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
            <IconX size={18} />
          </button>
        </div>

        {/* OCR Scan Receipt Bar */}
        <div className="p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/30 dark:to-indigo-900/30 rounded-2xl border border-purple-200 dark:border-purple-800/50 flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs font-bold text-purple-900 dark:text-purple-200 flex items-center gap-1">
              <IconSparkles size={14} /> Scan Receipt (AI OCR)
            </span>
            <span className="text-[10px] text-purple-600 dark:text-purple-300 block">
              Auto-fill merchant, date & amount
            </span>
          </div>

          <label className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-extrabold cursor-pointer shadow-sm flex items-center gap-1">
            <IconUpload size={14} /> {scanning ? 'Scanning...' : 'Upload Receipt'}
            <input type="file" accept="image/*,.pdf" onChange={handleFileUpload} className="hidden" />
          </label>
        </div>

        {/* OCR Result Alert */}
        {ocrData && (
          <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 text-xs rounded-xl border border-emerald-200 dark:border-emerald-800 flex items-center gap-2">
            <IconCheck size={16} className="text-emerald-600 shrink-0" />
            <span>
              OCR Extracted <strong>{ocrData.merchant}</strong> ({Math.round(ocrData.confidence * 100)}% confidence). Please review fields.
            </span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Title / Merchant *</label>
            <input
              type="text"
              name="title"
              required
              value={form.title}
              onChange={handleChange}
              placeholder="e.g. Starbucks Shibuya, Uber Ride, Hotel Stay"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Amount *</label>
              <input
                type="number"
                step="0.01"
                name="amount"
                required
                value={form.amount}
                onChange={handleChange}
                placeholder="420.00"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Currency</label>
              <input
                type="text"
                name="currency"
                value={form.currency}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold uppercase"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Category</label>
              <select
                name="category"
                value={form.category}
                onChange={handleChange}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Payment Method</label>
              <select
                name="payment_method"
                value={form.payment_method}
                onChange={handleChange}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
              >
                {PAYMENT_METHODS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Expense Date</label>
              <input
                type="date"
                name="expense_date"
                value={form.expense_date}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Location Name</label>
              <input
                type="text"
                name="location_name"
                value={form.location_name}
                onChange={handleChange}
                placeholder="e.g. Tokyo Station"
                className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Notes (Optional)</label>
            <input
              type="text"
              name="notes"
              value={form.notes}
              onChange={handleChange}
              placeholder="e.g. Shared dinner with travel buddy"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-xs font-semibold"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-extrabold shadow-md transition-all mt-2"
          >
            {initialData ? 'Save Expense Changes' : 'Record Expense'}
          </button>
        </form>
      </div>
    </div>
  );
}
