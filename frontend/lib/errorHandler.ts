import axios from 'axios';

/**
 * Centralized error handler for API errors
 */
export function handleApiError(error: unknown, fallbackMessage = 'An error occurred'): string {
  if (axios.isAxiosError(error)) {
    // Check for response error
    if (error.response) {
      const detail = error.response.data?.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (Array.isArray(detail)) {
        // FastAPI validation errors
        return detail.map(err => err.msg).join(', ');
      }
      return error.response.statusText || fallbackMessage;
    }
    // Network error
    if (error.request) {
      return 'Network error. Please check your connection.';
    }
  }

  // Generic error
  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

/**
 * Show error alert with proper message extraction
 */
export function showErrorAlert(error: unknown, fallbackMessage?: string) {
  const message = handleApiError(error, fallbackMessage);
  alert(message);
}

/**
 * Log error for debugging
 */
export function logError(context: string, error: unknown) {
  console.error(`[${context}]`, error);
}
