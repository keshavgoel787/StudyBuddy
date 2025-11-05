'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { ArrowLeft, BookOpen, Trash2, Eye, Calendar as CalendarIcon } from 'lucide-react';
import { getAllNotes, deleteNote } from '@/lib/api';

interface Note {
  id: string;
  title: string;
  created_at: string;
}

export default function NotesLibrary() {
  const router = useRouter();
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      const data = await getAllNotes();
      setNotes(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load notes:', error);
      setLoading(false);
    }
  };

  const handleDelete = async (noteId: string) => {
    if (!confirm('Are you sure you want to delete this note? This will also delete all study materials.')) {
      return;
    }

    try {
      await deleteNote(noteId);
      setNotes(notes.filter(n => n.id !== noteId));
    } catch (error) {
      console.error('Failed to delete note:', error);
      alert('Failed to delete note');
    }
  };

  const handleView = (noteId: string) => {
    // Navigate directly - let the study page handle loading/generating materials
    router.push(`/study/${noteId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin text-lavender text-6xl">📚</div>
          <p className="text-xl text-mauve font-serif">Loading your notes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 overflow-hidden">
      {/* Animated flowers */}
      <FloatingFlower initialX={5} initialY={10} color="#D4C5E2" delay={0} />
      <FloatingFlower initialX={90} initialY={15} color="#FFB3C1" delay={1} />
      <FloatingFlower initialX={10} initialY={80} color="#FFD4B2" delay={2} />

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Dashboard
          </Button>
          <div className="flex-1">
            <h1 className="text-5xl font-bold text-lavender mb-2">
              My Notes 📚
            </h1>
            <p className="text-xl text-mauve font-serif italic">
              All your study materials in one place
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => router.push('/study')}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            Upload New
          </Button>
        </div>

        {/* Notes List */}
        {notes.length === 0 ? (
          <Card className="text-center py-12">
            <BookOpen className="w-16 h-16 text-mauve/40 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold mb-2">No notes yet</h2>
            <p className="text-mauve/70 mb-6">
              Start by uploading your first set of notes!
            </p>
            <Button
              variant="primary"
              onClick={() => router.push('/study')}
            >
              Upload Notes
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {notes.map((note) => (
              <Card key={note.id} variant="default" className="hover:shadow-xl transition-all">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      {note.title}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-mauve/70">
                      <CalendarIcon className="w-4 h-4" />
                      <span>{formatDate(note.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleView(note.id)}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(note.id)}
                      className="border-rose text-rose hover:bg-rose/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
