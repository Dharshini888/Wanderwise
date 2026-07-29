import React from 'react';

const INTEREST_TAGS = [
  'History', 'Museums', 'Adventure', 'Shopping', 'Photography', 'Nightlife',
  'Street Food', 'Luxury Dining', 'Nature', 'Wildlife', 'Hiking', 'Temples',
  'Architecture', 'Local Culture', 'Beaches', 'Snow', 'Mountains', 'Cafes',
  'Hidden Gems', 'Festivals', 'Markets', 'Road Trips', 'Boating', 'Water Sports',
  'Camping', 'Wellness', 'Ayurveda', 'Spa', 'Kids Activities', 'Theme Parks',
  'Art', 'Music', 'Technology', 'Anime', 'Gaming', 'Sports'
];

export default function InterestsStep({ form, onToggleInterest }) {
  const selectedList = form.interests ? form.interests.split(',').map(s => s.trim()) : [];

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <label className="text-xs font-bold text-gray-700 dark:text-gray-300">Select Interests & Activity Tags</label>
        <span className="text-[11px] font-extrabold text-blue-600 dark:text-blue-400">{selectedList.length} Selected</span>
      </div>

      <div className="grid grid-cols-3 gap-1.5 max-h-64 overflow-y-auto pr-1">
        {INTEREST_TAGS.map((tag) => {
          const isSelected = selectedList.includes(tag);
          return (
            <button
              key={tag}
              type="button"
              onClick={() => onToggleInterest(tag)}
              className={`py-2 px-2 rounded-xl text-xs font-semibold text-left border transition-all ${
                isSelected
                  ? 'border-blue-600 bg-blue-600 text-white shadow-sm font-bold'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50'
              }`}
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}
