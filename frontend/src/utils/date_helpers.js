/**
 * date_helpers.js — Safe Local Date Arithmetic and Dynamic Trip Status Engine
 * Handles calendar dates in local browser timezone without UTC day-shift errors.
 */

export const parseLocalDate = (dateStr) => {
  if (!dateStr) return null;
  if (dateStr instanceof Date) {
    return new Date(dateStr.getFullYear(), dateStr.getMonth(), dateStr.getDate());
  }
  const s = String(dateStr).slice(0, 10);
  const parts = s.split('-').map(Number);
  if (parts.length === 3 && !parts.some(isNaN)) {
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }
  const fallback = new Date(dateStr);
  return isNaN(fallback.getTime()) ? null : new Date(fallback.getFullYear(), fallback.getMonth(), fallback.getDate());
};

export const getLocalDateStr = (d = new Date()) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const formatLocalDate = (dateStr, options = { day: 'numeric', month: 'short', year: 'numeric' }) => {
  const d = parseLocalDate(dateStr);
  if (!d) return String(dateStr || '');
  return d.toLocaleDateString('en-US', options);
};

export const calculateTripDuration = (start, end) => {
  const st = parseLocalDate(start);
  const en = parseLocalDate(end);
  if (!st || !en) return 1;
  const diffTime = en.getTime() - st.getTime();
  return Math.max(1, Math.round(diffTime / 86400000) + 1);
};

export const getDaysUntil = (startDateStr) => {
  const st = parseLocalDate(startDateStr);
  if (!st) return 0;
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((st.getTime() - today.getTime()) / 86400000);
};

export const getDaysAgo = (endDateStr) => {
  const en = parseLocalDate(endDateStr);
  if (!en) return 0;
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((today.getTime() - en.getTime()) / 86400000);
};

export const getTripStatusInfo = (startDateStr, endDateStr) => {
  const st = parseLocalDate(startDateStr);
  const en = parseLocalDate(endDateStr) || st;
  if (!st) {
    return {
      status: 'Draft',
      label: 'Draft',
      badgeClass: 'bg-slate-500/15 text-slate-400 border border-slate-500/30',
      pillClass: 'bg-slate-500/20 text-slate-300',
      dotColor: 'bg-slate-400',
      text: 'Draft Plan',
      progressPct: 0
    };
  }

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const totalDays = Math.max(1, Math.round((en.getTime() - st.getTime()) / 86400000) + 1);

  if (today.getTime() < st.getTime()) {
    const daysUntil = Math.round((st.getTime() - today.getTime()) / 86400000);
    return {
      status: 'Upcoming',
      label: 'Upcoming',
      badgeClass: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
      pillClass: 'bg-blue-500/20 text-blue-300',
      dotColor: 'bg-blue-400',
      daysUntil,
      totalDays,
      text: daysUntil === 0 ? 'Starts Today' : `Starts in ${daysUntil} day${daysUntil === 1 ? '' : 's'}`,
      progressPct: 0
    };
  }

  if (today.getTime() > en.getTime()) {
    const daysAgo = Math.round((today.getTime() - en.getTime()) / 86400000);
    return {
      status: 'Completed',
      label: 'Completed',
      badgeClass: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
      pillClass: 'bg-emerald-500/20 text-emerald-300',
      dotColor: 'bg-emerald-400',
      daysAgo,
      totalDays,
      text: daysAgo === 0 ? 'Completed Today' : `Completed ${daysAgo} day${daysAgo === 1 ? '' : 's'} ago`,
      progressPct: 100
    };
  }

  const currentDay = Math.round((today.getTime() - st.getTime()) / 86400000) + 1;
  const progressPct = Math.min(100, Math.round((currentDay / totalDays) * 100));
  return {
    status: 'Ongoing',
    label: 'Ongoing',
    badgeClass: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    pillClass: 'bg-amber-500/20 text-amber-300',
    dotColor: 'bg-amber-400 animate-pulse',
    currentDay,
    totalDays,
    text: `Day ${currentDay} of ${totalDays}`,
    progressPct
  };
};
