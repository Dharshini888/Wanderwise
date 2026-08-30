import api from './axios';

export const searchGuideDestination = async (destination) => {
  const res = await api.get('/api/guide/search', { params: { destination } });
  return res.data;
};

export const getNearbyGuidePlaces = async ({ lat, lon, radius = 3000, category = 'ALL', query = '', destination = '' }) => {
  const params = { lat, lon, radius, category };
  if (query && typeof query === 'string' && query.trim()) params.query = query.trim();
  if (destination && typeof destination === 'string' && destination.trim()) params.destination = destination.trim();
  const res = await api.get('/api/guide/nearby', { params });
  return res.data;
};

export const getGuideCategories = async () => {
  const res = await api.get('/api/guide/categories');
  return res.data;
};

export const getPlaceDetails = async (placeId, lat, lon) => {
  const params = {};
  if (lat) params.lat = lat;
  if (lon) params.lon = lon;
  const res = await api.get(`/api/guide/place/${placeId}`, { params });
  return res.data;
};

export const getPlaceRoute = async ({ originLat, originLon, destLat, destLon, mode = 'walking' }) => {
  const params = {
    origin_lat: originLat,
    origin_lon: originLon,
    dest_lat: destLat,
    dest_lon: destLon,
    mode,
  };
  const res = await api.get('/api/guide/route', { params });
  return res.data;
};
