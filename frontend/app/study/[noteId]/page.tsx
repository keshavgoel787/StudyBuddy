'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { ArrowLeft, BookOpen, RefreshCw } from 'lucide-react';
import { getStudyMaterial, generateStudyMaterial } from '@/lib/api';

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

export default function ViewStudyMaterial() {
  const router = useRouter();
  const params = useParams();
  const noteId = params.noteId as string;

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [material, setMaterial] = useState<StudyMaterial | null>(null);
  const [currentFlashcard, setCurrentFlashcard] = useState(0);
  const [showFlashcardAnswer, setShowFlashcardAnswer] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState<number[]>([]);
  const [showQuizResults, setShowQuizResults] = useState(false);

  useEffect(() => {
    loadStudyMaterial();
  }, [noteId]);

  const loadStudyMaterial = async () => {
    try {
      const data = await getStudyMaterial(noteId);
      setMaterial(data);
      setQuizAnswers(new Array(data.practice_questions.length).fill(-1));
      setLoading(false);
    } catch (error: any) {
      // If no study material exists, try to generate it
      if (error.response?.status === 404) {
        handleGenerate();
      } else {
        console.error('Failed to load study material:', error);
        alert('Failed to load study material');
        setLoading(false);
      }
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = await generateStudyMaterial(noteId);
      setMaterial(data);
      setQuizAnswers(new Array(data.practice_questions.length).fill(-1));
    } catch (error) {
      console.error('Failed to generate study material:', error);
      alert('Failed to generate study material');
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  const handleQuizAnswer = (questionIndex: number, answerIndex: number) => {
    if (showQuizResults) return; // Don't allow changes after showing results
    const newAnswers = [...quizAnswers];
    newAnswers[questionIndex] = answerIndex;
    setQuizAnswers(newAnswers);
  };

  const handleSubmitQuiz = () => {
    if (quizAnswers.includes(-1)) {
      alert('Please answer all questions before submitting!');
      return;
    }
    setShowQuizResults(true);
  };

  const calculateQuizScore = () => {
    if (!material) return 0;
    let correct = 0;
    material.practice_questions.forEach((q, i) => {
      if (quizAnswers[i] === q.correct_index) correct++;
    });
    return Math.round((correct / material.practice_questions.length) * 100);
  };

  if (loading || generating) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin text-lavender text-6xl">✨</div>
          <p className="text-xl text-mauve font-serif">
            {generating ? 'Generating your study materials...' : 'Loading study materials...'}
          </p>
        </div>
      </div>
    );
  }

  if (!material) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <Card className="text-center max-w-md">
          <BookOpen className="w-16 h-16 text-mauve/40 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No Study Materials Found</h2>
          <p className="text-mauve/70 mb-6">
            Something went wrong. Please try again.
          </p>
          <Button variant="primary" onClick={() => router.push('/notes')}>
            Back to Notes
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 overflow-hidden">
      {/* Animated flowers */}
      <FloatingFlower initialX={5} initialY={10} color="#D4C5E2" delay={0} />
      <FloatingFlower initialX={90} initialY={15} color="#FFB3C1" delay={1} />
      <FloatingFlower initialX={10} initialY={80} color="#C5E1A5" delay={2} />

      <div className="max-w-4xl mx-auto relative z-10 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" onClick={() => router.push('/notes')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            My Notes
          </Button>
          <div className="flex-1">
            <h1 className="text-5xl font-bold text-lavender mb-2">
              Study Materials ✨
            </h1>
          </div>
          <Button variant="outline" onClick={handleGenerate} disabled={generating}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Regenerate
          </Button>
        </div>

        {/* Summary Section */}
        <Card variant="lavender">
          <h2 className="text-2xl font-semibold text-lavender mb-4">📝 Summary</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-lg mb-2">Quick Summary</h3>
              <p className="text-foreground/80 leading-relaxed">{material.summary_short}</p>
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Detailed Summary</h3>
              <p className="text-foreground/80 leading-relaxed whitespace-pre-line">
                {material.summary_detailed}
              </p>
            </div>
          </div>
        </Card>

        {/* Flashcards Section */}
        {material.flashcards.length > 0 && (
          <Card variant="rose">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-rose">🗂️ Flashcards</h2>
              <span className="text-sm text-mauve">
                {currentFlashcard + 1} / {material.flashcards.length}
              </span>
            </div>

            <div
              className="min-h-[200px] bg-white/50 rounded-xl p-6 cursor-pointer flex items-center justify-center text-center border-2 border-rose/20 hover:border-rose/40 transition-all"
              onClick={() => setShowFlashcardAnswer(!showFlashcardAnswer)}
            >
              <div>
                <p className="text-sm text-mauve/70 mb-2">
                  {showFlashcardAnswer ? 'Answer' : 'Question'} (click to flip)
                </p>
                <p className="text-lg font-medium">
                  {showFlashcardAnswer
                    ? material.flashcards[currentFlashcard].answer
                    : material.flashcards[currentFlashcard].question}
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <Button
                variant="outline"
                onClick={() => {
                  setCurrentFlashcard(Math.max(0, currentFlashcard - 1));
                  setShowFlashcardAnswer(false);
                }}
                disabled={currentFlashcard === 0}
                className="flex-1"
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setCurrentFlashcard(
                    Math.min(material.flashcards.length - 1, currentFlashcard + 1)
                  );
                  setShowFlashcardAnswer(false);
                }}
                disabled={currentFlashcard === material.flashcards.length - 1}
                className="flex-1"
              >
                Next
              </Button>
            </div>
          </Card>
        )}

        {/* Practice Questions Section */}
        {material.practice_questions.length > 0 && (
          <Card variant="peach">
            <h2 className="text-2xl font-semibold text-peach mb-6">📚 Practice Quiz</h2>

            <div className="space-y-6">
              {material.practice_questions.map((q, qIndex) => (
                <div key={qIndex} className="bg-white/50 rounded-xl p-4 border border-peach/20">
                  <p className="font-semibold mb-3">
                    {qIndex + 1}. {q.question}
                  </p>

                  <div className="space-y-2">
                    {q.options.map((option, oIndex) => {
                      const isSelected = quizAnswers[qIndex] === oIndex;
                      const isCorrect = oIndex === q.correct_index;
                      const showCorrectness = showQuizResults;

                      let optionClass = 'p-3 rounded-lg border-2 cursor-pointer transition-all ';
                      if (showCorrectness) {
                        if (isCorrect) {
                          optionClass += 'bg-sage/20 border-sage text-sage';
                        } else if (isSelected && !isCorrect) {
                          optionClass += 'bg-rose/20 border-rose text-rose';
                        } else {
                          optionClass += 'border-mauve/20 bg-white/30';
                        }
                      } else {
                        optionClass += isSelected
                          ? 'bg-lavender/20 border-lavender'
                          : 'border-mauve/20 bg-white/30 hover:border-lavender/50';
                      }

                      return (
                        <div
                          key={oIndex}
                          className={optionClass}
                          onClick={() => handleQuizAnswer(qIndex, oIndex)}
                        >
                          <span className="font-medium">{String.fromCharCode(65 + oIndex)}.</span>{' '}
                          {option}
                        </div>
                      );
                    })}
                  </div>

                  {showQuizResults && (
                    <div className="mt-3 p-3 bg-sage/10 rounded-lg border border-sage/30">
                      <p className="text-sm font-medium text-sage mb-1">Explanation:</p>
                      <p className="text-sm text-foreground/80">{q.explanation}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {!showQuizResults ? (
              <Button variant="primary" onClick={handleSubmitQuiz} className="w-full mt-6">
                Submit Quiz
              </Button>
            ) : (
              <div className="mt-6 text-center">
                <Card variant="sage" className="inline-block">
                  <p className="text-lg font-semibold">Your Score: {calculateQuizScore()}%</p>
                  <p className="text-sm text-mauve/70 mt-1">
                    {material.practice_questions.filter((q, i) => quizAnswers[i] === q.correct_index).length}{' '}
                    / {material.practice_questions.length} correct
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setQuizAnswers(new Array(material.practice_questions.length).fill(-1));
                      setShowQuizResults(false);
                    }}
                    className="mt-3"
                  >
                    Retake Quiz
                  </Button>
                </Card>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
