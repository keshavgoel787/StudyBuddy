import axios from 'axios';
import { apiCache, withCache } from './apiCache';

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
export const getDayPlan = async (forceRefresh: boolean = false) => {
  // If force refresh, invalidate cache and bypass it
  if (forceRefresh) {
    apiCache.invalidate('calendar:day-plan');
    const response = await api.get('/calendar/day-plan', {
      params: { force_refresh: true }
    });
    return response.data;
  }

  // Otherwise use cache (30 minutes)
  return withCache('calendar:day-plan', async () => {
    const response = await api.get('/calendar/day-plan');
    return response.data;
  }, 30 * 60 * 1000);
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

  const response = await api.post('/notes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const generateStudyMaterial = async (noteDocumentId: string, topicHint?: string) => {
  const response = await api.post('/notes/generate-study', {
    note_document_id: noteDocumentId,
    topic_hint: topicHint || null,
  });
  return response.data;
};

export const getStudyMaterial = async (noteDocumentId: string) => {
  // Cache study material for 1 hour (rarely changes unless regenerated)
  return withCache(`notes:${noteDocumentId}:study`, async () => {
    const response = await api.get(`/notes/${noteDocumentId}/study`);
    return response.data;
  }, 60 * 60 * 1000);
};

export const getAllNotes = async () => {
  // Cache notes list for 2 minutes
  return withCache('notes:all', async () => {
    const response = await api.get('/notes/');
    return response.data;
  }, 2 * 60 * 1000);
};

export const deleteNote = async (noteDocumentId: string) => {
  const response = await api.delete(`/notes/${noteDocumentId}`);
  // Invalidate cache after deletion
  apiCache.invalidate('notes:all');
  apiCache.invalidate(`notes:${noteDocumentId}:study`);
  return response.data;
};

// Invalidate cache after new note upload
export const invalidateNotesCache = () => {
  apiCache.invalidatePattern(/^notes:/);
};
