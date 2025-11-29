"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/atoms/Card"
import { Progress } from "@/components/atoms/Progress"
import { Upload } from "lucide-react"

interface UploadProgressProps {
  progress: number
  filename: string
}

export function UploadProgress({ progress, filename }: UploadProgressProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Uploading Video
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm text-muted-foreground truncate">{filename}</p>
        <Progress value={progress} />
        <p className="text-xs text-muted-foreground text-right">{progress}%</p>
      </CardContent>
    </Card>
  )
}
