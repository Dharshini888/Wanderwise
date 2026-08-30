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

export const downloadExpenseExport = async (tripId, type) => {
  const endpoint = type === 'csv' ? `/api/expenses/${tripId}/export/csv` : `/api/expenses/${tripId}/export/pdf`;
  const res = await api.get(endpoint, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `expenses_trip_${tripId}.${type}`);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
};
