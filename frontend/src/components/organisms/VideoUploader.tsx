"use client"

import { useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/atoms/Card"
import { Button } from "@/components/atoms/Button"
import { Input } from "@/components/atoms/Input"
import { UploadProgress } from "@/components/molecules/UploadProgress"
import { Upload, FileVideo } from "lucide-react"
import path from "path"

interface VideoUploaderProps {
  onUploadComplete: (videoId: string, filename: string, filePath: string) => void
}

export function VideoUploader({ onUploadComplete }: VideoUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [filename, setFilename] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setFilename(file.name)
    setProgress(0)

    try {
      const formData = new FormData()
      formData.append("file", file)

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const data = await response.json()
      setProgress(100)

      setTimeout(() => {
        onUploadComplete(data.videoId, data.filename, data.filePath)
        setUploading(false)
        setProgress(0)
        setFilename("")
        if (fileInputRef.current) {
          fileInputRef.current.value = ""
        }
      }, 500)
    } catch (error) {
      console.error("Upload error:", error)
      alert("Failed to upload video. Please try again.")
      setUploading(false)
      setProgress(0)
    }
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  if (uploading) {
    return <UploadProgress progress={progress} filename={filename} />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileVideo className="h-6 w-6" />
          Upload Workout Video
        </CardTitle>
        <CardDescription>
          Upload a bench press video for analysis. Supported formats: MP4, MOV, AVI
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center space-y-4 py-8 border-2 border-dashed border-muted rounded-lg">
          <Upload className="h-12 w-12 text-muted-foreground" />
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Click the button below to select a video file
            </p>
            <Button onClick={handleButtonClick} size="lg">
              Choose Video File
            </Button>
          </div>
          <Input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      </CardContent>
    </Card>
  )
}
