'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { EventCalendar } from '@/components/EventCalendar';
import { Calendar, Clock, Utensils, BookOpen, Bus, Sparkles, LogOut, RefreshCw, CheckSquare, Plus, Trash2, Circle, CheckCircle2, CalendarPlus, List, CalendarDays } from 'lucide-react';
import { getDayPlan, getAssignments, createAssignment, updateAssignment, deleteAssignment, syncAssignmentBlockToCalendar, syncBusToCalendar, createCustomEvent, deleteCalendarEvent, Assignment, AssignmentCreate, CustomEventCreate } from '@/lib/api';
import '../calendar.css';

interface Event {
  id: string;
  title: string;
  location?: string;
  start: string;
  end: string;
  description?: string;
  event_type?: string; // "calendar" | "commute" | "assignment"
}

interface TimeSlot {
  start: string;
  end: string;
  label: string;
}

interface BusSuggestion {
  direction: string;
  departure_time: string;
  arrival_time: string;
  departure_label: string;
  arrival_label: string;
  reason: string;
  is_late_night: boolean;
}

interface Recommendations {
  lunch_slots: TimeSlot[];
  study_slots: TimeSlot[];
  commute_suggestion?: {
    leave_by: string;
    leave_by_label: string;
    reason: string;
  };
  bus_suggestions?: {
    morning?: BusSuggestion;
    evening?: BusSuggestion;
  };
  summary: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [userName, setUserName] = useState('');
  const [events, setEvents] = useState<Event[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendations | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [showNewAssignmentForm, setShowNewAssignmentForm] = useState(false);
  const [newAssignment, setNewAssignment] = useState({
    title: '',
    description: '',
    assignment_type: '',
    due_date: '',
    estimated_hours: '',
    priority: 2
  });
  const [syncedEvents, setSyncedEvents] = useState<Set<string>>(new Set());
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error'} | null>(null);
  const [showCreateEventModal, setShowCreateEventModal] = useState(false);
  const [newEvent, setNewEvent] = useState<CustomEventCreate>({
    title: '',
    start_time: '',
    end_time: '',
    description: '',
    location: '',
    color_id: '9' // Default to blue
  });
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('calendar');

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      router.push('/');
      return;
    }

