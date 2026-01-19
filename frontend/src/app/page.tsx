"use client"

import { useRouter } from "next/navigation"
import { VideoUploader } from "@/components/organisms/VideoUploader"

export default function HomePage() {
  const router = useRouter()

  const handleUploadComplete = (videoId: string, filename: string, filePath: string) => {
    // Redirect to video detail page immediately after upload
    router.push(`/videos/${videoId}`)
  }

  return (
    <div className="h-full bg-background flex flex-col items-center justify-center">
      {/* Main Content */}
      <main className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto">
          <VideoUploader onUploadComplete={handleUploadComplete} />
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8">
        <p className="text-sm text-center text-muted-foreground">
          Powered by YOLO, MediaPipe, and Next.js | Local-First Analysis
        </p>
      </footer>
    </div>
  )
}
