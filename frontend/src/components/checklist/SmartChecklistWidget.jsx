import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getChecklist, generateChecklist } from '../../api/checklist';
import {
  IconChecklist,
  IconSparkles,
  IconArrowRight,
  IconAlertCircle,
  IconCheck,
} from '@tabler/icons-react';

export default function SmartChecklistWidget({ tripId, tripTitle }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!tripId) return;
    const fetchChecklist = async () => {
      setLoading(true);
      try {
        const res = await getChecklist(tripId);
        setData(res);
      } catch (err) {
        console.error('[SmartChecklistWidget] Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchChecklist();
  }, [tripId]);

  const handleGenerate = async (e) => {
    e.stopPropagation();
    if (!tripId || generating) return;
    setGenerating(true);
    try {
      const res = await generateChecklist(tripId);
      setData(res);
    } catch (err) {
      console.error('[SmartChecklistWidget] Generate error:', err);
    } finally {
      setGenerating(false);
    }
  };

  if (!tripId) return null;

  const summary = data?.summary || { total: 0, completed: 0, pending: 0, urgent: 0, readiness_percentage: 0 };
  const items = Array.isArray(data?.items) ? data.items : [];
  const urgentTasks = items.filter((i) => i && i.priority === 'URGENT' && i.status === 'PENDING');
  const pendingTasks = items.filter((i) => i && i.status === 'PENDING');

  return (
    <div className="bg-[var(--bg-card)] p-5 rounded-2xl border border-[var(--border-color)] shadow-xs space-y-4 hover:border-blue-500/30 transition-all">
      {/* HEADER */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
            <IconChecklist size={20} />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading tracking-tight">
              Smart Travel Checklist
            </h3>
            {tripTitle && (
              <p className="text-[11px] font-medium text-[var(--text-secondary)] truncate max-w-[180px]">
                {tripTitle}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="p-1.5 rounded-lg text-blue-600 dark:text-blue-400 hover:bg-blue-500/10 transition-colors cursor-pointer border border-blue-500/20"
          title="Generate or update smart checklist"
        >
          <IconSparkles size={16} className={generating ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* READINESS PROGRESS BAR */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="text-[var(--text-secondary)]">Readiness Score</span>
          <span className="text-blue-600 dark:text-blue-400 font-extrabold font-heading">
            {summary.readiness_percentage}%
          </span>
        </div>
        <div className="w-full h-2.5 bg-[var(--bg-subtle)] rounded-full overflow-hidden border border-[var(--border-color)]">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.max(summary.readiness_percentage, 4)}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] font-medium pt-0.5">
          <span>{summary.completed} of {summary.total} completed</span>
          {summary.urgent > 0 && (
            <span className="text-rose-600 dark:text-rose-400 font-bold flex items-center gap-1">
              <IconAlertCircle size={12} />
              {summary.urgent} urgent
            </span>
          )}
        </div>
      </div>

      {/* TOP URGENT / PENDING TASK PREVIEW */}
      {urgentTasks.length > 0 ? (
        <div className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <IconAlertCircle size={16} className="text-rose-600 dark:text-rose-400 shrink-0" />
            <span className="text-xs font-bold text-[var(--text-primary)] truncate">
              {urgentTasks[0].title}
            </span>
          </div>
          <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-600 dark:text-rose-400 uppercase tracking-wider shrink-0">
            Urgent
          </span>
        </div>
      ) : pendingTasks.length > 0 ? (
        <div className="p-3 rounded-xl bg-[var(--bg-subtle)] border border-[var(--border-color)] flex items-center justify-between gap-2">
          <span className="text-xs font-medium text-[var(--text-secondary)] truncate">
            Next: {pendingTasks[0].title}
          </span>
        </div>
      ) : summary.total > 0 ? (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold flex items-center gap-2">
          <IconCheck size={16} />
          <span>All preparation tasks completed!</span>
        </div>
      ) : null}

      {/* VIEW CHECKLIST BUTTON */}
      <button
        onClick={() => navigate(`/checklist?tripId=${tripId}`)}
        className="w-full py-2 px-3 rounded-xl text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
      >
        <span>View Full Checklist</span>
        <IconArrowRight size={14} />
      </button>
    </div>
  );
}
