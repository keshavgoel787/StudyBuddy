'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { Calendar, Clock, Utensils, BookOpen, Bus, Sparkles, LogOut, RefreshCw, CheckSquare, Plus, Trash2, Circle, CheckCircle2 } from 'lucide-react';
import { getDayPlan, getAssignments, createAssignment, updateAssignment, deleteAssignment, Assignment, AssignmentCreate } from '@/lib/api';

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
    due_date: '',
    estimated_hours: 1,
    priority: 2
  });

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
        due_date: new Date(newAssignment.due_date).toISOString(),
        estimated_hours: newAssignment.estimated_hours,
        priority: newAssignment.priority
      };

      await createAssignment(assignmentData);
      setNewAssignment({
        title: '',
        description: '',
        due_date: '',
        estimated_hours: 1,
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
                      className={`p-4 rounded-xl border ${
                        isAssignment
                          ? 'bg-purple-50/50 border-purple-300/50'
                          : isCommute
                          ? 'bg-blue-50/50 border-blue-300/50'
                          : 'bg-soft-pink/30 border-rose/20'
                      }`}
                    >
                      <div className="flex items-start gap-2">
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
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">🌅</span>
                      <h3 className="font-semibold text-lg">Morning Bus</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Departs Main & Murray:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions.morning.departure_label}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Arrives at UDC:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions.morning.arrival_label}
                        </span>
                      </div>
                      <p className="text-sm text-mauve/70 mt-2 italic">
                        💡 {recommendations.bus_suggestions.morning.reason}
                      </p>
                      {recommendations.bus_suggestions.morning.is_late_night && (
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
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">🌆</span>
                      <h3 className="font-semibold text-lg">Evening Bus</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Departs UDC:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions.evening.departure_label}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-mauve">Arrives Main & Murray:</span>
                        <span className="font-semibold text-sage">
                          {recommendations.bus_suggestions.evening.arrival_label}
                        </span>
                      </div>
                      <p className="text-sm text-mauve/70 mt-2 italic">
                        💡 {recommendations.bus_suggestions.evening.reason}
                      </p>
                      {recommendations.bus_suggestions.evening.is_late_night && (
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
                    <label className="text-sm text-mauve mb-1 block">Estimated Hours</label>
                    <input
                      type="number"
                      min="0.1"
                      step="0.5"
                      value={newAssignment.estimated_hours}
                      onChange={(e) => setNewAssignment({ ...newAssignment, estimated_hours: parseFloat(e.target.value) })}
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
    </div>
  );
}
