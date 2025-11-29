"use client"

import { useState } from "react"
import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { Trash2, Video, Clock } from "lucide-react"
import { Badge } from "@/components/atoms/Badge"
import { useVideoStatus } from "@/hooks/useVideoStatus"

interface VideoCardProps {
  video: {
    id: string
    filename: string
    status: string
    createdAt: string
    overallStatus?: string | null
  }
  onDelete: (id: string) => void
}

export function VideoCard({ video, onDelete }: VideoCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  
  // Use polling hook for real-time status updates if processing
  const { video: liveVideo } = useVideoStatus({
    videoId: video.id,
    enabled: video.status === 'PROCESSING' || video.status === 'PENDING',
    pollingInterval: 5000
  })

  const currentStatus = liveVideo?.status || video.status
  const currentOverallStatus = liveVideo?.overallStatus || video.overallStatus

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault() // Prevent navigation
    e.stopPropagation()

    if (!confirm(`Delete "${video.filename}"?`)) {
      return
    }

    setIsDeleting(true)
    try {
      await onDelete(video.id)
    } catch (error) {
      console.error('Delete failed:', error)
      setIsDeleting(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'default'
      case 'PROCESSING':
        return 'secondary'
      case 'PENDING':
        return 'outline'
      case 'FAILED':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  return (
    <Link href={`/videos/${video.id}`}>
      <div className="group relative rounded-lg border p-4 hover:shadow-lg transition-all cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Video className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <h3 className="font-semibold truncate">{video.filename}</h3>
            </div>
            
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
              <Clock className="h-4 w-4" />
              <span>{formatDistanceToNow(new Date(video.createdAt), { addSuffix: true })}</span>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge variant={getStatusColor(currentStatus)}>
                {currentStatus}
              </Badge>
              
              {currentStatus === 'COMPLETED' && currentOverallStatus && (
                <Badge variant={currentOverallStatus === 'OK' ? 'default' : 'destructive'}>
                  {currentOverallStatus}
                </Badge>
              )}
            </div>
          </div>

          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 rounded-md hover:bg-destructive hover:text-destructive-foreground transition-colors disabled:opacity-50"
            aria-label="Delete video"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      </div>
    </Link>
  )
}
