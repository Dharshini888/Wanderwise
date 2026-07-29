import React from 'react';

export default function DailyRoutineStep({ form, onChange }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Wake Up Time</label>
          <input
            type="time"
            name="wake_up_time"
            value={form.wake_up_time || '08:00'}
            onChange={onChange}
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Sleep Time</label>
          <input
            type="time"
            name="sleep_time"
            value={form.sleep_time || '22:30'}
            onChange={onChange}
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Lunch Preferred Time</label>
          <input
            type="time"
            name="lunch_time"
            value={form.lunch_time || '13:00'}
            onChange={onChange}
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Dinner Preferred Time</label>
          <input
            type="time"
            name="dinner_time"
            value={form.dinner_time || '19:30'}
            onChange={onChange}
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-bold"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Preferred Viewpoint Spot</label>
        <select
          name="preferred_sunset_spot"
          value={form.preferred_sunset_spot || 'sunset'}
          onChange={onChange}
          className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
        >
          <option value="sunset">Clifftop Sunset / Golden Hour Viewpoint</option>
          <option value="sunrise">Early Morning Sunrise Spot</option>
          <option value="both">Both Sunrise & Sunset Viewpoints</option>
          <option value="none">No Preference</option>
        </select>
      </div>
    </div>
  );
}
