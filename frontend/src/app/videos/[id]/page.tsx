"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { useVideoStatus } from "@/hooks/useVideoStatus"
import { ProcessingStatus, LoadingSpinner } from "@/components/molecules/LoadingStatus"
import { Badge } from "@/components/atoms/Badge"
import { BarHeightChart } from "@/components/organisms/BarHeightChart"

interface VideoDetailPageProps {
  params: {
    id: string
  }
}

export default function VideoDetailPage({ params }: VideoDetailPageProps) {
  const router = useRouter()
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
        <LoadingSpinner text="Loading video..." />
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
            Back to Library
          </button>
        </div>
      </div>
    )
  }

  if (isProcessing) {
    return (
      <div className="h-full flex items-center justify-center">
        <ProcessingStatus 
          message="Processing video..."
          subMessage="This may take several minutes. You can close this page and come back later."
        />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header Bar */}
      <div className="border-b px-6 py-4 flex-shrink-0">
        <button
          onClick={() => router.push('/videos')}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-3"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Library
        </button>

        <h1 className="text-2xl font-bold tracking-tight mb-2">{video.filename}</h1>
        <div className="flex gap-2">
          <Badge variant={video.status === 'COMPLETED' ? 'default' : 'secondary'}>
            {video.status}
          </Badge>
          {isCompleted && video.overallStatus && (
            <Badge variant={video.overallStatus === 'OK' ? 'default' : 'destructive'}>
              {video.overallStatus}
            </Badge>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {isCompleted && video.processedPath ? (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-[60%_40%]">
            {/* Left: Video Player */}
            <div className="flex items-center justify-center bg-black/5 p-4 h-[40vh] md:h-[60vh]">
              <video
                controls
                className="max-w-full max-h-full object-contain"
                src={`/api/stream?path=${encodeURIComponent(video.processedPath)}`}
              >
                Your browser does not support the video tag.
              </video>
            </div>

            {/* Right: Stats Panel */}
            <div className="p-6 border-l">
              <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
              
              <div className="space-y-4">
                {/* Overall Status Card */}
                <div className="rounded-lg border p-4">
                  <h3 className="font-semibold mb-2">Overall Status</h3>
                  <div className="mt-2">
                    <Badge 
                      variant={video.overallStatus?.includes('GOOD') ? 'default' : 'destructive'}
                      className="text-lg px-3 py-1"
                    >
                      {video.overallStatus || (video.status === 'COMPLETED' ? 'N/A' : 'PROCESSING')}
                    </Badge>
                  </div>
                </div>

                {/* Form Analysis Card */}
                <div className="rounded-lg border p-4">
                  <h3 className="font-semibold mb-2">Form Analysis</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span>Hip Lift:</span>
                      <Badge variant={video.hipLiftDetected ? 'destructive' : 'default'}>
                        {video.hipLiftStatus || 'N/A'}
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Shallow Rep:</span>
                      <Badge variant={video.shallowRepDetected ? 'destructive' : 'default'}>
                        {video.shallowRepStatus || 'N/A'}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Video Info Card */}
                <div className="rounded-lg border p-4">
                  <h3 className="font-semibold mb-2">Video Info</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Total Frames:</span>
                      <span>{video.totalFrames || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>FPS:</span>
                      <span>{video.fps || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Duration:</span>
                      <span>{video.videoDuration ? `${video.videoDuration.toFixed(1)}s` : 'N/A'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bar Height Chart - Full Width Below */}
          {video.analysisData && video.analysisData.length > 0 && (
            <div className="p-6 border-t">
              <BarHeightChart 
                data={video.analysisData} 
                title="Bar Height Over Time"
                description="Vertical position of the bar during the workout (lower values indicate bar is closer to chest)"
              />
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="rounded-lg border border-dashed p-12 text-center">
            <p className="text-muted-foreground">
              {video.status === 'FAILED' ? 'Analysis failed' : 'No analysis results available'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
