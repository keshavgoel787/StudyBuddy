'use client';

import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  submessage?: string;
}

export function LoadingSpinner({ message, submessage }: LoadingSpinnerProps) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="w-16 h-16 text-rose animate-spin mx-auto" />
        {message && (
          <p className="text-xl text-mauve font-serif">
            {message}
          </p>
        )}
        {submessage && (
          <p className="text-sm text-mauve/70">
            {submessage}
          </p>
        )}
      </div>
    </div>
  );
}
