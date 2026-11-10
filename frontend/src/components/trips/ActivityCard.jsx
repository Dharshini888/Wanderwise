import React from 'react';
import { Link } from 'react-router-dom';
import {
  IconLock, IconLockOpen, IconTrash, IconMapPin, IconClock,
  IconSparkles, IconWalk, IconCamera, IconInfoCircle, IconExternalLink, IconSoup, IconArrowRight, IconRoute
} from '@tabler/icons-react';
import { formatCurrency } from '../../utils/currencyFormatter';
import VerificationBadge from '../ui/VerificationBadge';

export default function ActivityCard({ activity, tripCurrency = 'USD', onLockToggle, onDelete, isDragging }) {
  if (!activity) return null;

  const isLocked = activity.is_locked;
  const costAmt = activity.cost?.amount !== undefined ? activity.cost.amount : (activity.ticket_price || 0);
  const currCode = activity.cost?.currency || tripCurrency || 'USD';
  const formattedCost = activity.formatted_cost || (costAmt > 0 ? formatCurrency(costAmt, currCode) : 'Free Entry');

  const meta = activity.metadata || activity.activity_metadata || {};
  const place = activity.place || {};


  // Category & Area Suggestion identification
  const catLower = (place.category || '').toLowerCase();
  const isAreaSuggestion = activity.is_area_suggestion || meta.is_area_suggestion || catLower.includes('area suggestion') || (activity.title || '').toLowerCase().includes('area dining suggestion');
  const isDining = !isAreaSuggestion && (catLower.includes('restaurant') || catLower.includes('cafe') || catLower.includes('food') || activity.activity_type === 'meal');
  const isTransit = activity.activity_type === 'transit' || catLower.includes('transit') || (activity.title || '').toLowerCase().includes('transfer') || (activity.title || '').toLowerCase().includes('arrival window') || (activity.title || '').toLowerCase().includes('departure window');
  const dietarySuitability = activity.dietary_suitability || meta.dietary_suitability;
  const provenance = activity.provenance || meta.provenance;

  const isTravelAvailable = activity.transport_mode && activity.transport_mode !== 'Not available';
  const rawDist = meta.distance || activity.distance;
  const isZeroDist = rawDist === 0 || rawDist === '0' || rawDist === '0.0' || rawDist === '0.0 km' || rawDist === '0 km';
  const travelDist = (!rawDist || rawDist === 'Not available' || rawDist === 'Unavailable' || isZeroDist) ? null : rawDist;
  const travelDur = activity.transport_duration && activity.transport_duration !== 'Not available' ? activity.transport_duration : null;

  let travelVerification = meta.verification_status;
  if (isAreaSuggestion) {
    travelVerification = 'Route Unavailable';
  } else if (!travelVerification) {
    if (meta.verification_status === 'Co-located Venue' || meta.verification_status === 'Adjacent Location') {
      travelVerification = 'Co-located Venue';
    } else if (meta.verification_status === 'Estimated Distance') {
      travelVerification = 'Estimated Distance';
    } else if (travelDist && isTravelAvailable && meta.geometry && meta.geometry.length > 0) {
      travelVerification = 'Route Calculated';
    } else if (travelDist && isTravelAvailable) {
      travelVerification = 'Estimated Distance';
    } else {
      travelVerification = 'Route Unavailable';
    }
  }

  // Clean single tip extraction
  let tipText = '';
  if (meta.tips) {
    if (Array.isArray(meta.tips) && meta.tips.length > 0) {
      tipText = typeof meta.tips[0] === 'string' ? meta.tips[0] : String(meta.tips[0]);
    } else if (typeof meta.tips === 'string') {
      tipText = meta.tips;
    }
  }

  // Multi-bullet AI reason rationale
  const aiReasonStr = activity.ai_reason || '';
  const aiReasonLines = aiReasonStr.split('\n').filter(Boolean);

  // Meal cost calculation
  const mealCostVal = activity.meal_cost || meta.meal_cost;
  let formattedMealCost = '';
  if (mealCostVal) {
    if (typeof mealCostVal === 'number' || !isNaN(Number(mealCostVal))) {
      formattedMealCost = formatCurrency(Number(mealCostVal), currCode);
    } else {
      formattedMealCost = String(mealCostVal);
    }
  } else if (costAmt > 0) {
    formattedMealCost = formatCurrency(costAmt, currCode);
  } else {
    formattedMealCost = 'A la carte dining (Market estimate)';
  }

  // Signature dish
  const sigDish = meta.signature_dish || place.signature_dish;

  // Nearby places list
  const nearbyList = place.nearby || meta.nearby || [];

  // Opening hours resolution
  const hasOpeningHours = Boolean(place.opening_time || meta.opening_time);
  const openTime = place.opening_time || meta.opening_time;
  const closeTime = place.closing_time || meta.closing_time || '06:00 PM';
  
  // Format itinerary date string if present
  let dateLabel = 'Itinerary Date';
  if (activity.date) {
    try {
      const dObj = new Date(activity.date);
      dateLabel = dObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch (_) {}
  }

  // Google Maps Search URL
  const gMapsUrl = place.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent((place.name || activity.title) + (place.city ? `, ${place.city}` : ''))}`;

  const hasNextStop = Boolean(activity.next_place_name && activity.next_place_name.trim() !== '');

  return (
    <div
      className={`p-5 rounded-2xl bg-white dark:bg-gray-800 border transition-all duration-200 shadow-sm hover:shadow-md space-y-3.5 ${
        isLocked
          ? 'border-amber-300 dark:border-amber-700/60 bg-amber-50/20 dark:bg-amber-900/10'
          : 'border-gray-200 dark:border-gray-700/70'
      } ${isDragging ? 'opacity-50 scale-95 shadow-xl' : ''}`}
    >
      {/* 1. Header Badges & Action Controls */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Time Slot */}
          <span className="text-xs font-extrabold px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300">
            ⏰ {activity.start_time || '08:30'} – {activity.end_time || '09:30'}
            {!hasOpeningHours && <span className="opacity-75 font-normal text-[10px] ml-1">(Tentative)</span>}
          </span>

          {/* Category / Area Suggestion Badge */}
          {isAreaSuggestion ? (
            <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
              📍 Area-Based Suggestion (Unverified)
            </span>
          ) : place.category ? (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 capitalize">
              {place.category}
            </span>
          ) : null}

          {/* Crowd Level */}
          {activity.crowd_level && activity.crowd_level !== 'Not available' && activity.crowd_level !== 'None' && activity.crowd_level !== 'Unavailable' && (
            <span
              className={`text-xs px-2.5 py-1 rounded-lg font-semibold ${
                activity.crowd_level?.toLowerCase() === 'high'
                  ? 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                  : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
              }`}
            >
              Crowd: {activity.crowd_level}
            </span>
          )}

          {/* Single Clean Rating */}
          {place.rating ? (
            <span className="text-xs font-black px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
              ⭐ {place.rating}
            </span>
          ) : (
            <span className="text-xs font-semibold px-2 py-0.5 rounded-lg bg-gray-100 dark:bg-gray-700/60 text-gray-500 dark:text-gray-400">
              Unrated
            </span>
          )}

          {/* Dietary Suitability Badge */}
          {dietarySuitability && (
            <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/50">
              🌱 {dietarySuitability}
            </span>
          )}

          {/* Intercity Transit Badge */}
          {isTransit && (
            <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50">
              🚌 Intercity Transit
            </span>
          )}
        </div>

        {/* Lock & Delete Action Buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <a
            href={gMapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open place on Google Maps"
            className="p-1.5 rounded-lg text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
          >
            <IconExternalLink size={16} />
          </a>

          <button
            onClick={() => onLockToggle && onLockToggle(activity.id)}
            title={isLocked ? 'Unlock Activity (Will be regenerated by AI)' : 'Lock Activity (Protects from AI regeneration)'}
            className={`p-1.5 rounded-lg transition-colors ${
              isLocked
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300'
                : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {isLocked ? <IconLock size={16} /> : <IconLockOpen size={16} />}
          </button>

          <button
            onClick={() => onDelete && onDelete(activity.id)}
            title="Delete Activity"
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <IconTrash size={16} />
          </button>
        </div>
      </div>

      {/* 2. Main Activity Title & Description */}
      <div>
        <h4 className="text-base font-extrabold text-gray-900 dark:text-white font-heading">
          {activity.title}
        </h4>
        {activity.description && (
          <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 leading-relaxed">
            {activity.description}
          </p>
        )}
      </div>

      {/* 3. Place Details: Address & Opening Hours */}
      {(place.name || place.address) && (
        <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/40 border border-gray-100 dark:border-gray-700 space-y-1 text-xs">
          <div className="font-extrabold text-gray-900 dark:text-gray-100 flex items-center justify-between gap-1.5">
            <div className="flex items-center gap-1.5">
              <IconMapPin size={16} className="text-blue-600 dark:text-blue-400 shrink-0" />
              <span>{place.name || activity.title}</span>
            </div>
            <a
              href={gMapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-bold text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
            >
              <span>Map</span>
              <IconExternalLink size={12} />
            </a>
          </div>
          {place.address && (
            <p className="text-[11px] text-gray-500 dark:text-gray-400 pl-5 leading-tight">
              📍 {place.address}
            </p>
          )}
          <p className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 pl-5 flex items-center gap-1">
            {hasOpeningHours ? (
              <span>🟢 Open on {dateLabel} • {openTime} – {closeTime}</span>
            ) : (
              <span className="text-amber-600 dark:text-amber-400 font-semibold">⚠️ Hours unverified • Tentative schedule</span>
            )}
          </p>
        </div>
      )}

      {/* 4. Cost Label & Duration Row */}
      <div className="flex items-center justify-between text-xs pt-0.5 flex-wrap gap-2">
        <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400 font-semibold">
          {activity.duration_minutes && (
            <span className="flex items-center gap-1">
              <IconClock size={14} /> Duration: {activity.duration_minutes} mins
            </span>
          )}
          {isDining ? (
            <span className="font-extrabold text-emerald-600 dark:text-emerald-400">
              Est. Meal Cost: {formattedMealCost}
            </span>
          ) : isTransit ? (
            <span className="font-extrabold text-indigo-600 dark:text-indigo-400">
              Transit: {costAmt > 0 ? formattedCost : 'Transit Included (Estimated)'}
            </span>
          ) : (
            <span className={`font-extrabold ${costAmt > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-500'}`}>
              Ticket: {costAmt > 0 ? formattedCost : (activity.ticket_price === 0 || activity.ticket_price === 0.0 || activity.is_free_verified || (meta.provenance?.price_source && meta.provenance.price_source.toLowerCase().includes('free'))) ? 'Free Entry' : 'Price not verified'}
            </span>
          )}
        </div>
      </div>

      {/* 5. Rich Travel Transition or Final Activity Banner */}
      {hasNextStop ? (
        <div className="p-2.5 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 text-xs font-bold flex items-center justify-between gap-2 border border-indigo-100 dark:border-indigo-900/40 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <IconWalk size={15} className="text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span>
              {travelVerification === 'Route Unavailable' ? (
                <span>Travel: Route Pending Verification</span>
              ) : (travelVerification === 'Co-located Venue' || travelVerification === 'Adjacent Location') ? (
                <span>Travel: Walking • {travelDur || '< 5 min'} (Co-located Venue)</span>
              ) : travelVerification === 'Estimated Distance' ? (
                <span>
                  Travel: <span className="capitalize">{activity.transport_mode || 'Walking'}</span>
                  {travelDur ? ` • ~${travelDur}` : ''}
                  {travelDist ? ` (${travelDist})` : ''}
                </span>
              ) : (
                <span>
                  Travel: <span className="capitalize">{activity.transport_mode || 'Walking'}</span>
                  {travelDur ? ` • ${travelDur}` : ''}
                  {travelDist ? ` (${travelDist})` : ''}
                </span>
              )}
            </span>
            <VerificationBadge status={travelVerification} size="xs" />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1 text-[11px] text-indigo-700 dark:text-indigo-300 font-semibold">
              <span>Next: {activity.next_place_name}</span>
              <IconArrowRight size={13} />
            </div>

            <Link
              to={`/transit?from=${encodeURIComponent(place.name || activity.title)}&to=${encodeURIComponent(activity.next_place_name || 'Destination')}${place.latitude ? `&from_lat=${place.latitude}&from_lon=${place.longitude}` : ''}&auto_route=true`}
              className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-extrabold shadow-sm transition-all flex items-center gap-1 shrink-0"
              title="Get Smart Transit route for this transition"
            >
              <IconRoute size={13} />
              <span>Get Route</span>
            </Link>
          </div>
        </div>
      ) : (
        <div className="p-2 rounded-xl bg-gray-50 dark:bg-gray-800/40 text-gray-500 dark:text-gray-400 text-xs font-semibold flex items-center justify-between border border-dashed border-gray-200 dark:border-gray-700">
          <span>🚩 Final activity of the day</span>
          <span className="text-[10px] text-gray-400">Rest & Recharge</span>
        </div>
      )}

      {/* 6. Signature Dish Badge (Dining) */}
      {sigDish && (
        <div className="text-xs text-amber-900 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/40 p-3 rounded-xl flex items-center gap-2 border border-amber-200/80 dark:border-amber-800/40 font-medium">
          <IconSoup size={18} className="shrink-0 text-amber-600" />
          <span><strong>🍽 Signature Dish:</strong> {sigDish}</span>
        </div>
      )}

      {/* 7. Bulleted AI Selection Rationale */}
      {aiReasonLines.length > 0 && (
        <div className="p-3.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900/50 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-purple-800 dark:text-purple-300">
            <IconSparkles size={15} />
            <span>AI Selection Rationale</span>
          </div>
          <div className="text-[11px] text-purple-900 dark:text-purple-200 space-y-1 pl-5">
            {aiReasonLines.map((line, idx) => (
              <div key={idx} className="font-semibold leading-tight">
                {line.startsWith('✓') ? line : `✓ ${line}`}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. Tip & Nearby Places */}
      <div className="space-y-2 pt-0.5">
        {tipText && (
          <div className="text-[11px] text-gray-700 dark:text-gray-300 bg-blue-50/60 dark:bg-blue-950/30 p-3 rounded-xl flex items-start gap-2 border border-blue-100 dark:border-blue-900/40 font-medium">
            <IconInfoCircle size={15} className="text-blue-500 shrink-0 mt-0.5" />
            <span><strong>Tip:</strong> {tipText}</span>
          </div>
        )}

        {nearbyList.length > 0 && (
          <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1.5 flex-wrap pt-0.5">
            <span className="font-extrabold text-gray-800 dark:text-gray-200">Nearby:</span>
            {nearbyList.map((spot, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 font-semibold">
                • {spot}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 9. Direct "Open in Google Maps" Action Button */}
      {place.google_maps_url && (
        <div className="pt-1">
          <a
            href={place.google_maps_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-extrabold shadow-sm transition-colors"
          >
            <IconMapPin size={15} /> Open in Google Maps <IconExternalLink size={13} />
          </a>
        </div>
      )}

      {/* 10. Granular Field-Level Provenance & Verification Transparency */}
      {provenance && (() => {
        const pStatus = isAreaSuggestion ? 'unverified' : (provenance.overall_status || provenance.status || '').toLowerCase();
        let dotColor = 'bg-emerald-500';
        let statusLabel = 'Verified';
        let badgeColor = 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/40';

        if (isAreaSuggestion || pStatus.includes('unavailable') || pStatus.includes('unverified')) {
          dotColor = 'bg-gray-400';
          statusLabel = 'Unverified / Area Suggestion';
          badgeColor = 'bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700';
        } else if (pStatus.includes('estimated') || pStatus.includes('calibrated') || isDining || isTransit) {
          dotColor = 'bg-amber-500';
          statusLabel = 'Estimated';
          badgeColor = 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-800/40';
        }

        const sourceDetail = isAreaSuggestion
          ? 'Area Directory (Not a verified business POI)'
          : (provenance.place_verification || provenance.source || 'Verified Municipal Registry');

        return (
          <div className="pt-2 border-t border-gray-100 dark:border-gray-800 space-y-1.5">
            <div className="flex items-center justify-between gap-2 text-[10px] text-gray-500 dark:text-gray-400 font-medium flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className={`inline-block w-2 h-2 rounded-full ${dotColor} shrink-0`} />
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${badgeColor}`}>
                  {statusLabel}
                </span>
                <span className="font-semibold text-gray-700 dark:text-gray-300">{sourceDetail}</span>
              </div>
              {provenance.price_source && (
                <span className="text-gray-400 text-[9px]">Price Source: {provenance.price_source}</span>
              )}
            </div>

            {/* Field-Level Breakdown Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 text-[9px] text-gray-500 dark:text-gray-400 bg-gray-50/70 dark:bg-gray-800/40 p-2 rounded-lg border border-gray-100 dark:border-gray-700/60">
              <div>
                <span className="block font-bold text-gray-600 dark:text-gray-300">GPS / Coords:</span>
                <span className={place.latitude ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400'}>
                  {place.latitude ? 'Verified (GPS)' : 'Unavailable / Area Center'}
                </span>
              </div>
              <div>
                <span className="block font-bold text-gray-600 dark:text-gray-300">Opening Hours:</span>
                <span className={hasOpeningHours ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}>
                  {hasOpeningHours ? 'Verified Schedule' : 'Hours unverified (Tentative)'}
                </span>
              </div>
              <div>
                <span className="block font-bold text-gray-600 dark:text-gray-300">Rating & Reviews:</span>
                <span className={place.rating ? 'text-amber-600 dark:text-amber-400' : 'text-gray-400'}>
                  {place.rating ? `Community (${place.rating}★)` : 'Unrated'}
                </span>
              </div>
              <div>
                <span className="block font-bold text-gray-600 dark:text-gray-300">Route Status:</span>
                <span className={travelVerification === 'Route Calculated' ? 'text-blue-600 dark:text-blue-400' : travelVerification === 'Estimated Distance' ? 'text-amber-600 dark:text-amber-400' : travelVerification === 'Co-located Venue' ? 'text-purple-600 dark:text-purple-400' : 'text-gray-400'}>
                  {travelVerification}
                </span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
