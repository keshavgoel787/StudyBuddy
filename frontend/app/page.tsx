'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { Heart, Calendar, BookOpen, Sparkles } from 'lucide-react';
import { initiateGoogleAuth } from '@/lib/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 overflow-hidden">
      {/* Animated floating flowers */}
      <FloatingFlower initialX={5} initialY={10} color="#FFB3C1" delay={0} />
      <FloatingFlower initialX={90} initialY={15} color="#D4C5E2" delay={1} />
      <FloatingFlower initialX={10} initialY={75} color="#FFD4B2" delay={2} />
      <FloatingFlower initialX={85} initialY={80} color="#C5E1A5" delay={1.5} />
      <FloatingFlower initialX={50} initialY={5} color="#E8B4B8" delay={0.5} />
      <FloatingFlower initialX={95} initialY={50} color="#B8D8E8" delay={2.5} />

      <div className="max-w-4xl w-full space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-rose" />
            <h1 className="text-6xl font-bold bg-linear-to-r from-rose via-lavender to-powder-blue bg-clip-text text-transparent">
              SchoolBuddy
            </h1>
            <Sparkles className="w-10 h-10 text-lavender" />
          </div>
          <p className="text-2xl text-mauve font-serif italic">
            Your personal study companion & day planner ✨
          </p>
          <div className="flex items-center justify-center gap-2 text-dusty-rose">
            <Heart className="w-5 h-5 fill-current" />
            <p className="text-sm">Made with love for a special pre-med student</p>
            <Heart className="w-5 h-5 fill-current" />
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card variant="rose" className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-white/60 rounded-full">
                <Calendar className="w-8 h-8 text-rose" />
              </div>
              <h2 className="text-2xl font-semibold">Day Planner AI</h2>
            </div>
            <p className="text-foreground/80 leading-relaxed">
              Syncs with your Google Calendar to suggest perfect times for lunch,
              study sessions, and when to head home. Never miss a moment! 🍱📚
            </p>
          </Card>

          <Card variant="lavender" className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-white/60 rounded-full">
                <BookOpen className="w-8 h-8 text-lavender" />
              </div>
              <h2 className="text-2xl font-semibold">Study Buddy AI</h2>
            </div>
            <p className="text-foreground/80 leading-relaxed">
              Upload handwritten notes or paste text to generate summaries,
              flashcards, and practice questions. Biochem just got easier! 🧬✨
            </p>
          </Card>
        </div>

        {/* CTA */}
        <div className="text-center space-y-4">
          <Button
            variant="primary"
            size="lg"
            onClick={initiateGoogleAuth}
            className="text-xl px-12"
          >
            Sign in with Google 🌸
          </Button>
          <p className="text-sm text-mauve/80">
            We'll need access to your Google Calendar to help plan your day
          </p>
        </div>

        {/* Decorative quote */}
        <Card className="text-center border-dusty-rose/30">
          <p className="text-lg font-serif italic text-mauve">
            "Success is the sum of small efforts repeated day in and day out."
          </p>
          <p className="text-sm text-foreground/60 mt-2">— Robert Collier</p>
        </Card>
      </div>
    </div>
  );
}
