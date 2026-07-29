import React from 'react';

const ACCOM_TYPES = [
  { id: 'hotel', title: 'Hotel', desc: 'Comfortable standard rooms & services' },
  { id: 'hostel', title: 'Hostel', desc: 'Social dorms & budget friendly' },
  { id: 'resort', title: 'Resort', desc: 'All-inclusive relaxation & amenities' },
  { id: 'homestay', title: 'Homestay', desc: 'Authentic local hosts & home cooked meals' },
  { id: 'apartment', title: 'Apartment / Airbnb', desc: 'Kitchen & living space' },
  { id: 'villa', title: 'Luxury Villa', desc: 'Private pool & butler service' },
  { id: 'camping', title: 'Glamping / Camping', desc: 'Outdoors & starry nights' },
  { id: 'no_preference', title: 'No Preference', desc: 'AI chooses best option' },
];

export default function AccommodationStep({ form, onChange }) {
  return (
    <div className="space-y-3">
      <label className="block text-xs font-bold text-gray-700 dark:text-gray-300">Accommodation Style</label>
      <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
        {ACCOM_TYPES.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => onChange({ target: { name: 'accommodation_preference', value: a.id } })}
            className={`p-3 text-left rounded-xl border text-xs transition-all ${
              form.accommodation_preference === a.id
                ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-900 dark:text-indigo-100 font-bold shadow-sm'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
            }`}
          >
            <div className="font-bold">{a.title}</div>
            <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{a.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
