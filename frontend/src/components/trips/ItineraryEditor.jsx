import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ActivityCard from './ActivityCard';
import {
  IconPlus, IconRefresh, IconSparkles, IconSun, IconMoon, IconCalendar, IconCheck, IconWallet
} from '@tabler/icons-react';
import { formatTripDate } from '../../utils/formatters';


export default function ItineraryEditor({ trip, onLockToggle, onDeleteActivity, onRegenerateDay, onAddActivity }) {
  const [activeDayIdx, setActiveDayIdx] = useState(0);
  const [showAddModal, setShowAddModal] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [customAct, setCustomAct] = useState({
    title: '', description: '', time_slot: 'morning', start_time: '09:00', end_time: '10:30',
    place_name: '', ticket_price: '0'
  });

  const days = trip?.itinerary_days || [];
  const currentDay = days[activeDayIdx] || null;

  const handleRegenerate = async () => {
    if (!currentDay) return;
    setRegenerating(true);
    try {
      await onRegenerateDay(currentDay.day_number);
    } catch (_) {}
    setRegenerating(false);
  };


  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (!currentDay || !customAct.title) return;
    onAddActivity(currentDay.id, {
      ...customAct,
      day_id: currentDay.id,
      ticket_price: parseFloat(customAct.ticket_price) || 0
    });
    setShowAddModal(false);
    setCustomAct({ title: '', description: '', time_slot: 'morning', start_time: '09:00', end_time: '10:30', place_name: '', ticket_price: '0' });
  };

  if (!days.length) {
    return (
      <div className="p-8 text-center bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-200 dark:border-gray-700">
        <IconCalendar size={40} className="mx-auto text-gray-400 mb-2" />
        <h3 className="text-base font-bold text-gray-700 dark:text-gray-200">No Itinerary Days Found</h3>
        <p className="text-xs text-gray-500 mt-1">Generate AI Itinerary to populate daily activities.</p>
      </div>
    );
  }

  // Group activities by flexible time slots
  const activities = currentDay?.activities || [];

  return (
    <div className="space-y-6">
      {/* Day Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 custom-scrollbar">
        {days.map((day, idx) => (
          <button
            key={day.id || idx}
            onClick={() => setActiveDayIdx(idx)}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 ${
              activeDayIdx === idx
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-50'
            }`}
          >
            <span>Day {day.day_number}</span>
            <span className="opacity-80 font-normal">({formatTripDate(day.date, 'short')})</span>
          </button>
        ))}
      </div>

      {/* Day Header Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base font-extrabold text-gray-900 dark:text-white font-heading">
              {currentDay?.title || `Day ${currentDay?.day_number} Activities`}
            </h3>
            {currentDay?.base_city && (
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                🏙️ Base: {currentDay.base_city}
              </span>
            )}
            {currentDay?.overnight_stay && (
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-purple-50 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                🏨 Overnight: {currentDay.overnight_stay}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {currentDay?.theme_note || 'Flexible daily schedule'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {trip?.id && (
            <Link
              to={`/expenses/${trip.id}`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors shadow-sm"
            >
              <IconWallet size={16} /> Expenses
            </Link>
          )}

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 hover:bg-gray-100 text-gray-700 dark:text-gray-200 transition-colors shadow-sm"
          >
            <IconPlus size={16} /> Add Activity
          </button>

          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white transition-colors shadow-sm disabled:opacity-50"
          >
            <IconSparkles size={16} className={regenerating ? 'animate-spin' : ''} />
            {regenerating ? 'Regenerating...' : 'Regenerate Day'}
          </button>

        </div>

      </div>

      {/* Activity List */}
      <div className="space-y-3">
        {activities.length === 0 ? (
          <div className="p-8 text-center bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
            <p className="text-xs text-gray-500">No activities scheduled for this day yet.</p>
          </div>
        ) : (
          activities.map((act) => (
            <ActivityCard
              key={act.id}
              activity={act}
              onLockToggle={onLockToggle}
              onDelete={onDeleteActivity}
            />
          ))
        )}
      </div>

      {/* Add Custom Activity Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-extrabold text-gray-900 dark:text-white">Add Custom Activity</h3>

            <form onSubmit={handleAddSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={customAct.title}
                  onChange={(e) => setCustomAct({ ...customAct, title: e.target.value })}
                  placeholder="e.g. Fushimi Inari Taisha Visit"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={customAct.start_time}
                    onChange={(e) => setCustomAct({ ...customAct, start_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">End Time</label>
                  <input
                    type="time"
                    value={customAct.end_time}
                    onChange={(e) => setCustomAct({ ...customAct, end_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Location / Place Name</label>
                <input
                  type="text"
                  value={customAct.place_name}
                  onChange={(e) => setCustomAct({ ...customAct, place_name: e.target.value })}
                  placeholder="e.g. Fushimi Inari Shrine"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={customAct.description}
                  onChange={(e) => setCustomAct({ ...customAct, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 text-white"
                >
                  Add Activity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
