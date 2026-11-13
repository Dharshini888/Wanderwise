import React, { useState, useEffect } from 'react';
import {
  IconAlertTriangle,
  IconCheck,
  IconPlane,
  IconBuilding,
  IconCoin,
  IconCompass,
  IconCalendar,
  IconUsers,
  IconSparkles,
  IconChevronRight,
  IconInfoCircle,
} from '@tabler/icons-react';
import { formatCurrency } from '../../../../utils/currencyFormatter';
import { fetchBudgetAllocation } from '../../../../api/trips';

const TRANSPORT_MAP = {
  mixed: 'Mixed Transport',
  flight: 'Flight + Metro',
  train: 'Train / High Speed Rail',
  bus: 'Express Bus / Coach',
  car: 'Car Rental / Self Drive',
  bike: 'Motorbike / Bicycle',
  walk: 'Walking / Pedestrian',
  metro: 'Public Metro & Bus',
};

const AI_DIRECTIVE_MAP = {
  hidden_gems: 'Prioritize Hidden Gems',
  avoid_crowds: 'Avoid Crowds & Peak Hours',
  culture_first: 'Prioritize Local Culture & Heritage',
  outdoor_nature: 'Emphasize Nature & Landscapes',
  foodie_focus: 'Focus on Authentic Cuisine',
};

