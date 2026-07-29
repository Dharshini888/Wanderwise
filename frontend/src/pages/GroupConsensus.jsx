import React, { useState } from 'react';
import {
  IconUsers,
  IconThumbUp,
  IconThumbDown,
  IconSparkles,
  IconCheck,
  IconX,
} from '@tabler/icons-react';

const INITIAL_ACTIVITIES = [
  { id: '1', name: 'Morning Beach Trip', emoji: '🏖️', description: 'Relax by the ocean and catch the sunrise.', votes: { yes: 3, no: 2 }, aiSuggestion: 'Split group or find a compromise time slot.' },
  { id: '2', name: 'Museum of Modern Art', emoji: '🖼️', description: 'Explore world-class contemporary art exhibitions.', votes: { yes: 2, no: 3 }, aiSuggestion: 'Consider alternative due to low group interest.' },
  { id: '3', name: 'Local Food Tour', emoji: '🍜', description: 'Taste authentic street food and local flavors.', votes: { yes: 5, no: 0 }, aiSuggestion: 'Highly approved — schedule it first!' },
];

export default function GroupConsensus() {
  const [activities] = useState(INITIAL_ACTIVITIES);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeDir, setSwipeDir] = useState(null);

  const handleSwipe = (vote) => {
    setSwipeDir(vote ? 'right' : 'left');
    setTimeout(() => {
      setSwipeDir(null);
      setCurrentIndex(i => i + 1);
    }, 350);
  };

  const current = activities[currentIndex];
  const progress = (currentIndex / activities.length) * 100;

  return (
    <div className="flex flex-col gap-6 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight font-heading mb-1 flex items-center gap-2">
          <IconUsers className="text-[var(--color-primary-600)]" size={32} /> Group Consensus
        </h1>
        <p className="text-sm text-[var(--text-muted)] font-medium">Vote on activities for the upcoming group trip.</p>
      </div>

      {/* Progress */}
      <div className="glass-card p-4 bg-[var(--bg-card)] flex items-center gap-4">
        <span className="text-xs font-bold text-[var(--text-muted)] whitespace-nowrap">
          {Math.min(currentIndex, activities.length)} / {activities.length} voted
        </span>
        <div className="flex-1 bg-[var(--border-color)] rounded-full h-2 overflow-hidden">
          <div
            className="h-full rounded-full bg-[var(--color-primary-600)] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {current ? (
        <div className="flex flex-col items-center gap-6">
          {/* Swipe Card */}
          <div
            className={`glass-card bg-[var(--bg-card)] w-full max-w-sm p-8 flex flex-col items-center gap-5 text-center shadow-xl border border-[var(--border-color)] transition-all duration-300 ${
              swipeDir === 'right' ? 'translate-x-16 opacity-0 rotate-6' :
              swipeDir === 'left'  ? '-translate-x-16 opacity-0 -rotate-6' : ''
            }`}
          >
            <div className="text-7xl leading-none">{current.emoji}</div>
            <div>
              <h2 className="text-xl font-bold text-[var(--text-primary)] font-heading mb-2">{current.name}</h2>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{current.description}</p>
            </div>
            <div className="w-full bg-blue-50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-xl px-4 py-3 text-xs text-[var(--color-primary-600)] dark:text-blue-400 font-medium flex gap-2 items-start">
              <IconSparkles size={14} className="mt-0.5 flex-shrink-0 text-amber-500" />
              <span className="text-left">{current.aiSuggestion}</span>
            </div>
            <div className="flex gap-4 text-xs font-bold text-[var(--text-muted)]">
              <span className="text-emerald-600">{current.votes.yes} yes</span>
              <span>·</span>
              <span className="text-red-500">{current.votes.no} no</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-6 items-center">
            <button
              onClick={() => handleSwipe(false)}
              className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-950/20 border-2 border-red-200 dark:border-red-800 text-red-500 flex items-center justify-center hover:bg-red-500 hover:text-white hover:border-red-500 transition-all transform active:scale-90 cursor-pointer shadow-md shadow-red-500/10"
            >
              <IconThumbDown size={24} />
            </button>
            <span className="text-xs text-[var(--text-muted)] font-semibold">swipe</span>
            <button
              onClick={() => handleSwipe(true)}
              className="w-16 h-16 rounded-full bg-emerald-50 dark:bg-emerald-950/20 border-2 border-emerald-200 dark:border-emerald-800 text-emerald-600 flex items-center justify-center hover:bg-emerald-500 hover:text-white hover:border-emerald-500 transition-all transform active:scale-90 cursor-pointer shadow-md shadow-emerald-500/10"
            >
              <IconThumbUp size={24} />
            </button>
          </div>

          <p className="text-xs text-[var(--text-muted)]">👍 Yeah &nbsp;·&nbsp; 👎 Nope</p>
        </div>
      ) : (
        /* Results */
        <div className="flex flex-col gap-4 max-w-lg animate-fadeIn">
          <div className="glass-card p-6 bg-[var(--bg-card)] text-center">
            <div className="text-3xl mb-2">🎉</div>
            <h2 className="text-xl font-bold text-[var(--text-primary)] font-heading mb-1">Voting Complete!</h2>
            <p className="text-sm text-[var(--text-muted)]">Here's the AI-powered consensus summary.</p>
          </div>
          {activities.map(act => {
            const total = act.votes.yes + act.votes.no;
            const yesPercent = total > 0 ? Math.round((act.votes.yes / total) * 100) : 0;
            const approved = yesPercent >= 50;
            return (
              <div key={act.id} className="glass-card p-5 bg-[var(--bg-card)] border border-[var(--border-color)] flex gap-4 items-start">
                <div className="text-3xl">{act.emoji}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] font-heading">{act.name}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-0.5 ${approved ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : 'bg-red-50 dark:bg-red-950/20 text-red-500'}`}>
                      {approved ? <IconCheck size={10} /> : <IconX size={10} />}
                      {approved ? 'Approved' : 'Skipped'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-2.5">
                    <div className="flex-1 bg-[var(--border-color)] rounded-full h-1.5 overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${yesPercent}%` }} />
                    </div>
                    <span className="text-[10px] font-bold text-[var(--text-muted)] whitespace-nowrap">{act.votes.yes}↑ {act.votes.no}↓</span>
                  </div>
                  <p className="text-[11px] text-[var(--color-primary-600)] dark:text-blue-400 font-medium flex gap-1 items-center">
                    <IconSparkles size={11} className="text-amber-500" /> {act.aiSuggestion}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
