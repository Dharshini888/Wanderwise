import React from 'react';

export default function DateStep({ form, onChange }) {
  const calculateDays = () => {
    if (!form.start_date || !form.end_date) return 0;
    const s = new Date(form.start_date);
    const e = new Date(form.end_date);
    const diff = Math.ceil((e - s) / (1000 * 60 * 60 * 24)) + 1;
    return diff > 0 ? diff : 0;
  };

  const totalDays = calculateDays();

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Start Date *</label>
          <input
            type="date"
            name="start_date"
            required
            value={form.start_date}
            onChange={onChange}
            className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">End Date *</label>
          <input
            type="date"
            name="end_date"
            required
            value={form.end_date}
            onChange={onChange}
            className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
      </div>

      <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-2xl flex justify-between items-center border border-blue-100 dark:border-blue-800">
        <span className="text-xs font-bold text-blue-900 dark:text-blue-200">Total Trip Duration</span>
        <span className="text-sm font-extrabold text-blue-600 dark:text-blue-400">{totalDays} Day{totalDays !== 1 ? 's' : ''}</span>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Flexible Travel Dates</label>
        <select
          name="flexible_dates"
          value={form.flexible_dates}
          onChange={onChange}
          className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
        >
          <option value="Fixed Dates">Exact Dates (Fixed)</option>
          <option value="±1 day">Flexible ±1 day</option>
          <option value="±2 days">Flexible ±2 days</option>
          <option value="Weekend only">Weekend Trip Only</option>
          <option value="Weekdays only">Weekday Trip Only</option>
        </select>
      </div>
    </div>
  );
}
