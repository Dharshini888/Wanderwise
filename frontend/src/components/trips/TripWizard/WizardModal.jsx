import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  IconX,
  IconSparkles,
  IconPlaneDeparture,
  IconMapPin,
  IconCalendar,
  IconUsers,
  IconCoin,
  IconCurrentLocation,
  IconLoader2,
  IconPlus,
  IconMinus,
  IconCheck,
} from '@tabler/icons-react';
import { fetchCurrencyRegistry, checkDuplicateTrip, searchLocations, reverseGeocodeLocation } from '../../../api/trips';
import { useAuth } from '../../../context/AuthContext';

const PREFERENCE_OPTIONS = [
  { id: 'Adventure', label: 'Adventure', emoji: '🏔️', desc: 'Trekking, outdoor sports & thrills' },
  { id: 'Culture and History', label: 'Culture & History', emoji: '🏛️', desc: 'Museums, heritage sites & temples' },
  { id: 'Nature', label: 'Nature', emoji: '🌿', desc: 'Parks, viewpoints & landscapes' },
  { id: 'Food', label: 'Food', emoji: '🍲', desc: 'Local cuisine, street food & dining' },
  { id: 'Shopping', label: 'Shopping', emoji: '🛍️', desc: 'Local bazaars, markets & craft hubs' },
  { id: 'Relaxation', label: 'Relaxation', emoji: '🧘', desc: 'Scenic walks, cafes & leisure' },
  { id: 'Family Activities', label: 'Family Activities', emoji: '👨‍👩‍👧', desc: 'Child-friendly spots & theme parks' },
];

const DEFAULT_CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar' },
  { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
];