    loadDayPlan();
    loadAssignments();
  }, [router]);

  const loadDayPlan = async (forceRefresh: boolean = false) => {
    try {
      const data = await getDayPlan(forceRefresh);
      setEvents(data.events || []);
      setRecommendations(data.recommendations);
      setLoading(false);
      setRefreshing(false);
    } catch (error: any) {
      console.error('Failed to load day plan:', error);
      alert(`Error loading day plan: ${error.response?.data?.detail || error.message}`);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDayPlan(true); // Force refresh when button is clicked
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    router.push('/');
  };

  const loadAssignments = async () => {
    try {
      const data = await getAssignments(false);
      setAssignments(data);
    } catch (error: any) {
      console.error('Failed to load assignments:', error);
    }
  };

  const handleCreateAssignment = async () => {
    if (!newAssignment.title || !newAssignment.due_date) {
      alert('Please fill in title and due date');
      return;
    }

    try {
      const assignmentData: AssignmentCreate = {
        title: newAssignment.title,
        description: newAssignment.description || undefined,
        assignment_type: newAssignment.assignment_type || undefined,
        due_date: new Date(newAssignment.due_date).toISOString(),
        estimated_hours: newAssignment.estimated_hours ? parseFloat(newAssignment.estimated_hours) : undefined,
        priority: newAssignment.priority
      };

      await createAssignment(assignmentData);
      setNewAssignment({
        title: '',
        description: '',
        assignment_type: '',
        due_date: '',
        estimated_hours: '',
        priority: 2
      });
      setShowNewAssignmentForm(false);
      loadAssignments();
    } catch (error: any) {
      alert(`Failed to create assignment: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleToggleComplete = async (assignment: Assignment) => {
    try {
      await updateAssignment(assignment.id, { completed: !assignment.completed });
      loadAssignments();
    } catch (error: any) {
      alert(`Failed to update assignment: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteAssignment = async (id: number) => {
    if (!confirm('Are you sure you want to delete this assignment?')) {
      return;
    }

    try {
      await deleteAssignment(id);
      loadAssignments();
    } catch (error: any) {
      alert(`Failed to delete assignment: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 3: return 'text-red-600';
      case 2: return 'text-yellow-600';
      case 1: return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 3: return 'High';
      case 2: return 'Medium';
      case 1: return 'Low';
      default: return 'Unknown';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  };

  const showNotification = (message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000); // Auto-hide after 5 seconds
  };

  const handleSyncAssignmentBlock = async (event: Event) => {
    const eventKey = `assignment-${event.id}`;
    if (syncedEvents.has(eventKey)) {
      showNotification('This assignment block is already synced to your calendar', 'error');
      return;
    }

    try {
      // Extract assignment ID from event.id (format: "assignment-{id}-{index}")
      const assignmentIdMatch = event.id.match(/assignment-(\d+)-/);
      if (!assignmentIdMatch) {
        throw new Error('Invalid assignment block ID');
      }
      const assignmentId = parseInt(assignmentIdMatch[1]);

      await syncAssignmentBlockToCalendar(assignmentId, event.start, event.end);
      setSyncedEvents(prev => new Set(prev).add(eventKey));
      showNotification(`Study block "${event.title}" added to Google Calendar!`, 'success');

      // Auto-refresh dashboard to show synced event (lightweight - no AI regeneration)
      setRefreshing(true);
      await loadDayPlan(false);
    } catch (error: any) {
      console.error('Failed to sync assignment block:', error);
      showNotification(
        `Failed to sync: ${error.response?.data?.detail || error.message}`,
        'error'
      );
    }
  };

  const handleSyncBus = async (busSuggestion: BusSuggestion) => {
    const eventKey = `bus-${busSuggestion.direction}`;
    if (syncedEvents.has(eventKey)) {
      showNotification('This bus time is already synced to your calendar', 'error');
      return;
    }

    try {
      await syncBusToCalendar(
        busSuggestion.direction as 'outbound' | 'inbound',
        busSuggestion.departure_time,
        busSuggestion.arrival_time
      );
      setSyncedEvents(prev => new Set(prev).add(eventKey));
      showNotification(
        `${busSuggestion.direction === 'outbound' ? 'Morning' : 'Evening'} bus added to Google Calendar!`,
        'success'
      );

      // Auto-refresh dashboard to show synced event (lightweight - no AI regeneration)
      setRefreshing(true);
      await loadDayPlan(false);
    } catch (error: any) {
      console.error('Failed to sync bus:', error);
      showNotification(
        `Failed to sync bus: ${error.response?.data?.detail || error.message}`,
        'error'
      );
    }
  };

  const handleCreateEvent = async () => {
    // Validation
    if (!newEvent.title.trim()) {
      showNotification('Please enter an event title', 'error');
      return;
    }
    if (!newEvent.start_time || !newEvent.end_time) {
      showNotification('Please select start and end times', 'error');
      return;
    }

    // Convert datetime-local format to ISO with timezone
    const formatDateTime = (datetime: string) => {
      if (!datetime) return '';
      // datetime-local gives "2025-11-07T14:30", we need to add seconds and timezone
      return datetime.includes('T') ? `${datetime}:00` : datetime;
    };

    try {
      const eventToCreate = {
        ...newEvent,
        start_time: formatDateTime(newEvent.start_time),
        end_time: formatDateTime(newEvent.end_time)
      };

      await createCustomEvent(eventToCreate);
      showNotification(`Event "${newEvent.title}" created in Google Calendar!`, 'success');

      // Reset form and close modal
      setNewEvent({
        title: '',
        start_time: '',
        end_time: '',
        description: '',
        location: '',
        color_id: '9'
      });
      setShowCreateEventModal(false);

      // Refresh day plan to show new event (lightweight - no AI regeneration)
      setRefreshing(true);
      await loadDayPlan(false);
    } catch (error: any) {
      console.error('Failed to create event:', error);
      showNotification(
        `Failed to create event: ${error.response?.data?.detail || error.message}`,
        'error'
      );
    }
  };

  const handleDeleteEvent = async (event: Event) => {
    // Confirmation dialog
    if (!confirm(`Delete "${event.title}" from Google Calendar?`)) {
      return;
    }

    try {
      await deleteCalendarEvent(event.id);
      showNotification(`Event "${event.title}" deleted from calendar`, 'success');

      // Remove from synced events if it was synced
      setSyncedEvents(prev => {
        const newSet = new Set(prev);
        newSet.delete(event.id);
        return newSet;
      });

      // Refresh day plan to show updated schedule (lightweight - no AI regeneration)
      setRefreshing(true);
      await loadDayPlan(false);
    } catch (error: any) {
      console.error('Failed to delete event:', error);
      showNotification(
        `Failed to delete event: ${error.response?.data?.detail || error.message}`,
        'error'
      );
    }
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

      {/* Notification Toast */}
      {notification && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right">
          <div className={`px-6 py-4 rounded-xl shadow-lg border backdrop-blur-sm ${
            notification.type === 'success'
              ? 'bg-green-50/90 border-green-300 text-green-800'
              : 'bg-red-50/90 border-red-300 text-red-800'
          }`}>
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {notification.type === 'success' ? '✓' : '✕'}
              </span>
              <p className="font-medium">{notification.message}</p>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-5xl font-bold text-rose mb-2">
              Hi there! 🌸
            </h1>
            <p className="text-xl text-mauve font-serif italic">
              {new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
              })}
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="primary"
              onClick={() => setViewMode(viewMode === 'list' ? 'calendar' : 'list')}
            >
              {viewMode === 'list' ? (
                <>
                  <CalendarDays className="w-4 h-4 mr-2" />
                  Calendar View
                </>
              ) : (
                <>
                  <List className="w-4 h-4 mr-2" />
                  List View
                </>
              )}
            </Button>
            <Button
              variant="primary"
              onClick={() => setShowCreateEventModal(true)}
            >
              <CalendarPlus className="w-4 h-4 mr-2" />
              Create Event
            </Button>
            <Button
              variant="primary"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
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

        {/* Calendar/List View */}
        {viewMode === 'calendar' ? (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-6 h-6 text-lavender" />
              <h2 className="text-2xl font-semibold">Schedule Calendar</h2>
            </div>
            <EventCalendar
              events={events}
              onEventClick={(event) => {
                console.log('Event clicked:', event);
                // You could add a modal here to show event details
              }}
            />
          </div>
        ) : (
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
                  {events.map((event) => {
                    const isAssignment = event.event_type === "assignment";
                    const isCommute = event.event_type === "commute";

                    return (
                      <div
                        key={event.id}
                        className={`p-4 rounded-xl border relative ${
                          isAssignment
                            ? 'bg-purple-50/50 border-purple-300/50'
                            : isCommute
                            ? 'bg-blue-50/50 border-blue-300/50'
                            : 'bg-soft-pink/30 border-rose/20'
                        }`}
                      >
                        {/* Delete button in top-right corner */}
                        <button
                          onClick={() => handleDeleteEvent(event)}
                          className="absolute top-2 right-2 p-1.5 rounded-lg text-mauve/60 hover:text-red-600 hover:bg-red-50 transition-all"
                          title="Delete event from Google Calendar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>

                        <div className="flex items-start gap-2 pr-8">
                          {isAssignment && <span className="text-lg">📚</span>}
                          {isCommute && <span className="text-lg">🚌</span>}
                          <div className="flex-1">
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
                            {isAssignment && event.description && (
                              <p className="text-xs text-purple-600 mt-1 italic">
                                {event.description.includes('due')
                                  ? event.description.split('Auto-scheduled study block for assignment')[1]?.trim()
                                  : event.description}
                              </p>
                            )}
                          </div>
                          {isAssignment && (
                            <button
                              onClick={() => handleSyncAssignmentBlock(event)}
                              disabled={syncedEvents.has(`assignment-${event.id}`)}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                syncedEvents.has(`assignment-${event.id}`)
                                  ? 'bg-green-100 text-green-700 cursor-not-allowed'
                                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                              }`}
                              title={syncedEvents.has(`assignment-${event.id}`) ? 'Already synced' : 'Add to Google Calendar'}
                            >
                              {syncedEvents.has(`assignment-${event.id}`) ? (
                                <>
                                  <CheckCircle2 className="w-4 h-4" />
                                  <span>Synced</span>
                                </>
                              ) : (
                                <>
                                  <CalendarPlus className="w-4 h-4" />
                                  <span>Sync</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
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
            </div>
          </div>
        )}

        {/* Bus Suggestions */}
        <Card variant="sage" className="mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Bus className="w-6 h-6 text-sage" />
            <h2 className="text-2xl font-semibold">Bus Schedule 🚌</h2>
          </div>

          {recommendations?.bus_suggestions && (
            recommendations.bus_suggestions.morning || recommendations.bus_suggestions.evening
          ) ? (
            <>
              <div className="grid md:grid-cols-2 gap-4">
                {/* Morning Bus */}
                {recommendations.bus_suggestions.morning && (
                  <div className="p-4 bg-white/50 rounded-xl border border-sage/30">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">🌅</span>
                        <h3 className="font-semibold text-lg">Morning Bus</h3>
                      </div>
                      <button
                        onClick={() => handleSyncBus(recommendations.bus_suggestions!.morning!)}
                        disabled={syncedEvents.has('bus-outbound')}
                        className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                          syncedEvents.has('bus-outbound')
                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                        title={syncedEvents.has('bus-outbound') ? 'Already synced' : 'Add to Google Calendar'}
                      >
                        {syncedEvents.has('bus-outbound') ? (
                          <>
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Synced</span>
                          </>
                        ) : (
                          <>
                            <CalendarPlus className="w-3 h-3" />
                            <span>Sync</span>
                          </>
                        )}
                      </button>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Departs Main & Murray:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions!.morning!.departure_label}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Arrives at UDC:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions!.morning!.arrival_label}
                        </span>
                      </div>
                      <p className="text-sm text-mauve/70 mt-2 italic">
                        💡 {recommendations.bus_suggestions!.morning!.reason}
                      </p>
                      {recommendations.bus_suggestions!.morning!.is_late_night && (
                        <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full mt-2">
                          🌙 Late Night Bus
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Evening Bus */}
                {recommendations.bus_suggestions.evening && (
                  <div className="p-4 bg-white/50 rounded-xl border border-sage/30">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">🌆</span>
                        <h3 className="font-semibold text-lg">Evening Bus</h3>
                      </div>
                      <button
                        onClick={() => handleSyncBus(recommendations.bus_suggestions!.evening!)}
                        disabled={syncedEvents.has('bus-inbound')}
                        className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                          syncedEvents.has('bus-inbound')
                            ? 'bg-green-100 text-green-700 cursor-not-allowed'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                        title={syncedEvents.has('bus-inbound') ? 'Already synced' : 'Add to Google Calendar'}
                      >
                        {syncedEvents.has('bus-inbound') ? (
                          <>
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Synced</span>
                          </>
                        ) : (
                          <>
                            <CalendarPlus className="w-3 h-3" />
                            <span>Sync</span>
                          </>
                        )}
                      </button>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Departs UDC:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions!.evening!.departure_label}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Arrives Main & Murray:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions!.evening!.arrival_label}
                        </span>
                      </div>
                      <p className="text-sm text-mauve/70 mt-2 italic">
                        💡 {recommendations.bus_suggestions!.evening!.reason}
                      </p>
                      {recommendations.bus_suggestions!.evening!.is_late_night && (
                        <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full mt-2">
                          🌙 Late Night Bus
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>📍 Route:</strong> Westside (WS) - Main & Murray ↔ UDC
                </p>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🏡</div>
              <h3 className="text-xl font-semibold text-sage mb-2">No Campus Commitments Today</h3>
              <p className="text-mauve/70">
                All your events are remote or at home - no need to catch the bus today! Enjoy staying cozy 💚
              </p>
            </div>
          )}
        </Card>

        {/* Assignments */}
        <Card variant="lavender" className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="w-6 h-6 text-lavender" />
              <h2 className="text-2xl font-semibold">Assignments 📝</h2>
            </div>
            <Button
              variant="primary"
              onClick={() => setShowNewAssignmentForm(!showNewAssignmentForm)}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Assignment
            </Button>
          </div>

          {/* New Assignment Form */}
          {showNewAssignmentForm && (
            <div className="mb-4 p-4 bg-white/50 rounded-xl border border-lavender/30">
              <h3 className="font-semibold mb-3">Create New Assignment</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Assignment title"
                  value={newAssignment.title}
                  onChange={(e) => setNewAssignment({ ...newAssignment, title: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender"
                />
                <textarea
                  placeholder="Description (optional)"
                  value={newAssignment.description}
                  onChange={(e) => setNewAssignment({ ...newAssignment, description: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender resize-none"
                  rows={3}
                />
                <div>
                  <label className="text-sm text-mauve mb-1 block">Assignment Type</label>
                  <select
                    value={newAssignment.assignment_type}
                    onChange={(e) => setNewAssignment({ ...newAssignment, assignment_type: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender"
                  >
                    <option value="">Select type (optional)</option>
                    <option value="exam">Exam</option>
                    <option value="quiz">Quiz</option>
                    <option value="lab_report">Lab Report</option>
                    <option value="homework">Homework</option>
                    <option value="project">Project</option>
                    <option value="essay">Essay</option>
                    <option value="presentation">Presentation</option>
                    <option value="reading">Reading</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="grid md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-sm text-mauve mb-1 block">Due Date</label>
                    <input
                      type="datetime-local"
                      value={newAssignment.due_date}
                      onChange={(e) => setNewAssignment({ ...newAssignment, due_date: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-mauve mb-1 block">Estimated Hours (optional)</label>
                    <input
                      type="number"
                      min="0.1"
                      step="0.5"
                      placeholder="Leave blank for AI to suggest"
                      value={newAssignment.estimated_hours}
                      onChange={(e) => setNewAssignment({ ...newAssignment, estimated_hours: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-mauve mb-1 block">Priority</label>
                    <select
                      value={newAssignment.priority}
                      onChange={(e) => setNewAssignment({ ...newAssignment, priority: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border border-mauve/30 focus:outline-none focus:border-lavender"
                    >
                      <option value={1}>Low</option>
                      <option value={2}>Medium</option>
                      <option value={3}>High</option>
                    </select>
                  </div>
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setShowNewAssignmentForm(false)}>
                    Cancel
                  </Button>
                  <Button variant="primary" onClick={handleCreateAssignment}>
                    Create Assignment
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Assignments List */}
          {assignments.length === 0 ? (
            <p className="text-mauve/70 italic text-center py-6">
              No assignments yet. Click "New Assignment" to get started! ✨
            </p>
          ) : (
            <div className="space-y-3">
              {assignments.map((assignment) => {
                const dueDate = new Date(assignment.due_date);
                const isOverdue = dueDate < new Date() && !assignment.completed;

                return (
                  <div
                    key={assignment.id}
                    className={`p-4 rounded-xl border ${
                      assignment.completed
                        ? 'bg-green-50/50 border-green-200'
                        : isOverdue
                        ? 'bg-red-50/50 border-red-200'
                        : 'bg-white/50 border-lavender/30'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => handleToggleComplete(assignment)}
                        className="mt-1 text-lavender hover:scale-110 transition-transform"
                      >
                        {assignment.completed ? (
                          <CheckCircle2 className="w-6 h-6 text-green-600" />
                        ) : (
                          <Circle className="w-6 h-6" />
                        )}
                      </button>

                      <div className="flex-1">
                        <h3 className={`font-semibold ${assignment.completed ? 'line-through text-mauve/50' : ''}`}>
                          {assignment.title}
                        </h3>
                        {assignment.description && (
                          <p className={`text-sm mt-1 ${assignment.completed ? 'text-mauve/40' : 'text-mauve/70'}`}>
                            {assignment.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-sm">
                          <span className={isOverdue ? 'text-red-600 font-semibold' : 'text-mauve'}>
                            📅 Due: {dueDate.toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: 'numeric',
                              minute: '2-digit'
                            })}
                            {isOverdue && ' (Overdue!)'}
                          </span>
                          <span className="text-mauve">⏱️ {assignment.estimated_hours}h</span>
                          <span className={getPriorityColor(assignment.priority)}>
                            {getPriorityLabel(assignment.priority)} Priority
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteAssignment(assignment.id)}
                        className="text-red-400 hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

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

      {/* Create Event Modal */}
      {showCreateEventModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-rose">Create Event</h2>
              <button
                onClick={() => setShowCreateEventModal(false)}
                className="text-mauve hover:text-rose transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  Event Title *
                </label>
                <input
                  type="text"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  placeholder="e.g., Doctor Appointment"
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose"
                />
              </div>

              {/* Start Time */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  Start Time *
                </label>
                <input
                  type="datetime-local"
                  value={newEvent.start_time}
                  onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose"
                />
              </div>

              {/* End Time */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  End Time *
                </label>
                <input
                  type="datetime-local"
                  value={newEvent.end_time}
                  onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose"
                />
              </div>

              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  Location (optional)
                </label>
                <input
                  type="text"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  placeholder="e.g., Student Health Center"
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  placeholder="Add any notes..."
                  rows={3}
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose resize-none"
                />
              </div>

              {/* Color */}
              <div>
                <label className="block text-sm font-medium text-mauve mb-2">
                  Calendar Color
                </label>
                <select
                  value={newEvent.color_id}
                  onChange={(e) => setNewEvent({ ...newEvent, color_id: e.target.value })}
                  className="w-full px-4 py-2 border border-sage/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-rose"
                >
                  <option value="9">Blue (Default)</option>
                  <option value="3">Purple (Study)</option>
                  <option value="10">Green</option>
                  <option value="11">Red</option>
                  <option value="5">Yellow</option>
                  <option value="6">Orange</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateEventModal(false)}
                className="flex-1 px-4 py-2 border border-sage/30 rounded-lg text-mauve hover:bg-sage/10 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateEvent}
                className="flex-1 px-4 py-2 bg-rose text-white rounded-lg hover:bg-rose/90 transition-colors font-medium"
              >
                Create Event
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
