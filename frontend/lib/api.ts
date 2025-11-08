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

// Assignments
export interface AssignmentCreate {
  title: string;
  description?: string;
  assignment_type?: string;
  due_date: string; // ISO datetime string
  estimated_hours?: number;
  priority?: number; // 1=low, 2=medium, 3=high
}

export interface AssignmentUpdate {
  title?: string;
  description?: string;
  assignment_type?: string;
  due_date?: string;
  estimated_hours?: number;
  priority?: number;
  completed?: boolean;
}

export interface Assignment {
  id: number;
  user_id: string;
  title: string;
  description?: string;
  assignment_type?: string;
  due_date: string;
  estimated_hours?: number;
  priority: number;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

export const getAssignments = async (includeCompleted: boolean = false): Promise<Assignment[]> => {
  // Cache assignments for 2 minutes
  return withCache(`assignments:${includeCompleted}`, async () => {
    const response = await api.get('/assignments', {
      params: { include_completed: includeCompleted }
    });
    return response.data;
  }, 2 * 60 * 1000);
};

export const createAssignment = async (assignment: AssignmentCreate): Promise<Assignment> => {
  const response = await api.post('/assignments', assignment);
  // Invalidate cache after creation
  apiCache.invalidatePattern(/^assignments:/);
  return response.data;
};

export const updateAssignment = async (id: number, update: AssignmentUpdate): Promise<Assignment> => {
  const response = await api.patch(`/assignments/${id}`, update);
  // Invalidate cache after update
  apiCache.invalidatePattern(/^assignments:/);
  return response.data;
};

export const deleteAssignment = async (id: number): Promise<void> => {
  await api.delete(`/assignments/${id}`);
  // Invalidate cache after deletion
  apiCache.invalidatePattern(/^assignments:/);
  // Also invalidate calendar cache since assignment blocks may have changed
  apiCache.invalidate('calendar:day-plan');
};

// Google Calendar Event Sync
export interface EventSyncResponse {
  event_id: string;
  message: string;
}

export const syncAssignmentBlockToCalendar = async (
  assignmentId: number,
  startTime: string,
  endTime: string
): Promise<EventSyncResponse> => {
  const response = await api.post('/calendar/events/sync-assignment-block', {
    assignment_id: assignmentId,
    start_time: startTime,
    end_time: endTime
  });
  // Invalidate calendar cache after sync
  apiCache.invalidate('calendar:day-plan');
  return response.data;
};

export const syncBusToCalendar = async (
  direction: 'outbound' | 'inbound',
  departureTime: string,
  arrivalTime: string
): Promise<EventSyncResponse> => {
  const response = await api.post('/calendar/events/sync-bus', {
    direction,
    departure_time: departureTime,
    arrival_time: arrivalTime
  });
  // Invalidate calendar cache after sync
  apiCache.invalidate('calendar:day-plan');
  return response.data;
};

export interface CustomEventCreate {
  title: string;
  start_time: string;
  end_time: string;
  description?: string;
  location?: string;
  color_id?: string; // 1-11 Google Calendar color IDs
}

export const createCustomEvent = async (event: CustomEventCreate): Promise<EventSyncResponse> => {
  const response = await api.post('/calendar/events/create', event);
  // Invalidate calendar cache after creation
  apiCache.invalidate('calendar:day-plan');
  return response.data;
};

export const deleteCalendarEvent = async (eventId: string): Promise<void> => {
  await api.delete(`/calendar/events/${eventId}`);
  // Invalidate calendar cache after deletion
  apiCache.invalidate('calendar:day-plan');
};
