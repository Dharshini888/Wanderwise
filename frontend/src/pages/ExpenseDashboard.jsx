import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  IconPlus, IconDownload, IconFileSpreadsheet, IconFileTypePdf,
  IconArrowLeft, IconSparkles, IconMapPin, IconCalendar
} from '@tabler/icons-react';

import ExpenseSummary from '../components/expenses/ExpenseSummary';
import BudgetProgress from '../components/expenses/BudgetProgress';
import AIExpenseInsights from '../components/expenses/AIExpenseInsights';
import ExpensePieChart from '../components/expenses/ExpensePieChart';
import MerchantLeaderboard from '../components/expenses/MerchantLeaderboard';
import SpendingHeatmap from '../components/expenses/SpendingHeatmap';
import ExpenseFilters from '../components/expenses/ExpenseFilters';
import ExpenseTimeline from '../components/expenses/ExpenseTimeline';
import AddExpenseModal from '../components/expenses/AddExpenseModal';

import {
  getTripExpenses, getTripBudget, getExpenseAnalytics, getAIExpenseInsights,
  createExpense, updateExpense, deleteExpense, getExportCsvUrl, getExportPdfUrl
} from '../api/expenses';
import { getTripDetails } from '../api/trips';

export default function ExpenseDashboard({ overrideTripId }) {
  const routeParams = useParams() || {};
  const tripId = overrideTripId || routeParams.tripId;
  const navigate = useNavigate();


  const [trip, setTrip] = useState(null);
  const [budget, setBudget] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);

  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [sourceFilter, setSourceFilter] = useState('All');

  const loadData = async () => {
    if (!tripId) return;
    try {
      const [tData, bData, eData, aData, iData] = await Promise.all([

        getTripDetails(tripId).catch(() => null),
        getTripBudget(tripId).catch(() => null),
        getTripExpenses(tripId).catch(() => []),
        getExpenseAnalytics(tripId).catch(() => null),
        getAIExpenseInsights(tripId).catch(() => null),
      ]);

      if (tData) setTrip(tData);
      if (bData) setBudget(bData);
      if (Array.isArray(eData)) setExpenses(eData);
      if (aData) setAnalytics(aData);
      if (iData) setInsights(iData);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [tripId]);

  const handleSaveExpense = async (payload) => {
    if (editingExpense) {
      await updateExpense(editingExpense.id, payload);
    } else {
      await createExpense({ ...payload, trip_id: Number(tripId) });
    }
    setEditingExpense(null);
    loadData();
  };

  const handleEditClick = (expense) => {
    setEditingExpense(expense);
    setShowModal(true);
  };

  const handleDeleteClick = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense record?')) return;
    await deleteExpense(id);
    loadData();
  };

  // Filtered expenses list
  const filteredExpenses = expenses.filter((e) => {
    if (categoryFilter !== 'All' && e.category !== categoryFilter) return false;
    if (sourceFilter !== 'All' && e.expense_source !== sourceFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const titleMatch = (e.title || '').toLowerCase().includes(q);
      const locMatch = (e.location_name || '').toLowerCase().includes(q);
      const notesMatch = (e.notes || '').toLowerCase().includes(q);
      if (!titleMatch && !locMatch && !notesMatch) return false;
    }
    return true;
  });

  const currency = budget?.currency || trip?.currency || 'USD';

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-gray-500 font-semibold">Loading Expense Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl">
        <div className="space-y-1">
          <button
            onClick={() => navigate('/companion')}
            className="text-xs font-bold text-blue-200 hover:underline flex items-center gap-1 mb-2"
          >
            <IconArrowLeft size={16} /> Back to Trips
          </button>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-200">
            <IconSparkles size={16} /> WanderWise v2.1 Expense & Budget Manager
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading">
            {trip?.destination ? `${trip.destination} Spending` : 'Trip Expense Dashboard'}
          </h1>
          <p className="text-xs sm:text-sm text-blue-100 font-medium flex items-center gap-3">
            <span className="flex items-center gap-1"><IconMapPin size={14} /> {trip?.destination}</span>
            <span className="flex items-center gap-1"><IconCalendar size={14} /> {trip?.start_date} to {trip?.end_date}</span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <a
            href={getExportCsvUrl(tripId)}
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-bold text-xs flex items-center gap-1.5 transition-all"
          >
            <IconFileSpreadsheet size={16} /> Export CSV
          </a>

          <a
            href={getExportPdfUrl(tripId)}
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white font-bold text-xs flex items-center gap-1.5 transition-all"
          >
            <IconFileTypePdf size={16} /> Export PDF

          </a>

          <button
            onClick={() => { setEditingExpense(null); setShowModal(true); }}
            className="px-4 py-2.5 rounded-xl bg-white text-blue-600 hover:bg-blue-50 font-extrabold text-xs flex items-center gap-1.5 shadow-lg transition-all"
          >
            <IconPlus size={18} /> Add Expense
          </button>
        </div>
      </div>

      {/* Expense Metrics Summary Cards */}
      <ExpenseSummary budget={budget} analytics={analytics} insights={insights} />

      {/* Main Grid: Left analytics/charts, Right AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <BudgetProgress budget={budget} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <ExpensePieChart breakdown={analytics?.category_breakdown} currency={currency} />
            <MerchantLeaderboard merchants={analytics?.top_merchants} currency={currency} />
          </div>
          <SpendingHeatmap heatmap={analytics?.spending_heatmap} currency={currency} />
        </div>

        <div>
          <AIExpenseInsights insights={insights} currency={currency} />
        </div>
      </div>

      {/* Timeline & Filter Section */}
      <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-extrabold text-gray-900 dark:text-white font-heading">
            Expense Log & Timeline ({filteredExpenses.length})
          </h2>
        </div>

        <ExpenseFilters
          search={search}
          onSearchChange={setSearch}
          category={categoryFilter}
          onCategoryChange={setCategoryFilter}
          source={sourceFilter}
          onSourceChange={setSourceFilter}
        />

        <ExpenseTimeline
          expenses={filteredExpenses}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
        />
      </div>

      {/* Add / Edit Expense Modal */}
      <AddExpenseModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditingExpense(null); }}
        onSubmit={handleSaveExpense}
        initialData={editingExpense}
        defaultCurrency={currency}
      />
    </div>
  );
}
