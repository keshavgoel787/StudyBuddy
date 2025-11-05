'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { Calendar, Clock, Utensils, BookOpen, Bus, Sparkles, LogOut } from 'lucide-react';
import { getDayPlan } from '@/lib/api';

interface Event {
  id: string;
  title: string;
  location?: string;
  start: string;
  end: string;
}

interface TimeSlot {
  start: string;
  end: string;
  label: string;
}

interface Recommendations {
  lunch_slots: TimeSlot[];
  study_slots: TimeSlot[];
  commute_suggestion?: {
    leave_by: string;
    leave_by_label: string;
    reason: string;
  };
  summary: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState('');
  const [events, setEvents] = useState<Event[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendations | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.push('/');
      return;
    }

    loadDayPlan();
  }, [router]);

  const loadDayPlan = async () => {
    try {
      const data = await getDayPlan();
      setEvents(data.events || []);
      setRecommendations(data.recommendations);
      setLoading(false);
    } catch (error: any) {
      console.error('Failed to load day plan:', error);
      alert(`Error loading day plan: ${error.response?.data?.detail || error.message}`);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    router.push('/');
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin text-rose text-6xl">🌸</div>
          <p className="text-xl text-mauve font-serif">Loading your day...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 overflow-hidden">
      {/* Animated flowers */}
      <FloatingFlower initialX={3} initialY={8} color="#FFB3C1" delay={0} />
      <FloatingFlower initialX={92} initialY={12} color="#D4C5E2" delay={1.5} />
      <FloatingFlower initialX={8} initialY={85} color="#C5E1A5" delay={2} />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-5xl font-bold text-rose mb-2">
              Hi there! 🌸
            </h1>
            <p className="text-xl text-mauve font-serif italic">
              Here's your day at a glance
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/notes')}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              My Notes
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/study')}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Upload New
            </Button>
            <Button
              variant="outline"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>

        {/* AI Summary */}
        {recommendations && (
          <Card variant="rose" className="mb-6">
            <div className="flex items-start gap-3">
              <Sparkles className="w-6 h-6 text-rose mt-1" />
              <div>
                <h3 className="text-lg font-semibold mb-2">AI Day Summary</h3>
                <p className="text-foreground/80 leading-relaxed">
                  {recommendations.summary}
                </p>
              </div>
            </div>
          </Card>
        )}

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Today's Events */}
          <Card className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-6 h-6 text-lavender" />
              <h2 className="text-2xl font-semibold">Today's Schedule</h2>
            </div>

            {events.length === 0 ? (
              <p className="text-mauve/70 italic">No events scheduled for today ✨</p>
            ) : (
              <div className="space-y-3">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="p-4 bg-soft-pink/30 rounded-xl border border-rose/20"
                  >
                    <h3 className="font-semibold text-foreground">{event.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-mauve mt-1">
                      <Clock className="w-4 h-4" />
                      <span>
                        {formatTime(event.start)} - {formatTime(event.end)}
                      </span>
                    </div>
                    {event.location && (
                      <p className="text-sm text-mauve/70 mt-1">📍 {event.location}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Recommendations */}
          <div className="space-y-4">
            {/* Lunch */}
            {recommendations?.lunch_slots && recommendations.lunch_slots.length > 0 && (
              <Card variant="peach">
                <div className="flex items-center gap-2 mb-3">
                  <Utensils className="w-6 h-6 text-peach" />
                  <h3 className="text-xl font-semibold">Lunch Time 🍱</h3>
                </div>
                {recommendations.lunch_slots.map((slot, idx) => (
                  <div key={idx} className="text-foreground/80">
                    {slot.label}
                  </div>
                ))}
              </Card>
            )}

            {/* Study */}
            {recommendations?.study_slots && recommendations.study_slots.length > 0 && (
              <Card variant="lavender">
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="w-6 h-6 text-lavender" />
                  <h3 className="text-xl font-semibold">Study Time 📚</h3>
                </div>
                {recommendations.study_slots.map((slot, idx) => (
                  <div key={idx} className="text-foreground/80">
                    {slot.label}
                  </div>
                ))}
              </Card>
            )}

            {/* Commute */}
            {recommendations?.commute_suggestion && (
              <Card variant="sage">
                <div className="flex items-center gap-2 mb-3">
                  <Bus className="w-6 h-6 text-sage" />
                  <h3 className="text-xl font-semibold">Head Home 🚌</h3>
                </div>
                <p className="text-foreground/80">
                  Leave by: {recommendations.commute_suggestion.leave_by_label}
                </p>
                <p className="text-sm text-mauve/70 mt-1">
                  {recommendations.commute_suggestion.reason}
                </p>
              </Card>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <Card className="text-center">
          <p className="text-mauve font-serif italic mb-4">
            Ready to study? Upload your notes and let AI help you ace your exams! ✨
          </p>
          <Button
            variant="primary"
            size="lg"
            onClick={() => router.push('/study')}
          >
            Go to Study Buddy 🌸
          </Button>
        </Card>
      </div>
    </div>
  );
}
