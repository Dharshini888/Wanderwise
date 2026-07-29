import React from 'react';

export default function DestinationStep({ form, onChange }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Destination City / Region *</label>
        <input
          type="text"
          name="destination"
          required
          value={form.destination}
          onChange={onChange}
          placeholder="e.g. Tokyo, Paris, Bali, Varkala"
          className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-semibold"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Country</label>
          <input
            type="text"
            name="country"
            value={form.country}
            onChange={onChange}
            placeholder="e.g. Japan"
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Origin City</label>
          <input
            type="text"
            name="origin_city"
            value={form.origin_city}
            onChange={onChange}
            placeholder="e.g. London"
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Origin Airport Code</label>
          <input
            type="text"
            name="origin_airport"
            value={form.origin_airport}
            onChange={onChange}
            placeholder="e.g. LHR, DEL"
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Destination Airport</label>
          <input
            type="text"
            name="destination_airport"
            value={form.destination_airport}
            onChange={onChange}
            placeholder="e.g. HND, CDG"
            className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">Visa Requirement</label>
        <select
          name="visa_status"
          value={form.visa_status}
          onChange={onChange}
          className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm"
        >
          <option value="No Visa Needed">No Visa Needed / Visa Free</option>
          <option value="Already Have Visa">Already Have Visa</option>
          <option value="Visa on Arrival">Visa on Arrival / eVisa</option>
          <option value="Need Help">Need Visa Assistance</option>
        </select>
      </div>
    </div>
  );
}
