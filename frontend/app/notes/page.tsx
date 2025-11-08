'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { ArrowLeft, BookOpen, Trash2, Eye, Calendar as CalendarIcon, Layers } from 'lucide-react';
import { getAllNotes, deleteNote, combineNotes } from '@/lib/api';

interface Note {
  id: string;
  title: string;
  created_at: string;
  has_study_material: boolean;
}

interface CombinedStudyViewProps {
  material: any;
  onClose: () => void;
  selectedNotesTitles: string[];
}

function CombinedStudyView({ material, onClose, selectedNotesTitles }: CombinedStudyViewProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'flashcards' | 'practice'>('summary');

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card variant="default" className="bg-gradient-to-br from-lavender/10 to-rose/10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-lavender mb-2">
              Combined Study Guide 📚✨
            </h2>
            <p className="text-mauve/80">
              Synthesized from {selectedNotesTitles.length} notes: {selectedNotesTitles.join(', ')}
            </p>
          </div>
          <Button variant="outline" onClick={onClose}>
            Back to Notes
          </Button>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-mauve/20">
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'summary'
              ? 'text-lavender border-b-2 border-lavender'
              : 'text-mauve/60 hover:text-mauve'
          }`}
        >
          Summary
        </button>
        <button
          onClick={() => setActiveTab('flashcards')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'flashcards'
              ? 'text-lavender border-b-2 border-lavender'
              : 'text-mauve/60 hover:text-mauve'
          }`}
        >
          Flashcards ({material.flashcards?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab('practice')}
          className={`px-6 py-3 font-medium transition-all ${
            activeTab === 'practice'
              ? 'text-lavender border-b-2 border-lavender'
              : 'text-mauve/60 hover:text-mauve'
          }`}
        >
          Practice ({material.practice_questions?.length || 0})
        </button>
      </div>

      {/* Content */}
      {activeTab === 'summary' && (
        <div className="space-y-4">
          <Card>
            <h3 className="text-xl font-semibold text-lavender mb-3">Quick Summary</h3>
            <p className="text-mauve leading-relaxed">{material.summary_short}</p>
          </Card>
          <Card>
            <h3 className="text-xl font-semibold text-lavender mb-3">Detailed Summary</h3>
            <p className="text-mauve leading-relaxed whitespace-pre-wrap">{material.summary_detailed}</p>
          </Card>
        </div>
      )}

      {activeTab === 'flashcards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {material.flashcards?.map((card: any, idx: number) => (
            <Card key={idx} className="hover:shadow-lg transition-all">
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <span className="px-2 py-1 text-xs font-bold bg-lavender/20 text-lavender rounded">
                    {idx + 1}
                  </span>
                  <p className="font-semibold text-foreground flex-1">{card.question}</p>
                </div>
                <div className="pl-8">
                  <p className="text-mauve text-sm">{card.answer}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'practice' && (
        <div className="space-y-4">
          {material.practice_questions?.map((q: any, idx: number) => (
            <Card key={idx}>
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <span className="px-2 py-1 text-xs font-bold bg-rose/20 text-rose rounded">
                    Q{idx + 1}
                  </span>
                  <p className="font-semibold text-foreground flex-1">{q.question}</p>
                </div>
                <div className="pl-8 space-y-2">
                  {q.options?.map((opt: string, optIdx: number) => (
                    <div
                      key={optIdx}
                      className={`p-2 rounded ${
                        optIdx === q.correct_index
                          ? 'bg-sage/20 border border-sage'
                          : 'bg-mauve/5'
                      }`}
                    >
                      <span className="font-medium">{String.fromCharCode(65 + optIdx)}. </span>
                      {opt}
                    </div>
                  ))}
                  <div className="pt-2 border-t border-mauve/20">
                    <p className="text-sm text-mauve">
                      <span className="font-semibold">Explanation: </span>
                      {q.explanation}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function NotesLibrary() {
  const router = useRouter();
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [combineMode, setCombineMode] = useState(false);
  const [selectedNotes, setSelectedNotes] = useState<string[]>([]);
  const [combining, setCombining] = useState(false);
  const [combinedMaterial, setCombinedMaterial] = useState<any>(null);

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

  const toggleNoteSelection = (noteId: string) => {
    setSelectedNotes(prev =>
      prev.includes(noteId)
        ? prev.filter(id => id !== noteId)
        : [...prev, noteId]
    );
  };

  const handleCombineNotes = async () => {
    if (selectedNotes.length < 2) {
      alert('Please select at least 2 notes to combine');
      return;
    }

    if (selectedNotes.length > 10) {
      alert('You can combine a maximum of 10 notes at once');
      return;
    }

    setCombining(true);
    try {
      const result = await combineNotes(selectedNotes);
      setCombinedMaterial(result);
    } catch (error) {
      console.error('Failed to combine notes:', error);
      alert('Failed to combine notes. Please try again.');
    } finally {
      setCombining(false);
    }
  };

  const cancelCombineMode = () => {
    setCombineMode(false);
    setSelectedNotes([]);
    setCombinedMaterial(null);
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
              {combineMode ? 'Select notes to combine' : 'All your study materials in one place'}
            </p>
          </div>
          {!combineMode ? (
            <>
              <Button
                variant="secondary"
                onClick={() => setCombineMode(true)}
                disabled={notes.length < 2}
              >
                <Layers className="w-4 h-4 mr-2" />
                Combine Notes
              </Button>
              <Button
                variant="primary"
                onClick={() => router.push('/study')}
              >
                <BookOpen className="w-4 h-4 mr-2" />
                Upload New
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={cancelCombineMode}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCombineNotes}
                disabled={selectedNotes.length < 2 || combining}
              >
                <Layers className="w-4 h-4 mr-2" />
                {combining ? 'Combining...' : `Combine (${selectedNotes.length})`}
              </Button>
            </>
          )}
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
        ) : !combinedMaterial ? (
          <div className="space-y-4">
            {notes.map((note) => (
              <Card
                key={note.id}
                variant="default"
                className={`hover:shadow-xl transition-all ${
                  combineMode && selectedNotes.includes(note.id) ? 'ring-2 ring-lavender' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  {combineMode && (
                    <input
                      type="checkbox"
                      checked={selectedNotes.includes(note.id)}
                      onChange={() => toggleNoteSelection(note.id)}
                      className="w-5 h-5 text-lavender rounded focus:ring-lavender mr-4"
                    />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-xl font-semibold text-foreground">
                        {note.title}
                      </h3>
                      {note.has_study_material && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-sage/20 text-sage rounded-full">
                          ✨ Ready
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-mauve/70">
                      <CalendarIcon className="w-4 h-4" />
                      <span>{formatDate(note.created_at)}</span>
                    </div>
                  </div>

                  {!combineMode && (
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
                  )}
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <CombinedStudyView
            material={combinedMaterial}
            onClose={cancelCombineMode}
            selectedNotesTitles={notes.filter(n => selectedNotes.includes(n.id)).map(n => n.title)}
          />
        )}
      </div>
    </div>
  );
}
