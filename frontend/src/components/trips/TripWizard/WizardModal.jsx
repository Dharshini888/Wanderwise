import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { IconX, IconSparkles, IconChevronLeft, IconChevronRight } from '@tabler/icons-react';
import { fetchCurrencyRegistry, checkDuplicateTrip } from '../../../api/trips';
import { useAuth } from '../../../context/AuthContext';

import DestinationStep from './steps/DestinationStep';
import DateStep from './steps/DateStep';
import TravelersStep from './steps/TravelersStep';
import BudgetStep from './steps/BudgetStep';
import InterestsStep from './steps/InterestsStep';
import FoodStep from './steps/FoodStep';
import AccommodationStep from './steps/AccommodationStep';
import TransportStep from './steps/TransportStep';
import PaceStep from './steps/PaceStep';
import AccessibilityStep from './steps/AccessibilityStep';
import AiPreferencesStep from './steps/AiPreferencesStep';
import DailyRoutineStep from './steps/DailyRoutineStep';
import WeatherStep from './steps/WeatherStep';
import ReviewStep from './steps/ReviewStep';

export default function WizardModal({ userId, isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [generationStage, setGenerationStage] = useState(0);
  const [currencyList, setCurrencyList] = useState([]);

  const GENERATION_STAGES = [
    { title: 'Personalizing Itinerary Plan', desc: 'Resolving travel style, group dynamics & pace preferences...' },
    { title: 'Curating Real Places & Heritage Sites', desc: 'Selecting verified attractions, UNESCO landmarks & viewpoints...' },
    { title: 'Matching Dining & Dietary Criteria', desc: 'Verifying restaurants, street food & vegetarian-friendly venues...' },
    { title: 'Calculating Route & Door-to-Door Budget', desc: 'Estimating intercity transport, lodging & category allocations...' },
    { title: 'Finalizing & Saving Trip', desc: 'Persisting your complete day-by-day structured itinerary...' },
  ];

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

  const [form, setForm] = useState({
    destination: '',
    country: '',
    origin_city: 'Coimbatore',
    origin_airport: '',
    destination_airport: '',
    visa_status: 'No Visa Needed',
    start_date: '',
    end_date: '',
    flexible_dates: 'Fixed Dates',
    travel_type: 'leisure',
    travel_style: 'solo',
    adults: 1,
    children: 0,
    seniors: 0,
    pets: 0,
    budget: '1500',
    currency: 'USD',
    budget_type: 'Mid-range',
    interests: 'History, Street Food, Photography, Local Culture',
    food_preferences: 'Street Food, Local Delicacies',
    food_allergies: '',
    accommodation_preference: 'hotel',
    transportation: 'flight',
    activity_pace: 'balanced',
    accessibility: '',
    ai_preferences: 'avoid_crowds,hidden_gems',
    wake_up_time: '08:00',
    sleep_time: '22:30',
    lunch_time: '13:00',
    dinner_time: '19:30',
    preferred_sunset_spot: 'sunset',
    weather_preference: 'mix',
  });

  const { user } = useAuth();

  useEffect(() => {
    if (isOpen) {
      fetchCurrencyRegistry()
        .then((res) => {
          if (Array.isArray(res.data)) {
            setCurrencyList(res.data);
          }
        })
        .catch(() => {});

      if (user) {
        setForm((prev) => ({
          ...prev,
          currency: user.currency || prev.currency || 'USD',
          budget_type: user.preferred_budget || prev.budget_type || 'mid_range',
          travel_style: user.travel_styles ? user.travel_styles.split(',')[0].trim().toLowerCase() : prev.travel_style,
          interests: user.preferred_activities || prev.interests,
          food_preferences: user.dietary_preferences || prev.food_preferences,
          weather_preference: user.preferred_climate || prev.weather_preference,
        }));
      }
    }
  }, [isOpen, user]);

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleToggleInterest = (tag) => {
    let list = form.interests ? form.interests.split(',').map((s) => s.trim()).filter(Boolean) : [];
    if (list.includes(tag)) {
      list = list.filter((t) => t !== tag);
    } else {
      list.push(tag);
    }
    setForm({ ...form, interests: list.join(', ') });
  };

  const handleToggleFood = (food) => {
    let list = form.food_preferences ? form.food_preferences.split(',').map((s) => s.trim()).filter(Boolean) : [];
    if (list.includes(food)) {
      list = list.filter((f) => f !== food);
    } else {
      list.push(food);
    }
    setForm({ ...form, food_preferences: list.join(', ') });
  };

  const handleToggleAccess = (acc) => {
    let list = form.accessibility ? form.accessibility.split(',').map((s) => s.trim()).filter(Boolean) : [];
    if (list.includes(acc)) {
      list = list.filter((a) => a !== acc);
    } else {
      list.push(acc);
    }
    setForm({ ...form, accessibility: list.join(', ') });
  };

  const handleToggleAiPref = (prefId) => {
    let list = form.ai_preferences ? form.ai_preferences.split(',').map((s) => s.trim()).filter(Boolean) : [];
    if (list.includes(prefId)) {
      list = list.filter((p) => p !== prefId);
    } else {
      list.push(prefId);
    }
    setForm({ ...form, ai_preferences: list.join(', ') });
  };

  const validateCurrentStep = () => {
    if (step === 1) return form.destination.trim().length >= 2;
    if (step === 2) {
      if (!form.start_date || !form.end_date) return false;
      return new Date(form.end_date) >= new Date(form.start_date);
    }
    if (step === 4) return parseFloat(form.budget) > 0;
    return true;
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const tripPreferencesObj = {
        destination: form.destination,
        country: form.country,
        origin_city: form.origin_city,
        origin_airport: form.origin_airport,
        destination_airport: form.destination_airport,
        visa_status: form.visa_status,
        start_date: form.start_date,
        end_date: form.end_date,
        flexible_dates: form.flexible_dates,
        travel_type: form.travel_type,
        travel_style: form.travel_style,
        budget: form.budget,
        currency: form.currency,
        budget_type: form.budget_type,
        interests: form.interests,
        accommodation_preference: form.accommodation_preference,
        transportation: form.transportation,
        activity_pace: form.activity_pace,
        travelers: {
          adults: form.adults,
          children: form.children,
          seniors: form.seniors,
          pets: form.pets,
        },
        food: {
          preferences: form.food_preferences,
          allergies: form.food_allergies,
        },
        accessibility: form.accessibility,
        ai: form.ai_preferences,
        daily_routine: {
          wake_up_time: form.wake_up_time,
          sleep_time: form.sleep_time,
          lunch_time: form.lunch_time,
          dinner_time: form.dinner_time,
          preferred_viewpoint: form.preferred_sunset_spot,
        },
        weather: form.weather_preference,
      };

      const payload = {
        ...form,
        user_id: Number(userId),
        budget: parseFloat(form.budget),
        group_size: parseInt(form.adults) + parseInt(form.children) + parseInt(form.seniors),
        trip_preferences: tripPreferencesObj,
        force_create: true,
      };

      try {
        const dupCheck = await checkDuplicateTrip(form.destination, form.start_date);
        if (dupCheck && dupCheck.has_duplicate) {
          if (!window.confirm(dupCheck.message || 'You already have a trip to this destination around this time. Continue anyway?')) {
            setSubmitting(false);
            return;
          }
        }
      } catch (_) {}

      await onSuccess(payload);
      onClose();
    } catch (err) {
      console.error('[WizardModal] Generation error:', err);
      const errMsg = err?.response?.data?.detail || err?.message || 'Failed to generate itinerary. Please try again.';
      alert(`Itinerary generation notice: ${errMsg}`);
    } finally {
      setSubmitting(false);
    }
  };

  const renderStepTitle = () => {
    const titles = [
      '1. Destination & Origin',
      '2. Trip Dates & Duration',
      '3. Travelers & Group Style',
      '4. Budget & Currency',
      '5. Activity Interests & Tags',
      '6. Dining & Dietary Preferences',
      '7. Accommodation Preference',
      '8. Primary Transportation Mode',
      '9. Daily Activity Pace',
      '10. Accessibility & Comfort',
      '11. AI Recommendation Directives',
      '12. Daily Routine & Schedule',
      '13. Weather & Climate Preferences',
      '14. Review & AI Itinerary Generation',
    ];
    return titles[step - 1];
  };

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/65 backdrop-blur-md p-4 sm:p-6 overflow-hidden">
      <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden relative">
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
            {/* Visual Step Indicator Dots */}
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
        {/* Header & Progress Bar */}
        <div className="p-6 pb-4 shrink-0 border-b border-gray-100 dark:border-gray-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                Step {step} of 14
              </span>
              <h2 className="text-lg font-extrabold font-heading text-gray-900 dark:text-white">
                {renderStepTitle()}
              </h2>
            </div>
            <button onClick={onClose} className="p-2 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
              <IconX size={20} />
            </button>
          </div>

          <div className="w-full bg-gray-100 dark:bg-gray-700 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full transition-all duration-300"
              style={{ width: `${(step / 14) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Body - Scrollable Container */}
        <div className="p-6 py-4 overflow-y-auto flex-1 min-h-0 custom-scrollbar">
          {step === 1 && <DestinationStep form={form} onChange={handleChange} />}
          {step === 2 && <DateStep form={form} onChange={handleChange} />}
          {step === 3 && <TravelersStep form={form} onChange={handleChange} />}
          {step === 4 && <BudgetStep form={form} onChange={handleChange} currencyList={currencyList} />}
          {step === 5 && <InterestsStep form={form} onToggleInterest={handleToggleInterest} />}
          {step === 6 && <FoodStep form={form} onChange={handleChange} onToggleFood={handleToggleFood} />}
          {step === 7 && <AccommodationStep form={form} onChange={handleChange} />}
          {step === 8 && <TransportStep form={form} onChange={handleChange} />}
          {step === 9 && <PaceStep form={form} onChange={handleChange} />}
          {step === 10 && <AccessibilityStep form={form} onToggleAccess={handleToggleAccess} />}
          {step === 11 && <AiPreferencesStep form={form} onToggleAiPref={handleToggleAiPref} />}
          {step === 12 && <DailyRoutineStep form={form} onChange={handleChange} />}
          {step === 13 && <WeatherStep form={form} onChange={handleChange} />}
          {step === 14 && <ReviewStep form={form} />}
        </div>

        {/* Footer Navigation */}
        <div className="p-6 pt-4 shrink-0 border-t border-gray-100 dark:border-gray-700/80 bg-white dark:bg-gray-800 flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="px-4 py-2.5 rounded-xl text-xs font-bold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 flex items-center gap-1"
            >
              <IconChevronLeft size={16} /> Back
            </button>
          ) : <div />}

          {step < 14 ? (
            <button
              type="button"
              disabled={!validateCurrentStep()}
              onClick={() => setStep(step + 1)}
              className="px-5 py-2.5 rounded-xl text-xs font-extrabold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1 shadow-md"
            >
              Next Step <IconChevronRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="px-6 py-2.5 rounded-xl text-xs font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg flex items-center gap-2 disabled:opacity-50"
            >
              <IconSparkles size={18} /> {submitting ? 'Generating AI Itinerary...' : 'Generate Personalized Itinerary'}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
