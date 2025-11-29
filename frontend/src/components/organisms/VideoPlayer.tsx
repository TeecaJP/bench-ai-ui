"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/atoms/Card"
import { Button } from "@/components/atoms/Button"
import { StatusBadge } from "@/components/molecules/StatusBadge"
import { Play, Download } from "lucide-react"

interface VideoPlayerProps {
  videoSrc: string
  title: string
  status?: string
  description?: string
  onDownload?: () => void
}

export function VideoPlayer({ videoSrc, title, status, description, onDownload }: VideoPlayerProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Play className="h-5 w-5" />
              {title}
            </CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {status && <StatusBadge status={status} />}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
          <video
            src={videoSrc}
            controls
            className="w-full h-full"
          >
            Your browser does not support the video tag.
          </video>
        </div>
        {onDownload && (
          <Button onClick={onDownload} variant="outline" className="w-full">
            <Download className="h-4 w-4 mr-2" />
            Download Processed Video
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