export default function ReviewStep({
  form,
  onNavigateStep,
  onFeasibilityChange,
  onSelectAlternative,
}) {
  const [budgetPlan, setBudgetPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const calculateDays = () => {
    if (!form.start_date || !form.end_date) return 1;
    const s = new Date(form.start_date);
    const e = new Date(form.end_date);
    const diff = Math.ceil((e - s) / (1000 * 60 * 60 * 24)) + 1;
    return diff > 0 ? diff : 1;
  };

  const days = calculateDays();
  const rawBudget = parseFloat(form.budget) || 1000;
  const currency = form.currency || 'USD';
  const adults = parseInt(form.adults) || 1;
  const children = parseInt(form.children) || 0;
  const totalTravelers = adults + children;

  const rawTransport = (form.transportation || '').toLowerCase().trim();
  const transportDisplay = TRANSPORT_MAP[rawTransport] || form.transportation || 'Mixed Transport';

  // Fetch Central Budget Allocation calculation
  useEffect(() => {
    let isCancelled = false;
    setLoading(true);
    setFetchError(null);

    const params = {
      budget: rawBudget,
      currency: currency,
      tier: form.budget_type || 'mid_range',
      destination: form.destination || 'Destination',
      origin_city: form.origin_city || 'Coimbatore',
      days: days,
      adults: adults,
      children: children,
      travel_style: form.travel_style || (children > 0 ? 'family' : 'solo'),
      transport_mode: transportDisplay,
      accommodation_preference: form.accommodation_preference || 'hotel',
    };

    fetchBudgetAllocation(params)
      .then((data) => {
        if (!isCancelled) {
          setBudgetPlan(data);
          setLoading(false);
          if (onFeasibilityChange) {
            onFeasibilityChange(data.is_feasible, data);
          }
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          console.error('[ReviewStep] Budget allocation fetch error:', err);
          setFetchError(err.message || 'Failed to calculate budget allocation');
          setLoading(false);
          // If error in sandbox or offline, default to safe assumption
          if (onFeasibilityChange) {
            onFeasibilityChange(true, null);
          }
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [
    rawBudget,
    currency,
    form.budget_type,
    form.destination,
    form.origin_city,
    days,
    adults,
    children,
    transportDisplay,
    form.accommodation_preference,
  ]);

  const rawDirectives = form.ai_preferences
    ? form.ai_preferences.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const directiveLabels = rawDirectives.map((d) => AI_DIRECTIVE_MAP[d] || d);

  // Parse explicit interests only
  const selectedInterests = form.interests
    ? form.interests
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  const isFeasible = budgetPlan ? budgetPlan.is_feasible : true;
  const shortfall = budgetPlan ? budgetPlan.shortfall : 0;
  const shortfallPct = budgetPlan ? budgetPlan.shortfall_percentage : 0;
  const estTotalCost = budgetPlan ? budgetPlan.total_estimated_trip_cost : rawBudget;
  const transDetails = budgetPlan?.transportation_details;

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-200 dark:border-gray-700 animate-pulse">
        <div className="w-8 h-8 border-3 border-blue-500/20 border-t-blue-600 rounded-full animate-spin mx-auto" />
        <h4 className="text-sm font-extrabold text-gray-800 dark:text-gray-200">
          Evaluating Door-to-Door Budget Feasibility...
        </h4>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Calculating transportation benchmarks, lodging occupancy, meals, and activities for {form.destination || 'your trip'}.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 1. Trip Overview Banner */}
      <div
        className={`p-4 rounded-2xl text-white shadow-lg space-y-1 transition-all ${
          isFeasible
            ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600'
            : 'bg-gradient-to-r from-rose-600 via-red-600 to-amber-600'
        }`}
      >
        <div className="flex justify-between items-center">
          <span className="text-[10px] uppercase font-bold tracking-widest text-white/80">
            Trip Overview & Feasibility
          </span>
          <span
            className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center gap-1 shadow-sm ${
              isFeasible
                ? 'bg-emerald-500 text-white'
                : 'bg-white text-rose-700 font-extrabold animate-pulse'
            }`}
          >
            {isFeasible ? (
              <>
                <IconCheck size={12} /> Budget Feasible
              </>
            ) : (
              <>
                <IconAlertTriangle size={12} /> Over Budget (+{shortfallPct}%)
              </>
            )}
          </span>
        </div>
        <h3 className="text-xl font-extrabold">{form.destination || 'Destination'}</h3>
        <p className="text-xs text-white/90 font-medium">
          From {form.origin_city || 'Origin'} • {form.start_date} to {form.end_date} • {days} Days ({Math.max(1, days - 1)} Nights) • {form.travel_style || 'Solo'} Style • {form.budget_type || 'Mid-range'}
        </p>
      </div>

      {/* 2. STRICT BUDGET FEASIBILITY ALERT SCREEN (If Budget Insufficient) */}
      {!isFeasible && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 rounded-2xl border-2 border-rose-300 dark:border-rose-800 space-y-3 shadow-md animate-fadeIn">
          <div className="flex items-start gap-2.5">
            <div className="p-2 bg-rose-100 dark:bg-rose-900/60 rounded-xl text-rose-600 dark:text-rose-400 shrink-0">
              <IconAlertTriangle size={22} />
            </div>
            <div className="space-y-1 flex-1">
              <h4 className="text-sm font-extrabold text-rose-900 dark:text-rose-200">
                Your budget is insufficient for this destination.
              </h4>
              <p className="text-xs text-rose-700 dark:text-rose-300 leading-relaxed">
                {budgetPlan?.feasibility_note ||
                  `The estimated minimum cost (${formatCurrency(estTotalCost, currency)}) exceeds your available budget (${formatCurrency(rawBudget, currency)}) by ${formatCurrency(shortfall, currency)}.`}
              </p>
            </div>
          </div>

          {/* Key Feasibility Metric Cards */}
          <div className="grid grid-cols-3 gap-2 pt-1 text-center">
            <div className="p-2.5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
              <span className="text-[10px] font-bold text-gray-500 uppercase block">Available Budget</span>
              <span className="text-xs font-black text-gray-800 dark:text-gray-100 block mt-0.5">
                {formatCurrency(rawBudget, currency)}
              </span>
            </div>
            <div className="p-2.5 bg-white dark:bg-gray-800 rounded-xl border border-blue-200 dark:border-blue-900">
              <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase block">Min. Required</span>
              <span className="text-xs font-black text-blue-700 dark:text-blue-300 block mt-0.5">
                {budgetPlan?.formatted_total_estimated_cost || formatCurrency(estTotalCost, currency)}
              </span>
            </div>
            <div className="p-2.5 bg-rose-100 dark:bg-rose-900/40 rounded-xl border border-rose-300 dark:border-rose-700">
              <span className="text-[10px] font-bold text-rose-700 dark:text-rose-400 uppercase block">Shortfall</span>
              <span className="text-xs font-black text-rose-700 dark:text-rose-300 block mt-0.5">
                +{budgetPlan?.formatted_shortfall || formatCurrency(shortfall, currency)}
              </span>
            </div>
          </div>

          {/* Quick-Fix Action Buttons */}
          <div className="pt-1">
            <span className="text-[11px] font-extrabold text-gray-700 dark:text-gray-300 block mb-1.5">
              Choose an adjustment to proceed:
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => onNavigateStep && onNavigateStep(4)}
                className="py-2 px-2 rounded-xl text-[11px] font-bold bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-all text-center flex items-center justify-center gap-1"
              >
                Adjust Budget <IconChevronRight size={13} />
              </button>
              <button
                type="button"
                onClick={() => onNavigateStep && onNavigateStep(2)}
                className="py-2 px-2 rounded-xl text-[11px] font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm transition-all text-center flex items-center justify-center gap-1"
              >
                Change Dates <IconChevronRight size={13} />
              </button>
              <button
                type="button"
                onClick={() => onNavigateStep && onNavigateStep(1)}
                className="py-2 px-2 rounded-xl text-[11px] font-bold bg-purple-600 text-white hover:bg-purple-700 shadow-sm transition-all text-center flex items-center justify-center gap-1"
              >
                Change Place <IconChevronRight size={13} />
              </button>
            </div>
          </div>

          {/* Realistic Affordable Alternatives */}
          {budgetPlan?.affordable_alternatives && budgetPlan.affordable_alternatives.length > 0 && (
            <div className="pt-2 border-t border-rose-200 dark:border-rose-800/80 space-y-2">
              <span className="text-[11px] font-extrabold text-gray-800 dark:text-gray-200 block">
                Recommended Affordable Alternatives for Your Budget:
              </span>
              <div className="space-y-1.5">
                {budgetPlan.affordable_alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center justify-between gap-2 shadow-xs"
                  >
                    <div className="space-y-0.5 text-left flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-extrabold text-xs text-gray-900 dark:text-white truncate">
                          {alt.name}
                        </span>
                        <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">
                          {alt.type}
                        </span>
                      </div>
                      <p className="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1">
                        {alt.reason}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-black text-emerald-600 dark:text-emerald-400 block">
                        ~{alt.est_cost}
                      </span>
                      {onSelectAlternative && (
                        <button
                          type="button"
                          onClick={() => onSelectAlternative(alt.name)}
                          className="mt-1 text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Select Destination →
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. Feasible Budget Summary Numbers (If Budget Feasible) */}
      {isFeasible && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Total Budget</span>
            <span className="text-sm font-black text-emerald-600 dark:text-emerald-400 block mt-0.5">
              {formatCurrency(rawBudget, currency)}
            </span>
            <span className="text-[9px] text-gray-500 block">Allocated ceiling</span>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Est. Trip Cost</span>
            <span className="text-sm font-black text-blue-600 dark:text-blue-400 block mt-0.5">
              {budgetPlan?.formatted_total_estimated_cost || formatCurrency(estTotalCost, currency)}
            </span>
            <span className="text-[9px] text-gray-500 block">Door-to-door group total</span>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Surplus Buffer</span>
            <span className="text-sm font-black text-teal-600 dark:text-teal-400 block mt-0.5">
              {budgetPlan?.formatted_remaining_budget || formatCurrency(Math.max(0, rawBudget - estTotalCost), currency)}
            </span>
            <span className="text-[9px] text-gray-500 block">Unallocated safety balance</span>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <span className="text-gray-500 dark:text-gray-400 text-[10px] block font-bold uppercase">Uncertainty Range</span>
            <span className="text-xs font-black text-purple-600 dark:text-purple-400 block mt-0.5">
              {budgetPlan?.uncertainty_range?.formatted_range || '±10% Range'}
            </span>
            <span className="text-[9px] text-gray-500 block">Seasonal variation</span>
          </div>
        </div>
      )}

      {/* 4. Transportation Breakdown Card */}
      <div className="p-3.5 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2.5 text-xs">
        <div className="flex justify-between items-center border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <div className="flex items-center gap-1.5">
            <IconPlane size={16} className="text-blue-600 dark:text-blue-400" />
            <span className="font-extrabold text-gray-800 dark:text-gray-200">
              Intercity & Flight Corridor Breakdown ({transDetails?.corridor_mode || transDetails?.mode || 'Flight Transit'})
            </span>
          </div>
          <span className="text-[10px] font-extrabold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/40 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800">
            {transDetails?.pricing_type || 'Market Benchmark'}
          </span>
        </div>

        {transDetails?.local_transit_mode && (
          <div className="text-[10px] text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-2.5 py-1 rounded-md flex items-center justify-between">
            <span>Destination Local Transit: <strong>{transDetails.local_transit_mode}</strong></span>
            <span className="text-gray-500 text-[9px]">Included in Local Transit category below</span>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
          <div className="p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
            <span className="text-gray-500 text-[10px] block font-semibold">Outbound Transit</span>
            <span className="font-bold text-gray-900 dark:text-white block mt-0.5">
              {transDetails?.formatted_outbound || formatCurrency(budgetPlan?.outbound_travel_estimate || 0, currency)}
            </span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
            <span className="text-gray-500 text-[10px] block font-semibold">Return Transit</span>
            <span className="font-bold text-gray-900 dark:text-white block mt-0.5">
              {transDetails?.formatted_return || formatCurrency(budgetPlan?.return_travel_estimate || 0, currency)}
            </span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
            <span className="text-gray-500 text-[10px] block font-semibold">Group Transport Total</span>
            <span className="font-extrabold text-blue-600 dark:text-blue-400 block mt-0.5">
              {transDetails?.formatted_group_total || transDetails?.formatted_total_transport || formatCurrency((budgetPlan?.outbound_travel_estimate || 0) * 2, currency)}
            </span>
          </div>
          <div className="p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
            <span className="text-gray-500 text-[10px] block font-semibold">Per-Person Transport</span>
            <span className="font-bold text-gray-900 dark:text-white block mt-0.5">
              {transDetails?.formatted_per_person || formatCurrency(Math.round(((budgetPlan?.outbound_travel_estimate || 0) * 2) / Math.max(1, totalTravelers)), currency)}
            </span>
          </div>
        </div>

        {children > 0 && transDetails && (
          <div className="flex items-center gap-3 text-[10px] text-gray-600 dark:text-gray-400 px-1">
            <span>Adult RT Fare: <strong>{transDetails.formatted_adult_fare}</strong> / adult</span>
            <span>•</span>
            <span>Child RT Fare: <strong>{transDetails.formatted_child_fare}</strong> / child</span>
          </div>
        )}

        <div className="flex items-center gap-1.5 text-[10px] text-gray-500 dark:text-gray-400 pt-1 border-t border-gray-100 dark:border-gray-700/60">
          <IconInfoCircle size={13} className="shrink-0 text-amber-500" />
          <span>
            {transDetails?.notes ||
              `Transportation estimates based on regional corridor benchmarks for ${adults} adult(s)` +
                (children > 0 ? ` and ${children} child(ren)` : '') +
                `. Directionally split 50/50 outbound and return.`}
          </span>
        </div>
      </div>

      {/* 5. Major Category Expense Breakdown */}
      {budgetPlan?.categories && (
        <div className="p-3.5 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-200 dark:border-gray-700 space-y-2 text-xs">
          <div className="flex justify-between items-center border-b border-gray-200 dark:border-gray-700 pb-1.5">
            <span className="font-extrabold text-gray-800 dark:text-gray-200">
              Estimated Category Expense Breakdown
            </span>
            <span className="text-[10px] font-bold text-gray-500">
              Formula: Outbound + Return + Lodging + Food + Local + Activities + Fees + Contingency
            </span>
          </div>

          <div className="space-y-1.5 pt-1">
            {budgetPlan.categories.map((cat) => (
              <div
                key={cat.key}
                className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-[11px]"
              >
                <div className="space-y-0.5">
                  <span className="font-bold text-gray-800 dark:text-gray-200 block">
                    {cat.label}
                  </span>
                  <span className="text-[10px] text-gray-500 dark:text-gray-400 block">
                    {cat.pricing_basis || cat.notes}
                  </span>
                </div>
                <div className="text-right shrink-0">
                  <span className="font-extrabold text-gray-900 dark:text-white block">
                    {cat.formatted_estimated || formatCurrency(cat.estimated_cost, currency)}
                  </span>
                  <span className="text-[9px] text-gray-400 block">
                    {cat.unit_rate || `${cat.percentage}% allocation`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Structured Parameters & Interests Review */}
      <div className="space-y-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/60 p-3.5 rounded-xl border border-gray-200 dark:border-gray-700">
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Canonical Travelers:</span>
          <span className="font-bold">
            {adults} Adult(s){children > 0 ? `, ${children} Child(ren)` : ''} ({totalTravelers} total)
          </span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Accommodation Standard:</span>
          <span className="font-bold capitalize">
            {form.accommodation_preference || 'Hotel'} ({budgetPlan?.num_rooms || Math.max(1, Math.floor((totalTravelers + 1) / 2))} room(s) standard)
          </span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Travel Pace & Routine:</span>
          <span className="font-bold capitalize">
            {form.activity_pace || 'balanced'} pace • Wake {form.wake_up_time || '08:00'}
          </span>
        </div>
        <div className="flex justify-between border-b border-gray-200 dark:border-gray-700 pb-1.5">
          <span className="font-semibold text-gray-500 dark:text-gray-400">Dietary Preferences:</span>
          <span className="font-bold capitalize">
            {form.food_preferences || 'No Preference'}
          </span>
        </div>

        {/* Explicit Interest Tags Badge List */}
        <div className="pt-1 border-b border-gray-200 dark:border-gray-700 pb-2">
          <div className="flex justify-between items-center mb-1">
            <span className="font-semibold text-gray-500 dark:text-gray-400">Selected Interests:</span>
            <span className="text-[10px] font-extrabold text-blue-600 dark:text-blue-400">
              {selectedInterests.length} Tag(s)
            </span>
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {selectedInterests.length > 0 ? (
              selectedInterests.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-lg text-[10px] font-extrabold bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                >
                  {tag}
                </span>
              ))
            ) : (
              <span className="text-gray-400 italic text-[11px]">No specific tags selected (Sightseeing)</span>
            )}
          </div>
        </div>

        {directiveLabels.length > 0 && (
          <div className="flex justify-between pt-1">
            <span className="font-semibold text-gray-500 dark:text-gray-400">AI Directives:</span>
            <span className="font-bold text-purple-600 dark:text-purple-400 truncate max-w-[220px]">
              {directiveLabels.join(', ')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
