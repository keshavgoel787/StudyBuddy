'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { FloatingFlower } from '@/components/AnimatedFlower';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { StudyMaterialViewer, StudyMaterial } from '@/components/StudyMaterialViewer';
import { ArrowLeft, BookOpen, RefreshCw } from 'lucide-react';
import { getStudyMaterial, generateStudyMaterial } from '@/lib/api';
import { showErrorAlert, logError } from '@/lib/errorHandler';

export default function ViewStudyMaterial() {
  const router = useRouter();
  const params = useParams();
  const noteId = params.noteId as string;

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [material, setMaterial] = useState<StudyMaterial | null>(null);

  useEffect(() => {
    loadStudyMaterial();
  }, [noteId]);

  const loadStudyMaterial = async () => {
    try {
      const data = await getStudyMaterial(noteId);
      setMaterial(data);
      setLoading(false);
    } catch (error: any) {
      // If no study material exists, try to generate it
      if (error.response?.status === 404) {
        handleGenerate();
      } else {
        logError('Load Study Material', error);
        showErrorAlert(error, 'Failed to load study material');
        setLoading(false);
      }
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const data = await generateStudyMaterial(noteId);
      setMaterial(data);
    } catch (error) {
      logError('Generate Study Material', error);
      showErrorAlert(error, 'Failed to generate study material');
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  if (loading || generating) {
    return (
      <LoadingSpinner
        message={generating ? 'Generating your study materials...' : 'Loading study materials...'}
      />
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

        <StudyMaterialViewer studyMaterial={material} />
      </div>
    </div>
  );
}
