import { useState, useEffect } from 'react'

interface Video {
  id: string
  filename: string
  status: string
  originalPath: string | null
  processedPath: string | null
  overallStatus: string | null
  hipLiftDetected: boolean | null
  hipLiftStatus: string | null
  shallowRepDetected: boolean | null
  shallowRepStatus: string | null
  totalFrames: number | null
  fps: number | null
  videoDuration: number | null
  createdAt: string
  updatedAt: string
}

interface UseVideoStatusOptions {
  videoId: string | null
  pollingInterval?: number
  enabled?: boolean
}

export function useVideoStatus({
  videoId,
  pollingInterval = 5000,
  enabled = true
}: UseVideoStatusOptions) {
  const [video, setVideo] = useState<Video | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!videoId || !enabled) {
      return
    }

    let intervalId: NodeJS.Timeout | null = null
    let isMounted = true

    const fetchStatus = async () => {
      try {
        setIsLoading(true)
        const response = await fetch(`/api/videos/${videoId}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch video status: ${response.statusText}`)
        }

        const data = await response.json()
        
        if (isMounted) {
          setVideo(data)
          setError(null)

          // Stop polling if completed or failed
          if (data.status === 'COMPLETED' || data.status === 'FAILED') {
            if (intervalId) {
              clearInterval(intervalId)
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unknown error')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    // Initial fetch
    fetchStatus()

    // Set up polling
    intervalId = setInterval(fetchStatus, pollingInterval)

    return () => {
      isMounted = false
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [videoId, pollingInterval, enabled])

  return {
    video,
    isLoading,
    error,
    isProcessing: video?.status === 'PROCESSING' || video?.status === 'PENDING',
    isCompleted: video?.status === 'COMPLETED',
    isFailed: video?.status === 'FAILED'
  }
}
