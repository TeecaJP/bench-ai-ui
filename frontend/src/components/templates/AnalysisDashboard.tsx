"use client"

import { MetricCard } from "@/components/molecules/MetricCard"
import { TimeSeriesChart } from "@/components/organisms/TimeSeriesChart"
import { VideoPlayer } from "@/components/organisms/VideoPlayer"
import type { TimeSeriesDataPoint } from "@/lib/api"
import { formatDuration } from "@/lib/utils"

interface AnalysisDashboardProps {
  overallStatus: string
  hipLiftDetected: boolean
  shallowRepDetected: boolean
  totalFrames: number
  fps: number
  videoDuration: number
  processedVideoPath: string
  timeSeriesData: TimeSeriesDataPoint[]
  originalVideoPath?: string
}

export function AnalysisDashboard({
  overallStatus,
  hipLiftDetected,
  shallowRepDetected,
  totalFrames,
  fps,
  videoDuration,
  processedVideoPath,
  timeSeriesData,
  originalVideoPath,
}: AnalysisDashboardProps) {
  const handleDownload = () => {
    // Create a download link
    const link = document.createElement("a")
    link.href = `/api/download?path=${encodeURIComponent(processedVideoPath)}`
    link.download = processedVideoPath.split("/").pop() || "processed_video.mp4"
    link.click()
  }

  return (
    <div className="space-y-6">
      {/* Video Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {originalVideoPath && (
          <VideoPlayer
            videoSrc={`/api/video?path=${encodeURIComponent(originalVideoPath)}`}
            title="Original Video"
            description="Uploaded workout video"
          />
        )}
        <VideoPlayer
          videoSrc={`/api/video?path=${encodeURIComponent(processedVideoPath)}`}
          title="Processed Video"
          description="Video with AI analysis overlay"
          status={overallStatus}
          onDownload={handleDownload}
        />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Overall Status"
          status={overallStatus === "OK" ? "success" : "warning"}
          metrics={[
            { label: "Result", value: overallStatus },
          ]}
        />
        <MetricCard
          title="Form Issues"
          status={hipLiftDetected || shallowRepDetected ? "warning" : "success"}
          metrics={[
            { label: "Hip Lift", value: hipLiftDetected ? "Detected" : "None" },
            { label: "Shallow Reps", value: shallowRepDetected ? "Detected" : "None" },
          ]}
        />
        <MetricCard
          title="Video Info"
          status="info"
          metrics={[
            { label: "Duration", value: formatDuration(videoDuration) },
            { label: "FPS", value: fps },
            { label: "Total Frames", value: totalFrames },
          ]}
        />
      </div>

      {/* Time Series Chart */}
      {timeSeriesData.length > 0 && (
        <TimeSeriesChart
          data={timeSeriesData}
          description="Track hip, elbow, and shoulder positions throughout the exercise"
        />
      )}
    </div>
  )
}
