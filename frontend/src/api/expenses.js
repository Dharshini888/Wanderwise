import api from './axios';

export const createExpense = async (data) => {
  const res = await api.post('/api/expenses', data);
  return res.data;
};

export const getTripExpenses = async (tripId) => {
  const res = await api.get(`/api/expenses/trip/${tripId}`);
  return res.data;
};

export const getExpenseAnalytics = async (tripId) => {
  const res = await api.get(`/api/expenses/analytics/${tripId}`);
  return res.data;
};

export const getTripBudget = async (tripId) => {
  const res = await api.get(`/api/expenses/budget/${tripId}`);
  return res.data;
};

export const getAIExpenseInsights = async (tripId) => {
  const res = await api.get(`/api/expenses/${tripId}/insights`);
  return res.data;
};

export const uploadReceiptOCR = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/api/expenses/ocr', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const updateExpense = async (id, data) => {
  const res = await api.put(`/api/expenses/${id}`, data);
  return res.data;
};

export const deleteExpense = async (id) => {
  const res = await api.delete(`/api/expenses/${id}`);
  return res.data;
};

export const getExportCsvUrl = (tripId) => `http://localhost:8000/api/expenses/export/csv?trip_id=${tripId}`;
export const getExportPdfUrl = (tripId) => `http://localhost:8000/api/expenses/export/pdf?trip_id=${tripId}`;
