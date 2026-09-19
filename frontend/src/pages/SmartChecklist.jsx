import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getPaginatedTrips } from '../api/trips';
import {
  getChecklist,
  createChecklistItem,
  updateChecklistItem,
  deleteChecklistItem,
  generateChecklist,
} from '../api/checklist';
import {
  IconChecklist,
  IconSparkles,
  IconPlus,
  IconTrash,
  IconPencil,
  IconAlertCircle,
  IconArrowRight,
  IconRefresh,
  IconFilter,
  IconCalendar,
  IconCheck,
  IconFileText,
  IconBackpack,
  IconReceipt2,
  IconMap,
  IconCloudStorm,
  IconShieldCheck,
  IconBook,
  IconUser,
  IconPlaneDeparture,
} from '@tabler/icons-react';

const CATEGORY_ICONS = {
  DOCUMENTS: IconFileText,
  BOOKINGS: IconMap,
  MONEY: IconReceipt2,
  PACKING: IconBackpack,
  ITINERARY: IconPlaneDeparture,
  WEATHER: IconCloudStorm,
  TRANSIT: IconMap,
  SAFETY: IconShieldCheck,
  CUSTOM: IconUser,
};

const CATEGORIES = [
  'ALL',
  'DOCUMENTS',
  'BOOKINGS',
  'PACKING',
  'MONEY',
  'ITINERARY',
  'WEATHER',
  'SAFETY',
  'CUSTOM',
];

