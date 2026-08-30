import api from './axios';

export const getChecklist = async (tripId) => {
  const response = await api.get(`/api/checklist/${tripId}`);
  return response.data;
};

export const createChecklistItem = async (tripId, data) => {
  const response = await api.post(`/api/checklist/${tripId}`, data);
  return response.data;
};

export const updateChecklistItem = async (itemId, data) => {
  const response = await api.patch(`/api/checklist/${itemId}`, data);
  return response.data;
};

export const deleteChecklistItem = async (itemId) => {
  const response = await api.delete(`/api/checklist/${itemId}`);
  return response.data;
};

export const generateChecklist = async (tripId) => {
  const response = await api.post(`/api/checklist/${tripId}/generate`);
  return response.data;
};
