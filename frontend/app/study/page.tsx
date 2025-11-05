'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import {
  Upload,
  FileText,
  Sparkles,
  Loader2,
  ArrowLeft,
  BookOpen,
  ChevronRight,
  ChevronLeft,
  Check,
  X,
} from 'lucide-react';
import { uploadNote, uploadTextNote, generateStudyMaterial } from '@/lib/api';

interface Flashcard {
  question: string;
  answer: string;
}

interface PracticeQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

interface StudyMaterial {
  summary_short: string;
  summary_detailed: string;
  flashcards: Flashcard[];
  practice_questions: PracticeQuestion[];
}

export default function StudyPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [view, setView] = useState<'upload' | 'material'>('upload');
  const [loading, setLoading] = useState(false);
  const [textNotes, setTextNotes] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [topicHint, setTopicHint] = useState('');
  const [studyMaterial, setStudyMaterial] = useState<StudyMaterial | null>(null);

  // Flashcard state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);

  // Quiz state
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showQuizResult, setShowQuizResult] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', noteTitle || file.name);

      const uploadResult = await uploadNote(formData);
      const material = await generateStudyMaterial(uploadResult.note_document_id, topicHint);

      setStudyMaterial(material);
      setView('material');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload notes. Please try again.');
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
      const uploadResult = await uploadTextNote(
        textNotes,
        noteTitle || 'My Notes'
      );
      const material = await generateStudyMaterial(uploadResult.note_document_id, topicHint);

      setStudyMaterial(material);
      setView('material');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to process notes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const nextCard = () => {
    if (studyMaterial && currentCardIndex < studyMaterial.flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setShowAnswer(false);
    }
  };

  const prevCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1);
      setShowAnswer(false);
    }
  };

  const nextQuestion = () => {
    if (studyMaterial && currentQuizIndex < studyMaterial.practice_questions.length - 1) {
      setCurrentQuizIndex(currentQuizIndex + 1);
      setSelectedAnswer(null);
      setShowQuizResult(false);
    }
  };

  const prevQuestion = () => {
    if (currentQuizIndex > 0) {
      setCurrentQuizIndex(currentQuizIndex - 1);
      setSelectedAnswer(null);
      setShowQuizResult(false);
    }
  };

  const checkAnswer = () => {
    if (selectedAnswer !== null) {
      setShowQuizResult(true);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-16 h-16 text-rose animate-spin mx-auto" />
          <p className="text-xl text-mauve font-serif">
            AI is reading your notes... ✨
          </p>
          <p className="text-sm text-mauve/70">
            Generating summaries, flashcards, and practice questions
          </p>
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
            {/* Summaries */}
            <Card variant="rose">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <Sparkles className="w-6 h-6" />
                Summary
              </h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-lg mb-2">Quick Summary</h3>
                  <p className="text-foreground/80 leading-relaxed">
                    {studyMaterial.summary_short}
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Detailed Summary</h3>
                  <p className="text-foreground/80 leading-relaxed">
                    {studyMaterial.summary_detailed}
                  </p>
                </div>
              </div>
            </Card>

            {/* Flashcards */}
            {studyMaterial.flashcards.length > 0 && (
              <Card variant="lavender">
                <h2 className="text-2xl font-semibold mb-4">
                  Flashcards ({currentCardIndex + 1}/{studyMaterial.flashcards.length})
                </h2>
                <div
                  onClick={() => setShowAnswer(!showAnswer)}
                  className="bg-white/80 rounded-xl p-8 min-h-[200px] flex items-center justify-center cursor-pointer hover:bg-white transition-all border-2 border-lavender/30"
                >
                  <div className="text-center">
                    {!showAnswer ? (
                      <>
                        <p className="text-sm text-mauve/70 mb-2">Question</p>
                        <p className="text-xl font-medium">
                          {studyMaterial.flashcards[currentCardIndex].question}
                        </p>
                        <p className="text-sm text-mauve/70 mt-4 italic">
                          Click to reveal answer
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-sm text-mauve/70 mb-2">Answer</p>
                        <p className="text-xl font-medium text-lavender">
                          {studyMaterial.flashcards[currentCardIndex].answer}
                        </p>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex justify-between items-center mt-4">
                  <Button
                    variant="outline"
                    onClick={prevCard}
                    disabled={currentCardIndex === 0}
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={nextCard}
                    disabled={currentCardIndex === studyMaterial.flashcards.length - 1}
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </Card>
            )}

            {/* Practice Quiz */}
            {studyMaterial.practice_questions.length > 0 && (
              <Card variant="peach">
                <h2 className="text-2xl font-semibold mb-4">
                  Practice Quiz ({currentQuizIndex + 1}/{studyMaterial.practice_questions.length})
                </h2>
                <div className="space-y-4">
                  <p className="text-lg font-medium">
                    {studyMaterial.practice_questions[currentQuizIndex].question}
                  </p>

                  <div className="space-y-2">
                    {studyMaterial.practice_questions[currentQuizIndex].options.map((option, idx) => {
                      const isCorrect = idx === studyMaterial.practice_questions[currentQuizIndex].correct_index;
                      const isSelected = idx === selectedAnswer;
                      const showResult = showQuizResult && isSelected;

                      return (
                        <div
                          key={idx}
                          onClick={() => !showQuizResult && setSelectedAnswer(idx)}
                          className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                            showResult
                              ? isCorrect
                                ? 'border-sage bg-sage/20'
                                : 'border-rose bg-rose/20'
                              : isSelected
                              ? 'border-lavender bg-lavender/20'
                              : 'border-mauve/20 bg-white/60 hover:border-mauve'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span>{option}</span>
                            {showResult && isSelected && (
                              isCorrect ? (
                                <Check className="w-5 h-5 text-sage" />
                              ) : (
                                <X className="w-5 h-5 text-rose" />
                              )
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {showQuizResult && (
                    <div className="bg-powder-blue/30 rounded-xl p-4 border border-powder-blue/40">
                      <p className="font-medium mb-2">Explanation:</p>
                      <p className="text-foreground/80">
                        {studyMaterial.practice_questions[currentQuizIndex].explanation}
                      </p>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <Button
                      variant="outline"
                      onClick={prevQuestion}
                      disabled={currentQuizIndex === 0}
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </Button>

                    {!showQuizResult ? (
                      <Button
                        variant="primary"
                        onClick={checkAnswer}
                        disabled={selectedAnswer === null}
                      >
                        Check Answer
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={nextQuestion}
                        disabled={currentQuizIndex === studyMaterial.practice_questions.length - 1}
                      >
                        Next
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}

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
