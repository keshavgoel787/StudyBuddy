import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

// Auth
export const initiateGoogleAuth = () => {
  window.location.href = `${API_URL}/auth/google`;
};

// Calendar
export const getTodayEvents = async () => {
  const response = await api.get('/calendar/today');
  return response.data;
};

export const getDayPlan = async () => {
  const response = await api.get('/calendar/day-plan');
  return response.data;
};

// Notes
export const uploadNote = async (formData: FormData) => {
  const response = await api.post('/notes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const uploadTextNote = async (text: string, title: string) => {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('title', title);

  const response = await api.post('/notes/upload', formData);
  return response.data;
};

export const generateStudyMaterial = async (noteDocumentId: string) => {
  const response = await api.post('/notes/generate-study', {
    note_document_id: noteDocumentId,
  });
  return response.data;
};

export const getStudyMaterial = async (noteDocumentId: string) => {
  const response = await api.get(`/notes/${noteDocumentId}/study`);
  return response.data;
};
