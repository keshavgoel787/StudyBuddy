'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StudyMaterialViewer, StudyMaterial } from '@/components/StudyMaterialViewer';
import {
  Upload,
  FileText,
  Sparkles,
  ArrowLeft,
} from 'lucide-react';
import { uploadNote, uploadTextNote, generateStudyMaterial } from '@/lib/api';
import { showErrorAlert, logError } from '@/lib/errorHandler';

export default function StudyPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [view, setView] = useState<'upload' | 'material'>('upload');
  const [loading, setLoading] = useState(false);
  const [textNotes, setTextNotes] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [topicHint, setTopicHint] = useState('');
  const [studyMaterial, setStudyMaterial] = useState<StudyMaterial | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', noteTitle || file.name);

      // Upload and generate study material sequentially (generate depends on upload)
      const uploadResult = await uploadNote(formData);
      const material = await generateStudyMaterial(uploadResult.note_document_id, topicHint);

      setStudyMaterial(material);
      setView('material');
    } catch (error) {
      logError('File Upload', error);
      showErrorAlert(error, 'Failed to upload notes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTextUpload = async () => {
    if (!textNotes.trim()) {
      alert('Please enter some notes first!');
      return;
    }

    setLoading(true);
    try {
      // Upload and generate study material sequentially (generate depends on upload)
      const uploadResult = await uploadTextNote(
        textNotes,
        noteTitle || 'My Notes'
      );
      const material = await generateStudyMaterial(uploadResult.note_document_id, topicHint);

      setStudyMaterial(material);
      setView('material');
    } catch (error) {
      logError('Text Upload', error);
      showErrorAlert(error, 'Failed to process notes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <LoadingSpinner
        message="AI is reading your notes... ✨"
        submessage="Generating summaries, flashcards, and practice questions"
      />
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
            Back
          </Button>
          <div>
            <h1 className="text-5xl font-bold text-lavender mb-2">
              Study Buddy 📚
            </h1>
            <p className="text-xl text-mauve font-serif italic">
              Transform your notes into study materials
            </p>
          </div>
        </div>

        {view === 'upload' && (
          <div className="space-y-6">
            {/* Upload Card */}
            <Card variant="lavender" className="space-y-6">
              <div className="flex items-center gap-3">
                <Upload className="w-8 h-8 text-lavender" />
                <h2 className="text-2xl font-semibold">Upload Notes</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Note Title (optional)
                  </label>
                  <input
                    type="text"
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    placeholder="e.g., Biochem L12 - Enzyme Kinetics"
                    className="w-full px-4 py-3 rounded-xl border-2 border-lavender/30 bg-white/80 focus:border-lavender focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Topic/Subject (optional)
                  </label>
                  <input
                    type="text"
                    value={topicHint}
                    onChange={(e) => setTopicHint(e.target.value)}
                    placeholder="e.g., Physics - 2D Kinematics, Organic Chemistry, etc."
                    className="w-full px-4 py-3 rounded-xl border-2 border-lavender/30 bg-white/80 focus:border-lavender focus:outline-none"
                  />
                  <p className="text-xs text-mauve/70 mt-1">
                    💡 Helps the AI generate more relevant study materials
                  </p>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {/* Image Upload */}
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-lavender/40 rounded-xl p-8 text-center cursor-pointer hover:border-lavender hover:bg-lavender/5 transition-all"
                  >
                    <Upload className="w-12 h-12 text-lavender mx-auto mb-3" />
                    <p className="font-medium text-foreground mb-1">
                      Upload Image
                    </p>
                    <p className="text-sm text-mauve/70">
                      Handwritten notes (JPG, PNG)
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </div>

                  {/* Text Input */}
                  <div className="border-2 border-lavender/40 rounded-xl p-6 bg-white/60">
                    <FileText className="w-12 h-12 text-lavender mx-auto mb-3" />
                    <p className="font-medium text-foreground mb-1 text-center">
                      Or Paste Text
                    </p>
                    <p className="text-sm text-mauve/70 text-center mb-3">
                      Type or paste your notes
                    </p>
                  </div>
                </div>

                {/* Text Area */}
                <div>
                  <textarea
                    value={textNotes}
                    onChange={(e) => setTextNotes(e.target.value)}
                    placeholder="Paste your typed notes here..."
                    rows={8}
                    className="w-full px-4 py-3 rounded-xl border-2 border-lavender/30 bg-white/80 focus:border-lavender focus:outline-none resize-none"
                  />
                </div>

                <Button
                  variant="secondary"
                  size="lg"
                  onClick={handleTextUpload}
                  disabled={!textNotes.trim()}
                  className="w-full"
                >
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate Study Materials
                </Button>
              </div>
            </Card>

            <Card className="text-center border-dusty-rose/30">
              <p className="text-mauve font-serif italic">
                💡 Tip: The clearer your notes, the better the AI can help you study!
              </p>
            </Card>
          </div>
        )}

        {view === 'material' && studyMaterial && (
          <div className="space-y-6">
            <StudyMaterialViewer studyMaterial={studyMaterial} />

            {/* Actions */}
            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  setView('upload');
                  setStudyMaterial(null);
                  setTextNotes('');
                  setNoteTitle('');
                  setTopicHint('');
                }}
                className="flex-1"
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload New Notes
              </Button>
              <Button
                variant="primary"
                onClick={() => router.push('/dashboard')}
                className="flex-1"
              >
                Back to Dashboard
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
