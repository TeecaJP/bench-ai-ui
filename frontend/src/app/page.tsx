"use client"

import { useState } from "react"
import { VideoUploader } from "@/components/organisms/VideoUploader"
import { AnalysisDashboard } from "@/components/templates/AnalysisDashboard"
import { Button } from "@/components/atoms/Button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/atoms/Card"
import { Skeleton } from "@/components/atoms/Skeleton"
import { ArrowLeft, Loader2 } from "lucide-react"

export default function HomePage() {
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)

  const handleUploadComplete = async (videoId: string, filename: string, filePath: string) => {
    setCurrentVideoId(videoId)
    setAnalyzing(true)
    setAnalysisResult(null)

    try {
      // Start analysis
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ videoId }),
      })

      if (!response.ok) {
        throw new Error("Analysis failed")
      }

      const data = await response.json()

      // Fetch full video data with analysis points
      const videoResponse = await fetch(`/api/videos/${videoId}`)
      const videoData = await videoResponse.json()

      setAnalysisResult(videoData)
    } catch (error) {
      console.error("Analysis error:", error)
      alert("Failed to analyze video. Please try again.")
    } finally {
      setAnalyzing(false)
    }
  }

  const handleReset = () => {
    setCurrentVideoId(null)
    setAnalyzing(false)
    setAnalysisResult(null)
  }

  return (
    <div className="min-h-screen bg-background">

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {!currentVideoId && !analyzing && !analysisResult && (
          <div className="max-w-2xl mx-auto">
            <VideoUploader onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {analyzing && (
          <div className="max-w-4xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  Analyzing Video...
                </CardTitle>
                <CardDescription>
                  Our AI is processing your workout video. This may take a few moments.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
                <div className="aspect-video w-full">
                  <Skeleton className="h-full w-full" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {analysisResult && !analyzing && (
          <div className="max-w-7xl mx-auto">
            <AnalysisDashboard
              overallStatus={analysisResult.overallStatus}
              hipLiftDetected={analysisResult.hipLiftDetected}
              shallowRepDetected={analysisResult.shallowRepDetected}
              totalFrames={analysisResult.totalFrames}
              fps={analysisResult.fps}
              videoDuration={analysisResult.videoDuration}
              processedVideoPath={analysisResult.processedPath}
              timeSeriesData={analysisResult.analysisData}
              originalVideoPath={analysisResult.originalPath}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-16">
        <div className="container mx-auto px-4 py-6">
          <p className="text-sm text-center text-muted-foreground">
            Powered by YOLO, MediaPipe, and Next.js | Local-First Analysis
          </p>
        </div>
      </footer>
    </div>
  )
}