export default function WizardModal({
  userId,
  isOpen = true,
  onClose,
  onSuccess,
  destination = '',
  initialDestination = '',
}) {
  const { user } = useAuth();

  const [form, setForm] = useState({
    origin_city: 'Coimbatore',
    destination: destination || initialDestination || '',
    country: '',
    start_date: '',
    end_date: '',
    adults: 1,
    children: 0,
    budget: '',
    currency: 'USD',
    interests: [],
  });

  const [currencyList, setCurrencyList] = useState(DEFAULT_CURRENCIES);
  const [submitting, setSubmitting] = useState(false);
  const [generationStage, setGenerationStage] = useState(0);

  // Autocomplete & GPS States
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);
  const [showOriginDropdown, setShowOriginDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsSuccess, setGpsSuccess] = useState(false);

  const originInputRef = useRef(null);
  const destInputRef = useRef(null);

  const GENERATION_STAGES = [
    { title: 'Personalizing Itinerary Plan', desc: 'Resolving travel style, group dynamics & pace preferences...' },
    { title: 'Curating Real Places & Heritage Sites', desc: 'Selecting verified attractions, UNESCO landmarks & viewpoints...' },
    { title: 'Matching Dining & Dietary Criteria', desc: 'Verifying authentic restaurants & local culinary traditions...' },
    { title: 'Calculating Routes & Door-to-Door Budget', desc: 'Estimating intercity transport, lodging & category allocations...' },
    { title: 'Finalizing & Saving Trip', desc: 'Persisting your complete day-by-day structured itinerary...' },
  ];

  // Sync initial destination if passed externally
  useEffect(() => {
    const targetDest = destination || initialDestination;
    if (targetDest && (!form.destination || form.destination !== targetDest)) {
      setForm((prev) => ({ ...prev, destination: targetDest }));
    }
  }, [destination, initialDestination]);

  // Initial load: currencies & user profile defaults
  useEffect(() => {
    if (isOpen) {
      fetchCurrencyRegistry()
        .then((res) => {
          if (Array.isArray(res.data) && res.data.length > 0) {
            setCurrencyList(res.data);
          }
        })
        .catch(() => {});

      if (user) {
        setForm((prev) => ({
          ...prev,
          currency: user.currency || prev.currency || 'USD',
          origin_city: user.city || user.origin_city || prev.origin_city || 'Coimbatore',
        }));
      }
    }
  }, [isOpen, user]);

  // Prevent background scrolling while modal is open
  useEffect(() => {
    if (!isOpen) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen]);

  // Stage animation while submitting
  useEffect(() => {
    let interval;
    if (submitting) {
      setGenerationStage(0);
      interval = setInterval(() => {
        setGenerationStage((prev) => (prev < GENERATION_STAGES.length - 1 ? prev + 1 : prev));
      }, 3000);
    } else {
      setGenerationStage(0);
    }
    return () => clearInterval(interval);
  }, [submitting]);

  // Autocomplete debounce for Starting Location
  useEffect(() => {
    const val = form.origin_city.trim();
    if (!val || val.length < 2) {
      setOriginSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      const results = await searchLocations(val);
      setOriginSuggestions(results);
    }, 250);
    return () => clearTimeout(timer);
  }, [form.origin_city]);

  // Autocomplete debounce for Destination
  useEffect(() => {
    const val = form.destination.trim();
    if (!val || val.length < 2) {
      setDestSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      const results = await searchLocations(val);
      setDestSuggestions(results);
    }, 250);
    return () => clearTimeout(timer);
  }, [form.destination]);

  if (!isOpen) return null;

  const todayStr = new Date().toISOString().split('T')[0];

  // Calculate Duration
  let durationDays = 0;
  let durationNights = 0;
  let isDateRangeValid = true;

  if (form.start_date && form.end_date) {
    const start = new Date(form.start_date);
    const end = new Date(form.end_date);
    if (end >= start) {
      const diffMs = end.getTime() - start.getTime();
      durationDays = Math.round(diffMs / (1000 * 60 * 60 * 24)) + 1;
      durationNights = Math.max(0, durationDays - 1);
    } else {
      isDateRangeValid = false;
    }
  }

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setGpsLoading(true);
    setGpsSuccess(false);

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const loc = await reverseGeocodeLocation(lat, lon);
          if (loc && loc.city && loc.city !== 'Current Location') {
            setForm((prev) => ({
              ...prev,
              origin_city: loc.city,
            }));
            setGpsSuccess(true);
          } else if (loc && loc.display_name) {
            setForm((prev) => ({
              ...prev,
              origin_city: loc.display_name.split(',')[0].trim(),
            }));
            setGpsSuccess(true);
          } else {
            setForm((prev) => ({ ...prev, origin_city: 'Current Location' }));
            setGpsSuccess(true);
          }
        } catch (_) {
          alert('Could not determine city name from GPS coordinates.');
        } finally {
          setGpsLoading(false);
          setTimeout(() => setGpsSuccess(false), 3000);
        }
      },
      (err) => {
        setGpsLoading(false);
        alert(err.code === 1 ? 'Location permission was denied. Please enter your city manually.' : 'Unable to acquire GPS location.');
      },
      { timeout: 8000 }
    );
  };

  const handleTogglePreference = (prefId) => {
    setForm((prev) => {
      const exists = prev.interests.includes(prefId);
      const nextInterests = exists
        ? prev.interests.filter((i) => i !== prefId)
        : [...prev.interests, prefId];
      return { ...prev, interests: nextInterests };
    });
  };

  const isFormValid =
    form.destination.trim().length >= 2 &&
    form.start_date &&
    form.end_date &&
    isDateRangeValid &&
    durationDays > 0;

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!isFormValid || submitting) return;

    setSubmitting(true);
    try {
      const interestsStr = form.interests.join(', ');
      const totalAdults = parseInt(form.adults || 1);
      const totalChildren = parseInt(form.children || 0);
      const totalGroup = Math.max(1, totalAdults + totalChildren);
      const isFamily = totalChildren > 0 || form.interests.includes('Family Activities');
      const travelStyle = isFamily ? 'family' : totalGroup > 1 ? 'friends' : 'solo';
      const parsedBudget = form.budget && parseFloat(form.budget) > 0 ? parseFloat(form.budget) : null;

      const tripPreferencesObj = {
        destination: form.destination.trim(),
        country: form.country || '',
        origin_city: form.origin_city.trim() || 'Coimbatore',
        start_date: form.start_date,
        end_date: form.end_date,
        travel_style: travelStyle,
        budget: parsedBudget,
        currency: form.currency || 'USD',
        budget_type: parsedBudget ? 'Mid-range' : 'Unrestricted',
        interests: interestsStr || 'General Exploration',
        accommodation_preference: 'hotel',
        transportation: 'Mixed Transport',
        activity_pace: 'balanced',
        travelers: {
          adults: totalAdults,
          children: totalChildren,
          total: totalGroup,
        },
        food: {
          preferences: 'No Preference',
        },
        daily_routine: {
          wake_up_time: '08:00',
          sleep_time: '22:30',
          lunch_time: '13:00',
          dinner_time: '19:30',
          preferred_viewpoint: 'sunset',
        },
      };

      const payload = {
        destination: form.destination.trim(),
        country: form.country || '',
        origin_city: form.origin_city.trim() || 'Coimbatore',
        start_date: form.start_date,
        end_date: form.end_date,
        user_id: Number(userId),
        budget: parsedBudget,
        currency: form.currency || 'USD',
        travel_style: travelStyle,
        group_size: totalGroup,
        interests: interestsStr,
        transportation: 'Mixed Transport',
        accommodation_preference: 'hotel',
        trip_preferences: tripPreferencesObj,
        force_create: true,
      };

      // Duplicate trip warning check
      try {
        const dupCheck = await checkDuplicateTrip(form.destination.trim(), form.start_date);
        if (dupCheck && dupCheck.has_duplicate) {
          const proceed = window.confirm(
            dupCheck.message || `You already have a trip scheduled for ${form.destination} around this date. Continue creating anyway?`
          );
          if (!proceed) {
            setSubmitting(false);
            return;
          }
        }
      } catch (_) {}

      await onSuccess(payload);
      onClose();
    } catch (err) {
      console.error('[WizardModal] Generation error:', err);
      const errDetail = err?.response?.data?.detail;
      const errMsg =
        typeof errDetail === 'object'
          ? errDetail.message || JSON.stringify(errDetail)
          : errDetail || err?.message || 'Failed to generate itinerary. Please try again.';
      alert(`Itinerary generation notice: ${errMsg}`);
    } finally {
      setSubmitting(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/65 backdrop-blur-md p-3 sm:p-6 overflow-hidden animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden relative">
        {/* Active Generation Loading Overlay */}
        {submitting && (
          <div className="absolute inset-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md z-50 flex flex-col items-center justify-center p-6 text-center space-y-5 animate-fadeIn">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <IconSparkles size={24} className="text-blue-600 animate-pulse" />
              </div>
            </div>
            <div className="space-y-1.5 max-w-sm">
              <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400">
                Stage {generationStage + 1} of {GENERATION_STAGES.length}
              </span>
              <h3 className="text-base font-extrabold text-gray-900 dark:text-white font-heading">
                {GENERATION_STAGES[generationStage]?.title || 'Planning Your Itinerary'}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {GENERATION_STAGES[generationStage]?.desc || 'Validating routes, verified places, and budget allocation...'}
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-1">
              {GENERATION_STAGES.map((_, sIdx) => (
                <div
                  key={sIdx}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    sIdx === generationStage
                      ? 'w-6 bg-blue-600'
                      : sIdx < generationStage
                      ? 'w-2 bg-emerald-500'
                      : 'w-2 bg-gray-300 dark:bg-gray-700'
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Modal Header */}
        <div className="p-5 sm:p-6 pb-4 shrink-0 border-b border-gray-100 dark:border-gray-700/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <IconSparkles size={20} />
            </div>
            <div>
              <h2 className="text-lg font-extrabold font-heading text-gray-900 dark:text-white leading-tight">
                Plan a New Trip
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Enter your trip essentials and let WanderWise AI curate your itinerary.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            <IconX size={20} />
          </button>
        </div>

        {/* Form Body - Scrollable Container */}
        <form onSubmit={handleSubmit} className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-6 custom-scrollbar">
          {/* 1. WHERE ARE YOU GOING? */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                1. Where are you going?
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {/* Starting Location */}
              <div className="relative">
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Starting Location
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3 text-gray-400 pointer-events-none">
                    <IconPlaneDeparture size={16} />
                  </div>
                  <input
                    ref={originInputRef}
                    type="text"
                    name="origin_city"
                    value={form.origin_city}
                    onChange={(e) => {
                      setForm({ ...form, origin_city: e.target.value });
                      setShowOriginDropdown(true);
                    }}
                    onFocus={() => setShowOriginDropdown(true)}
                    placeholder="e.g. London, Chennai, New York"
                    className="w-full pl-9 pr-9 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-semibold text-gray-800 dark:text-gray-100 placeholder-gray-400 transition"
                  />
                  <button
                    type="button"
                    onClick={handleUseCurrentLocation}
                    title="Use my current GPS location"
                    disabled={gpsLoading}
                    className={`absolute right-2 p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition ${
                      gpsSuccess ? 'text-emerald-500' : ''
                    }`}
                  >
                    {gpsLoading ? (
                      <IconLoader2 size={16} className="animate-spin text-blue-600" />
                    ) : gpsSuccess ? (
                      <IconCheck size={16} className="text-emerald-500" />
                    ) : (
                      <IconCurrentLocation size={16} />
                    )}
                  </button>
                </div>

                {/* Autocomplete Dropdown */}
                {showOriginDropdown && originSuggestions.length > 0 && (
                  <div className="absolute z-30 left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden max-h-48 overflow-y-auto">
                    {originSuggestions.map((item, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setForm({ ...form, origin_city: item.name });
                          setShowOriginDropdown(false);
                        }}
                        className="w-full text-left px-3.5 py-2 text-xs hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-700 dark:text-gray-200 flex items-center justify-between border-b border-gray-50 dark:border-gray-700/50 last:border-0"
                      >
                        <span className="font-semibold">{item.name}</span>
                        <span className="text-[11px] text-gray-400">{item.country}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Destination */}
              <div className="relative">
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Destination <span className="text-red-500">*</span>
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3 text-gray-400 pointer-events-none">
                    <IconMapPin size={16} />
                  </div>
                  <input
                    ref={destInputRef}
                    type="text"
                    name="destination"
                    required
                    value={form.destination}
                    onChange={(e) => {
                      setForm({ ...form, destination: e.target.value });
                      setShowDestDropdown(true);
                    }}
                    onFocus={() => setShowDestDropdown(true)}
                    placeholder="e.g. Tokyo, Paris, Bali, Kyoto"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-semibold text-gray-800 dark:text-gray-100 placeholder-gray-400 transition"
                  />
                </div>

                {/* Autocomplete Dropdown */}
                {showDestDropdown && destSuggestions.length > 0 && (
                  <div className="absolute z-30 left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl overflow-hidden max-h-48 overflow-y-auto">
                    {destSuggestions.map((item, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setForm((prev) => ({
                            ...prev,
                            destination: item.name,
                            country: item.country || prev.country,
                            currency: item.currency || prev.currency,
                          }));
                          setShowDestDropdown(false);
                        }}
                        className="w-full text-left px-3.5 py-2 text-xs hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-700 dark:text-gray-200 flex items-center justify-between border-b border-gray-50 dark:border-gray-700/50 last:border-0"
                      >
                        <span className="font-semibold">{item.name}</span>
                        <span className="text-[11px] text-gray-400">{item.country}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 2. WHEN ARE YOU TRAVELLING? */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                2. When are you travelling?
              </span>
              {durationDays > 0 && isDateRangeValid && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  ✨ {durationDays} {durationDays === 1 ? 'Day Trip' : `Days / ${durationNights} Night${durationNights === 1 ? '' : 's'}`}
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Departure Date <span className="text-red-500">*</span>
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3 text-gray-400 pointer-events-none">
                    <IconCalendar size={16} />
                  </div>
                  <input
                    type="date"
                    required
                    min={todayStr}
                    value={form.start_date}
                    onChange={(e) => {
                      const newStart = e.target.value;
                      let newEnd = form.end_date;
                      if (newEnd && new Date(newEnd) < new Date(newStart)) {
                        newEnd = newStart;
                      }
                      setForm({ ...form, start_date: newStart, end_date: newEnd });
                    }}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-semibold text-gray-800 dark:text-gray-100 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
                  Return Date <span className="text-red-500">*</span>
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3 text-gray-400 pointer-events-none">
                    <IconCalendar size={16} />
                  </div>
                  <input
                    type="date"
                    required
                    min={form.start_date || todayStr}
                    value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-semibold text-gray-800 dark:text-gray-100 transition"
                  />
                </div>
              </div>
            </div>

            {!isDateRangeValid && (
              <p className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                Return date cannot be earlier than departure date.
              </p>
            )}
          </div>

          {/* 3. WHO'S TRAVELLING? */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                3. Who's travelling?
              </span>
              <span className="text-xs font-bold text-gray-600 dark:text-gray-300">
                {parseInt(form.adults || 1) + parseInt(form.children || 0)} Traveller{parseInt(form.adults || 1) + parseInt(form.children || 0) > 1 ? 's' : ''}
                {parseInt(form.children || 0) > 0 ? ` (${form.adults} Adults, ${form.children} Child${form.children > 1 ? 'ren' : ''})` : ''}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3.5 p-3.5 rounded-2xl bg-gray-50/70 dark:bg-gray-900/40 border border-gray-200/80 dark:border-gray-700/80">
              {/* Adults Counter */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="block text-xs font-bold text-gray-800 dark:text-gray-200">Adults</span>
                  <span className="block text-[10px] text-gray-400">Age 13+</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, adults: Math.max(1, parseInt(form.adults || 1) - 1) })}
                    disabled={parseInt(form.adults || 1) <= 1}
                    className="w-7 h-7 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:pointer-events-none transition"
                  >
                    <IconMinus size={14} />
                  </button>
                  <span className="w-5 text-center text-xs font-bold text-gray-900 dark:text-white">
                    {form.adults}
                  </span>
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, adults: Math.min(15, parseInt(form.adults || 1) + 1) })}
                    className="w-7 h-7 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                  >
                    <IconPlus size={14} />
                  </button>
                </div>
              </div>

              {/* Children Counter */}
              <div className="flex items-center justify-between border-l border-gray-200 dark:border-gray-700 pl-3.5">
                <div>
                  <span className="block text-xs font-bold text-gray-800 dark:text-gray-200">Children</span>
                  <span className="block text-[10px] text-gray-400">Age 0–12</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, children: Math.max(0, parseInt(form.children || 0) - 1) })}
                    disabled={parseInt(form.children || 0) <= 0}
                    className="w-7 h-7 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:pointer-events-none transition"
                  >
                    <IconMinus size={14} />
                  </button>
                  <span className="w-5 text-center text-xs font-bold text-gray-900 dark:text-white">
                    {form.children}
                  </span>
                  <button
                    type="button"
                    onClick={() => setForm({ ...form, children: Math.min(10, parseInt(form.children || 0) + 1) })}
                    className="w-7 h-7 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                  >
                    <IconPlus size={14} />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 4. WHAT'S YOUR BUDGET? (OPTIONAL) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                4. What's your budget? <span className="text-gray-400 font-normal lowercase">(optional)</span>
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 relative">
                <div className="relative flex items-center">
                  <div className="absolute left-3 text-gray-400 pointer-events-none">
                    <IconCoin size={16} />
                  </div>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    name="budget"
                    value={form.budget}
                    onChange={(e) => setForm({ ...form, budget: e.target.value })}
                    placeholder="e.g. 50,000 (Optional)"
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-semibold text-gray-800 dark:text-gray-100 placeholder-gray-400 transition"
                  />
                </div>
              </div>

              <div>
                <select
                  name="currency"
                  value={form.currency}
                  onChange={(e) => setForm({ ...form, currency: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 text-xs font-bold text-gray-800 dark:text-gray-100 transition"
                >
                  {currencyList.map((curr) => (
                    <option key={curr.code} value={curr.code}>
                      {curr.code} ({curr.symbol || curr.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <p className="text-[11px] text-gray-400 dark:text-gray-500">
              Leave blank to generate an AI-estimated itinerary without budget restrictions.
            </p>
          </div>

          {/* 5. WHAT DO YOU ENJOY? (OPTIONAL) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                5. What do you enjoy? <span className="text-gray-400 font-normal lowercase">(optional)</span>
              </span>
              <span className="text-[10px] text-gray-400">
                {form.interests.length > 0 ? `${form.interests.length} selected` : 'None selected'}
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {PREFERENCE_OPTIONS.map((item) => {
                const isSelected = form.interests.includes(item.id);
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleTogglePreference(item.id)}
                    className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all duration-200 border ${
                      isSelected
                        ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/25 scale-[1.02]'
                        : 'bg-gray-50/80 dark:bg-gray-900/40 text-gray-700 dark:text-gray-300 border-gray-200/90 dark:border-gray-700/80 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    <span>{item.emoji}</span>
                    <span>{item.label}</span>
                    {isSelected && <IconCheck size={13} className="ml-0.5 text-white" />}
                  </button>
                );
              })}
            </div>
          </div>
        </form>

        {/* Modal Footer Action */}
        <div className="p-5 sm:p-6 pt-3 shrink-0 border-t border-gray-100 dark:border-gray-700/80 bg-gray-50/50 dark:bg-gray-800/80">
          <button
            type="button"
            disabled={!isFormValid || submitting}
            onClick={handleSubmit}
            className="w-full py-3 px-5 rounded-2xl text-xs font-extrabold text-white bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-700 hover:to-indigo-800 shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:pointer-events-none transition flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <IconLoader2 size={18} className="animate-spin" />
                <span>Curating Your Personalized Itinerary...</span>
              </>
            ) : (
              <>
                <IconSparkles size={18} />
                <span>Generate My Trip</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
