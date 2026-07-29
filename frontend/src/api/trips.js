import api from './axios';

export const checkTripBudget = async (params) => {
  const res = await api.post('/api/trips/check-budget', null, { params });
  return res.data;
};

export const createTrip = async (data) => {
  const res = await api.post('/api/trips/create', data);
  return res.data;
};

export const getUserTrips = async (userId) => {
  const res = await api.get(`/api/trips/user/${userId}`);
  return res.data;
};

export const getTripDetails = async (tripId) => {
  const res = await api.get(`/api/trips/${tripId}`);
  return res.data;
};

export const updateTrip = async (tripId, data) => {
  const res = await api.put(`/api/trips/${tripId}`, data);
  return res.data;
};

export const deleteTrip = async (tripId) => {
  const res = await api.delete(`/api/trips/${tripId}`);
  return res.data;
};

export const duplicateTrip = async (tripId, userId) => {
  const res = await api.post(`/api/trips/${tripId}/duplicate?user_id=${userId}`);
  return res.data;
};

export const archiveTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/archive`);
  return res.data;
};

export const restoreTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/restore`);
  return res.data;
};

export const toggleFavoriteTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/favorite`);
  return res.data;
};

export const completeTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/complete`);
  return res.data;
};

export const cancelTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/cancel`);
  return res.data;
};

export const shareTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/share`);
  return res.data;
};

export const generateItinerary = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/generate-itinerary`);
  return res.data;
};

export const regenerateDay = async (tripId, dayNumber, notes = '') => {
  const res = await api.post(`/api/trips/${tripId}/regenerate-day`, { day_number: dayNumber, notes });
  return res.data;
};

export const searchTrips = async (userId, query) => {
  const res = await api.get('/api/trips/search', { params: { user_id: userId, query } });
  return res.data;
};

export const filterTrips = async (userId, filters = {}) => {
  const res = await api.get('/api/trips/filter', { params: { user_id: userId, ...filters } });
  return res.data;
};

export const getDashboardWidgets = async (userId) => {
  const res = await api.get(`/api/trips/dashboard-widgets/${userId}`);
  return res.data;
};

export const toggleActivityLock = async (activityId) => {
  const res = await api.put(`/api/trips/activities/${activityId}/lock`);
  return res.data;
};

export const deleteActivity = async (activityId) => {
  const res = await api.delete(`/api/trips/activities/${activityId}`);
  return res.data;
};

export const fetchCurrencyRegistry = async () => {
  const res = await api.get('/api/currency/registry');
  return res;
};


export const reorderActivity = async (tripId, payload) => {
  const res = await api.put(`/api/trips/${tripId}/activities/reorder`, payload);
  return res.data;
};

export const addCustomActivity = async (tripId, payload) => {
  const res = await api.post(`/api/trips/${tripId}/activities/add`, payload);
  return res.data;
};

export const getTripStats = async (userId) => {
  const res = await api.get('/api/trips/stats', { params: { user_id: userId } });
  return res.data;
};

export const getActiveTripSpotlight = async (userId) => {
  const res = await api.get('/api/trips/spotlight', { params: { user_id: userId } });
  return res.data;
};

export const getRecentlyViewedTrip = async (userId) => {
  const res = await api.get('/api/trips/recently-viewed', { params: { user_id: userId } });
  return res.data;
};

export const touchTrip = async (tripId) => {
  const res = await api.post(`/api/trips/${tripId}/touch`);
  return res.data;
};

export const checkDuplicateTrip = async (destination, startDate) => {
  const res = await api.post('/api/trips/check-duplicate', { destination, start_date: startDate });
  return res.data;
};

export const getPaginatedTrips = async (params = {}) => {
  const res = await api.get('/api/trips', { params });
  return res.data;
};
