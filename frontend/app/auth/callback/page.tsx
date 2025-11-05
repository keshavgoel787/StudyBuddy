'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');

    if (token) {
      // Store token in localStorage
      localStorage.setItem('auth_token', token);

      // Redirect to dashboard
      router.push('/dashboard');
    } else {
      // No token, redirect back to home
      router.push('/');
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 text-rose animate-spin mx-auto" />
        <p className="text-xl text-mauve font-serif">
          Signing you in... ✨
        </p>
      </div>
    </div>
  );
}
