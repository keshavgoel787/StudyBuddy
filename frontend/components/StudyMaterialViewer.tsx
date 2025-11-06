'use client';

import { useState } from 'react';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import {
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Check,
  X,
} from 'lucide-react';

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

export interface StudyMaterial {
  summary_short: string;
  summary_detailed: string;
  flashcards: Flashcard[];
  practice_questions: PracticeQuestion[];
}

interface StudyMaterialViewerProps {
  studyMaterial: StudyMaterial;
  variant?: 'full' | 'compact';
}

export function StudyMaterialViewer({ studyMaterial, variant = 'full' }: StudyMaterialViewerProps) {
  // Flashcard state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);

  // Quiz state
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showQuizResult, setShowQuizResult] = useState(false);

  const nextCard = () => {
    if (currentCardIndex < studyMaterial.flashcards.length - 1) {
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
    if (currentQuizIndex < studyMaterial.practice_questions.length - 1) {
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

  return (
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
            <p className="text-foreground/80 leading-relaxed whitespace-pre-line">
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
    </div>
  );
}
