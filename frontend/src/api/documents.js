import api from './axios';

export const getDocuments = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.category && params.category !== 'All') queryParams.append('category', params.category);
  if (params.status && params.status !== 'All') queryParams.append('status', params.status);
  if (params.tripId !== undefined && params.tripId !== null && params.tripId !== 'All') {
    queryParams.append('trip_id', params.tripId);
  }
  if (params.search) queryParams.append('search', params.search);
  if (params.sortBy) queryParams.append('sort_by', params.sortBy);

  const res = await api.get(`/api/documents?${queryParams.toString()}`);
  return res.data;
};

export const getDocumentStats = async () => {
  const res = await api.get('/api/documents/stats');
  return res.data;
};

export const getDocumentDetails = async (id) => {
  const res = await api.get(`/api/documents/${id}`);
  return res.data;
};

export const uploadDocument = async (formData, onProgress) => {
  const res = await api.post('/api/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    }
  });
  return res.data;
};

export const updateDocument = async (id, data) => {
  const res = await api.put(`/api/documents/${id}`, data);
  return res.data;
};

export const deleteDocument = async (id) => {
  const res = await api.delete(`/api/documents/${id}`);
  return res.data;
};

export const analyzeDocument = async (id) => {
  const res = await api.post(`/api/documents/${id}/analyze`);
  return res.data;
};

export const downloadDocumentFile = async (id, fileName = 'document.pdf', disposition = 'attachment') => {
  const token = localStorage.getItem('token');
  const response = await api.get(`/api/documents/${id}/download?disposition=${disposition}`, {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (disposition === 'inline') {
    return URL.createObjectURL(response.data);
  }

  const url = window.URL.createObjectURL(new Blob([response.data], { type: response.headers['content-type'] }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};
