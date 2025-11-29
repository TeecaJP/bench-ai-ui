"use client"

import { useEffect, useState } from "react"
import { VideoCard } from "@/components/molecules/VideoCard"
import { LoadingSpinner } from "@/components/molecules/LoadingStatus"

interface Video {
  id: string
  filename: string
  status: string
  createdAt: string
  overallStatus?: string|null
}

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/videos')
      
      if (!response.ok) {
        throw new Error('Failed to fetch videos')
      }

      const data = await response.json()
      setVideos(data.videos || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load videos')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/videos/${id}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Delete failed')
      }

      // Remove from UI immediately
      setVideos(prev => prev.filter(v => v.id !== id))
    } catch (error) {
      console.error('Delete error:', error)
      alert('Failed to delete video')
    }
  }

  if (isLoading) {
    return (
      <div className="container py-12">
        <LoadingSpinner text="Loading videos..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="container py-12">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-destructive">{error}</p>
          <button
            onClick={fetchVideos}
            className="mt-4 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Video Library</h1>
        <p className="text-muted-foreground mt-2">
          All your uploaded workout videos
        </p>
      </div>

      {videos.length === 0 ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-muted-foreground mb-4">No videos yet</p>
          <a
            href="/"
            className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            Upload your first video
          </a>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {videos.map(video => (
            <VideoCard
              key={video.id}
              video={video}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
