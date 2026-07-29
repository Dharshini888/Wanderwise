import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconAlertTriangle, IconSparkles, IconCheck, IconX,
  IconChevronDown, IconChevronUp, IconInfoCircle, IconArrowRight,
  IconCloudRain, IconWallet, IconMapPin, IconLuggage, IconCompass
} from '@tabler/icons-react';

export default function SuggestionCard({ suggestion, onComplete, onDismiss, onApplyAction }) {
  const [showWhy, setShowWhy] = useState(false);
  const navigate = useNavigate();

  if (!suggestion) return null;

  const { id, type, title, description, priority, priority_score, metadata } = suggestion;

  // Priority Styling Mapping
  const getPriorityStyle = (prio) => {
    switch (prio) {
      case 'high':
        return {
          border: 'border-l-4 border-l-red-500 border-red-500/20 bg-red-500/5',
          badge: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30',
          badgeText: '🔥 High Priority Alert',
          btnBg: 'bg-red-600 hover:bg-red-500 text-white'
        };
      case 'medium':
        return {
          border: 'border-l-4 border-l-amber-500 border-amber-500/20 bg-amber-500/5',
          badge: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30',
          badgeText: '✨ Optimization Idea',
          btnBg: 'bg-amber-600 hover:bg-amber-500 text-white'
        };
      default:
        return {
          border: 'border-l-4 border-l-blue-500 border-blue-500/20 bg-blue-500/5',
          badge: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30',
          badgeText: '🔵 Recommendation',
          btnBg: 'bg-blue-600 hover:bg-blue-500 text-white'
        };
    }
  };

  const style = getPriorityStyle(priority);
  const whyReasons = metadata?.why_reasons || [];
  const actionType = metadata?.action_type;

  const handleActionClick = () => {
    if (actionType === 'update_itinerary' || actionType === 'optimize_route') {
      if (onApplyAction) onApplyAction(suggestion);
      else navigate(`/trips`);
    } else if (actionType === 'view_budget') {
      navigate('/budget');
    } else if (actionType === 'explore_destination') {
      navigate('/recommendations');
    } else if (actionType === 'view_packing') {
      navigate('/packing');
    } else {
      if (onComplete) onComplete(id);
    }
  };

  return (
    <div className={`glass-card p-4 sm:p-5 rounded-2xl ${style.border} space-y-3 transition-all group`}>
      {/* Top Header & Priority Badge */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${style.badge}`}>
            {style.badgeText} ({priority_score || 50} pts)
          </span>
          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
            Category: {type}
          </span>
        </div>

        <button
          onClick={() => onDismiss && onDismiss(id)}
          title="Dismiss suggestion"
          className="p-1 rounded hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500 transition-colors"
        >
          <IconX size={14} />
        </button>
      </div>

      {/* Suggestion Title & Description */}
      <div>
        <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
          {title}
        </h3>
        <p className="text-xs text-[var(--text-secondary)] mt-1 font-medium leading-relaxed">
          {description}
        </p>
      </div>

      {/* AI Explanation Layer ("Why am I seeing this?") */}
      <div className="border-t border-[var(--border-color)] pt-2">
        <button
          onClick={() => setShowWhy(!showWhy)}
          className="text-[11px] font-extrabold text-[var(--color-primary-600)] dark:text-blue-400 flex items-center gap-1 hover:underline cursor-pointer"
        >
          <IconInfoCircle size={13} />
          Why am I seeing this? {showWhy ? <IconChevronUp size={13} /> : <IconChevronDown size={13} />}
        </button>

        {showWhy && (
          <div className="mt-2 p-3 rounded-xl bg-[var(--bg-app)]/80 border border-[var(--border-color)] space-y-1.5 animate-fadeIn">
            <div className="text-[10px] font-extrabold uppercase text-[var(--text-muted)] tracking-wider">
              Reasoning Engine Signals:
            </div>
            <ul className="space-y-1">
              {whyReasons.map((reason, idx) => (
                <li key={idx} className="text-xs text-[var(--text-primary)] flex items-start gap-1.5 font-medium">
                  <span className="text-emerald-500 font-bold shrink-0">✓</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Bottom Action Bar */}
      <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
        <button
          onClick={() => onComplete && onComplete(id)}
          className="px-3 py-1.5 rounded-lg text-xs font-bold text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-app)] transition-colors"
        >
          Mark Done
        </button>

        <button
          onClick={handleActionClick}
          className={`px-4 py-1.5 rounded-lg text-xs font-extrabold shadow-sm transition-all flex items-center gap-1.5 ${style.btnBg}`}
        >
          <span>Apply Action</span>
          <IconArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