export default function SmartChecklist() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [trips, setTrips] = useState([]);
  const [selectedTripId, setSelectedTripId] = useState(null);
  const [checklistData, setChecklistData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const [activeCategory, setActiveCategory] = useState('ALL');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Form State for Custom Task
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM',
    category: 'CUSTOM',
    due_date: '',
  });

  // Fetch Trips once auth is ready
  useEffect(() => {
    if (authLoading || !user?.id) return;

    const fetchTrips = async () => {
      try {
        const data = await getPaginatedTrips({ limit: 50 });
        const rawList = Array.isArray(data)
          ? data
          : Array.isArray(data?.trips)
          ? data.trips
          : Array.isArray(data?.items)
          ? data.items
          : [];
        const tripList = Array.isArray(rawList) ? rawList : [];
        setTrips(tripList);

        // Preselect trip from query param or first trip
        const paramTripId = searchParams.get('tripId');
        if (paramTripId && tripList.some((t) => t && String(t.id) === String(paramTripId))) {
          setSelectedTripId(Number(paramTripId));
        } else if (tripList.length > 0 && tripList[0]) {
          setSelectedTripId(tripList[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error('[SmartChecklist] Error fetching trips:', err);
        setError('Failed to load trips. Please try again.');
        setLoading(false);
      }
    };

    fetchTrips();
  }, [user, authLoading, searchParams]);

  // Fetch Checklist when selectedTripId changes
  useEffect(() => {
    if (!selectedTripId || authLoading) return;

    const fetchChecklist = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getChecklist(selectedTripId);
        setChecklistData(data);
      } catch (err) {
        console.error('[SmartChecklist] Error fetching checklist:', err);
        setError('Failed to load checklist. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchChecklist();
  }, [selectedTripId, authLoading]);

  // Handle Trip change from dropdown
  const handleTripChange = (e) => {
    const tid = Number(e.target.value);
    setSelectedTripId(tid);
    setSearchParams({ tripId: tid });
  };

  // Trigger Generator
  const handleGenerate = async () => {
    if (!selectedTripId) return;
    setGenerating(true);
    setError(null);
    try {
      const data = await generateChecklist(selectedTripId);
      setChecklistData(data);
    } catch (err) {
      console.error('[SmartChecklist] Generate error:', err);
      setError('Failed to generate smart checklist items.');
    } finally {
      setGenerating(false);
    }
  };

  // Toggle Item Completion
  const handleToggleStatus = async (item) => {
    const newStatus = item.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    
    // Optimistic UI update
    setChecklistData((prev) => {
      if (!prev) return prev;
      const updatedItems = prev.items.map((i) =>
        i.id === item.id ? { ...i, status: newStatus, completed_at: newStatus === 'COMPLETED' ? new Date().toISOString() : null } : i
      );
      const total = updatedItems.length;
      const completed = updatedItems.filter((i) => i.status === 'COMPLETED').length;
      const pending = updatedItems.filter((i) => i.status === 'PENDING').length;
      const urgent = updatedItems.filter((i) => i.priority === 'URGENT' && i.status === 'PENDING').length;
      const readiness_percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

      return {
        ...prev,
        summary: { total, completed, pending, urgent, readiness_percentage },
        items: updatedItems,
      };
    });

    try {
      await updateChecklistItem(item.id, { status: newStatus });
    } catch (err) {
      console.error('[SmartChecklist] Status update failed:', err);
      // Refresh on error
      if (selectedTripId) {
        const fresh = await getChecklist(selectedTripId);
        setChecklistData(fresh);
      }
    }
  };

  // Custom Task Create / Update submission
  const handleSubmitCustomTask = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !selectedTripId) return;

    try {
      if (editingItem) {
        const updated = await updateChecklistItem(editingItem.id, {
          title: formData.title,
          description: formData.description,
          priority: formData.priority,
          due_date: formData.due_date || null,
        });
        setChecklistData((prev) => ({
          ...prev,
          items: prev.items.map((i) => (i.id === editingItem.id ? updated : i)),
        }));
      } else {
        await createChecklistItem(selectedTripId, {
          title: formData.title,
          description: formData.description,
          priority: formData.priority,
          category: formData.category,
          due_date: formData.due_date || null,
        });
        const fresh = await getChecklist(selectedTripId);
        setChecklistData(fresh);
      }

      setShowAddModal(false);
      setEditingItem(null);
      setFormData({ title: '', description: '', priority: 'MEDIUM', category: 'CUSTOM', due_date: '' });
    } catch (err) {
      console.error('[SmartChecklist] Task save error:', err);
      setError('Failed to save custom task.');
    }
  };

  // Delete Custom Task
  const handleDeleteItem = async (itemId) => {
    try {
      await deleteChecklistItem(itemId);
      setChecklistData((prev) => {
        if (!prev) return prev;
        const updatedItems = prev.items.filter((i) => i.id !== itemId);
        const total = updatedItems.length;
        const completed = updatedItems.filter((i) => i.status === 'COMPLETED').length;
        const pending = updatedItems.filter((i) => i.status === 'PENDING').length;
        const urgent = updatedItems.filter((i) => i.priority === 'URGENT' && i.status === 'PENDING').length;
        const readiness_percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

        return {
          ...prev,
          summary: { total, completed, pending, urgent, readiness_percentage },
          items: updatedItems,
        };
      });
    } catch (err) {
      console.error('[SmartChecklist] Delete error:', err);
      setError('Failed to delete checklist item.');
    }
  };

  // Open edit modal
  const handleStartEdit = (item) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      description: item.description || '',
      priority: item.priority || 'MEDIUM',
      category: item.category || 'CUSTOM',
      due_date: item.due_date ? item.due_date.slice(0, 10) : '',
    });
    setShowAddModal(true);
  };

  const selectedTrip = useMemo(
    () => (Array.isArray(trips) ? trips : []).find((t) => t && t.id === selectedTripId),
    [trips, selectedTripId]
  );

  const items = checklistData?.items || [];
  const summary = checklistData?.summary || { total: 0, completed: 0, pending: 0, urgent: 0, readiness_percentage: 0 };

  const urgentItems = useMemo(
    () => items.filter((i) => i.priority === 'URGENT' && i.status === 'PENDING'),
    [items]
  );

  const filteredItems = useMemo(() => {
    if (activeCategory === 'ALL') return items;
    return items.filter((i) => (i.category || 'CUSTOM').toUpperCase() === activeCategory);
  }, [items, activeCategory]);

  const getPriorityBadgeClass = (priority) => {
    switch ((priority || '').toUpperCase()) {
      case 'URGENT':
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'MEDIUM':
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
      case 'LOW':
      default:
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* HEADER BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[var(--bg-card)] p-6 rounded-2xl border border-[var(--border-color)] shadow-xs">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              <IconChecklist size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-[var(--text-primary)] font-heading tracking-tight">
                Smart Travel Checklist
              </h1>
              <p className="text-xs text-[var(--text-secondary)] font-medium">
                Everything you need to prepare for your trip.
              </p>
            </div>
          </div>
        </div>

        {/* TRIP SELECTOR & ACTIONS */}
        <div className="flex flex-wrap items-center gap-3">
          {trips.length > 0 && (
            <select
              value={selectedTripId || ''}
              onChange={handleTripChange}
              className="px-3.5 py-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer max-w-xs"
            >
              {trips.map((t) => (
                <option key={t.id} value={t.id}>
                  ✈️ {t.title || t.destination} ({t.destination})
                </option>
              ))}
            </select>
          )}

          <button
            onClick={handleGenerate}
            disabled={generating || !selectedTripId}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 shadow-md shadow-blue-500/20 transition-all cursor-pointer"
          >
            <IconSparkles size={16} className={generating ? 'animate-spin' : ''} />
            <span>{generating ? 'Generating...' : 'Generate'}</span>
          </button>

          <button
            onClick={() => {
              setEditingItem(null);
              setFormData({ title: '', description: '', priority: 'MEDIUM', category: 'CUSTOM', due_date: '' });
              setShowAddModal(true);
            }}
            disabled={!selectedTripId}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-[var(--text-primary)] bg-[var(--bg-app)] border border-[var(--border-color)] hover:bg-[var(--bg-subtle)] transition-all cursor-pointer"
          >
            <IconPlus size={16} />
            <span>Add Task</span>
          </button>
        </div>
      </div>

      {/* ERROR NOTICE */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-medium">
          <div className="flex items-center gap-2">
            <IconAlertCircle size={18} />
            <span>{error}</span>
          </div>
          <button
            onClick={() => selectedTripId && getChecklist(selectedTripId).then(setChecklistData)}
            className="px-3 py-1 rounded-lg bg-rose-600 text-white font-bold hover:bg-rose-700 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* NO TRIPS STATE */}
      {trips.length === 0 && !loading && (
        <div className="p-8 text-center bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] space-y-3">
          <p className="text-sm font-semibold text-[var(--text-secondary)]">No upcoming trips found.</p>
          <button
            onClick={() => navigate('/trips')}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold shadow-md hover:bg-blue-700 transition-colors"
          >
            Create Your First Trip
          </button>
        </div>
      )}

      {selectedTripId && (
        <>
          {/* READINESS SUMMARY CARD */}
          <div className="bg-[var(--bg-card)] p-6 rounded-2xl border border-[var(--border-color)] shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs font-extrabold uppercase tracking-wider text-[var(--text-muted)]">
                  Trip Readiness Score
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-black text-[var(--text-primary)] font-heading">
                    {summary.readiness_percentage}%
                  </span>
                  <span className="text-xs font-bold text-[var(--text-secondary)]">Ready for travel</span>
                </div>
              </div>

              {/* STAT BADGES */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs font-bold">
                  <IconCheck size={14} />
                  <span>Completed: {summary.completed}</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 text-xs font-bold">
                  <span>Pending: {summary.pending}</span>
                </div>
                {summary.urgent > 0 && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 text-xs font-bold animate-pulse">
                    <IconAlertCircle size={14} />
                    <span>Urgent: {summary.urgent}</span>
                  </div>
                )}
              </div>
            </div>

            {/* PROGRESS BAR */}
            <div className="w-full h-3 bg-[var(--bg-subtle)] rounded-full overflow-hidden p-0.5 border border-[var(--border-color)]">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.max(summary.readiness_percentage, 2)}%` }}
              />
            </div>
          </div>

          {/* URGENT TASKS ALERT SECTION */}
          {urgentItems.length > 0 && (
            <div className="p-5 rounded-2xl bg-rose-500/5 border border-rose-500/20 space-y-3">
              <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
                <IconAlertCircle size={20} className="animate-bounce" />
                <h2 className="text-sm font-extrabold font-heading tracking-tight uppercase">
                  Action Required ({urgentItems.length} Urgent)
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {urgentItems.map((item) => {
                  const CatIcon = CATEGORY_ICONS[item.category] || IconFileText;
                  return (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-rose-500/30 flex items-start justify-between gap-3 shadow-2xs"
                    >
                      <div className="flex items-start gap-2.5">
                        <button
                          onClick={() => handleToggleStatus(item)}
                          className="mt-0.5 w-5 h-5 rounded-md border-2 border-rose-500 flex items-center justify-center text-white bg-transparent hover:bg-rose-500/20 transition-colors cursor-pointer"
                        >
                          {item.status === 'COMPLETED' && <IconCheck size={14} className="text-rose-500" />}
                        </button>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[var(--text-primary)]">{item.title}</span>
                          </div>
                          {item.description && (
                            <p className="text-[11px] text-[var(--text-secondary)] mt-0.5 line-clamp-2">
                              {item.description}
                            </p>
                          )}
                        </div>
                      </div>

                      {item.action_target && (
                        <button
                          onClick={() => navigate(item.action_target)}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-rose-600 dark:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition-colors flex items-center gap-1 shrink-0 cursor-pointer"
                        >
                          <span>Resolve</span>
                          <IconArrowRight size={12} />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* CATEGORY FILTERS */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
            {CATEGORIES.map((cat) => {
              const isActive = activeCategory === cat;
              const count =
                cat === 'ALL'
                  ? items.length
                  : items.filter((i) => (i.category || 'CUSTOM').toUpperCase() === cat).length;
              if (cat !== 'ALL' && count === 0) return null; // hide empty categories

              return (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shrink-0 flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  <span>{cat}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                      isActive ? 'bg-white/20 text-white' : 'bg-[var(--bg-subtle)] text-[var(--text-muted)]'
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* CHECKLIST ITEMS LIST */}
          {loading ? (
            <div className="flex items-center justify-center p-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 text-center bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] space-y-3">
              <IconChecklist size={36} className="mx-auto text-[var(--text-muted)] opacity-50" />
              <p className="text-xs font-semibold text-[var(--text-secondary)]">No checklist tasks found.</p>
              <button
                onClick={handleGenerate}
                className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold shadow-md hover:bg-blue-700 transition-colors"
              >
                Generate Checklist
              </button>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filteredItems.map((item) => {
                const CatIcon = CATEGORY_ICONS[item.category] || IconFileText;
                const isCompleted = item.status === 'COMPLETED';

                return (
                  <div
                    key={item.id}
                    className={`p-4 rounded-2xl bg-[var(--bg-card)] border transition-all duration-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      isCompleted
                        ? 'border-[var(--border-color)] opacity-60 bg-[var(--bg-subtle)]/50'
                        : 'border-[var(--border-color)] hover:border-blue-500/30 shadow-2xs'
                    }`}
                  >
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      {/* Checkbox */}
                      <button
                        onClick={() => handleToggleStatus(item)}
                        className={`mt-0.5 w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                          isCompleted
                            ? 'bg-emerald-500 border-emerald-500 text-white shadow-xs'
                            : 'border-[var(--border-color)] hover:border-blue-500 bg-[var(--bg-app)]'
                        }`}
                      >
                        {isCompleted && <IconCheck size={14} stroke={3} />}
                      </button>

                      <div className="space-y-1 min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`text-sm font-bold tracking-tight ${
                              isCompleted
                                ? 'line-through text-[var(--text-muted)]'
                                : 'text-[var(--text-primary)]'
                            }`}
                          >
                            {item.title}
                          </span>

                          {/* Category Tag */}
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--bg-subtle)] text-[10px] font-bold text-[var(--text-secondary)] border border-[var(--border-color)]">
                            <CatIcon size={12} />
                            <span>{item.category}</span>
                          </span>

                          {/* Priority Badge */}
                          <span
                            className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold border uppercase tracking-wider ${getPriorityBadgeClass(
                              item.priority
                            )}`}
                          >
                            {item.priority}
                          </span>
                        </div>

                        {item.description && (
                          <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                            {item.description}
                          </p>
                        )}

                        {/* Due Date / Source Metadata */}
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-[var(--text-muted)] pt-0.5 font-medium">
                          {item.due_date && (
                            <span className="flex items-center gap-1">
                              <IconCalendar size={13} />
                              <span>Due {new Date(item.due_date).toLocaleDateString()}</span>
                            </span>
                          )}
                          <span className="uppercase text-[10px] font-bold tracking-wider">
                            Source: {item.source}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* ACTION & CONTROLS */}
                    <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                      {item.action_target && !isCompleted && (
                        <button
                          onClick={() => navigate(item.action_target)}
                          className="px-3 py-1.5 rounded-xl text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 transition-all flex items-center gap-1 cursor-pointer"
                        >
                          <span>Open</span>
                          <IconArrowRight size={14} />
                        </button>
                      )}

                      {!item.is_auto_generated && (
                        <>
                          <button
                            onClick={() => handleStartEdit(item)}
                            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-blue-600 hover:bg-blue-500/10 transition-colors cursor-pointer"
                            title="Edit task"
                          >
                            <IconPencil size={16} />
                          </button>

                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-rose-600 hover:bg-rose-500/10 transition-colors cursor-pointer"
                            title="Delete task"
                          >
                            <IconTrash size={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* CUSTOM TASK MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-extrabold text-[var(--text-primary)] font-heading">
              {editingItem ? 'Edit Task' : 'Add Custom Task'}
            </h3>

            <form onSubmit={handleSubmitCustomTask} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Buy travel insurance policy"
                  className="w-full px-3 py-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1">Description</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Additional details or notes..."
                  className="w-full px-3 py-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs font-semibold text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="URGENT">URGENT</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[var(--text-secondary)] mb-1">Due Date</label>
                  <input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-xs text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-[var(--text-secondary)] bg-[var(--bg-subtle)] hover:text-[var(--text-primary)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20 transition-colors"
                >
                  Save Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
