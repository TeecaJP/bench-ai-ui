"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { useVideoStatus } from "@/hooks/useVideoStatus"
import { useTranslation } from "@/hooks/useTranslation" // i18n
import { ProcessingStatus, LoadingSpinner } from "@/components/molecules/LoadingStatus"
import { Badge } from "@/components/atoms/Badge"
import { BarHeightChart } from "@/components/organisms/BarHeightChart"
import { RepAnalysisPanel } from "@/components/organisms/RepAnalysisPanel"
import { Card } from "@/components/atoms/Card"

interface VideoDetailPageProps {
  params: {
    id: string
  }
}

export default function VideoDetailPage({ params }: VideoDetailPageProps) {
  const router = useRouter()
  const { t } = useTranslation() // Hook
  const { video, isLoading, error, isProcessing, isCompleted } = useVideoStatus({
    videoId: params.id,
    pollingInterval: 5000,
    enabled: true
  })

  // Auto-trigger analysis for PENDING videos
  useEffect(() => {
    if (video && video.status === 'PENDING') {
      const triggerAnalysis = async () => {
        try {
          const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videoId: params.id })
          })

          if (!response.ok) {
            console.error('Failed to trigger analysis:', response.statusText)
          }
        } catch (error) {
          console.error('Error triggering analysis:', error)
        }
      }

      triggerAnalysis()
    }
  }, [video?.status, params.id])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner text={t.common.loading} />
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="h-full flex items-center justify-center px-4">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center max-w-md">
          <p className="text-destructive">{error || 'Video not found'}</p>
          <button
            onClick={() => router.push('/videos')}
            className="mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {t.common.backToLibrary}
          </button>
        </div>
      </div>
    )
  }

  if (isProcessing) {
    return (
      <div className="h-full flex items-center justify-center">
        <ProcessingStatus
          message={t.common.processing}
          subMessage={t.common.processingDesc}
        />
      </div>
    )
  }

  // Helper to map status to text
  const getOverallStatusText = (status: string | null) => {
    if (!status) return t.common.na;
    if (status.includes('FAIL')) return t.status.failed;
    if (status === 'OK') return t.status.ok;
    return status;
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header Bar */}
      <div className="border-b px-6 py-4 flex-shrink-0 bg-background/95 backdrop-blur z-10">
        <button
          onClick={() => router.push('/videos')}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="h-4 w-4" />
          {t.common.backToLibrary}
        </button>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h1 className="text-2xl font-bold tracking-tight">{video.filename}</h1>
          <div className="flex gap-2">
            <Badge variant={video.status === 'COMPLETED' ? 'default' : 'secondary'}>
              {video.status}
            </Badge>
            {isCompleted && video.overallStatus && (
              <Badge variant={video.overallStatus === 'OK' ? 'default' : 'destructive'}>
                {getOverallStatusText(video.overallStatus)}
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area - Dashboard Layout */}
      {isCompleted && video.processedPath ? (
        <div className="flex-1 overflow-hidden">
          <div className="h-full grid grid-cols-1 md:grid-cols-[60%_40%] divide-y md:divide-y-0 md:divide-x">

            {/* Left Column: Video & Chart (Scrollable if needed) */}
            <div className="h-full flex flex-col overflow-y-auto">
              {/* Video Player Container */}
              <div className="bg-black/5 p-4 flex items-center justify-center min-h-[400px] shrink-0">
                <video
                  controls
                  className="max-w-full max-h-[60vh] object-contain shadow-lg rounded-md bg-black"
                  src={`/api/stream?path=${encodeURIComponent(video.processedPath)}`}
                >
                  Your browser does not support the video tag.
                </video>
              </div>

              {/* Chart Section */}
              {video.analysisData && video.analysisData.length > 0 && (
                <div className="p-6 border-t bg-background">
                  <BarHeightChart
                    data={video.analysisData}
                    title={t.analysis.barHeightTitle}
                    description={t.analysis.barHeightDesc}
                  />
                </div>
              )}
            </div>

            {/* Right Column: Info & Analysis (Scrollable) */}
            <div className="h-full overflow-y-auto bg-muted/5 p-6 space-y-6">

              {/* 1. Video Info Card */}
              <Card className="p-4 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-xs text-muted-foreground uppercase">{t.analysis.totalFrames}</div>
                  <div className="font-mono font-bold text-lg">{video.totalFrames || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground uppercase">{t.analysis.fps}</div>
                  <div className="font-mono font-bold text-lg">{video.fps || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground uppercase">{t.analysis.duration}</div>
                  <div className="font-mono font-bold text-lg">{video.videoDuration ? `${video.videoDuration.toFixed(1)}s` : '-'}</div>
                </div>
              </Card>

              {/* 2. Analysis Panel (Sliders + Rep List) */}
              <div className="rounded-lg">
                {/* Note: RepAnalysisPanel now handles its own layout (Settings + List) */}
                {/* We pass a custom className to make it fit nicely if needed, but standard block is fine */}
                {video.reps && video.reps.length > 0 ? (
                  <RepAnalysisPanel analysis={{ ...video, reps: video.reps } as any} />
                ) : (
                  <div className="text-center p-8 text-muted-foreground border border-dashed rounded-lg">
                    {t.repPanel.noReps}
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="rounded-lg border border-dashed p-12 text-center max-w-lg">
            <LoadingSpinner />
            <p className="mt-4 text-muted-foreground">
              {video.status === 'FAILED' ? t.status.failed : t.common.processingDesc}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
