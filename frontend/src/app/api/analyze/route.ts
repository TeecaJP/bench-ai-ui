import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import path from "path"
import fs from 'fs'

// Reduced timeout since we return immediately
export const maxDuration = 30 // seconds

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { videoId } = body

    if (!videoId) {
      return NextResponse.json({ error: "Video ID required" }, { status: 400 })
    }

    // Get video from database
    const video = await prisma.video.findUnique({
      where: { id: videoId },
    })

    if (!video) {
      return NextResponse.json({ error: "Video not found" }, { status: 404 })
    }

    // Update status to PROCESSING
    await prisma.video.update({
      where: { id: videoId },
      data: { status: "PROCESSING" },
    })

    // Generate output path
    const outputFilename = `processed_${path.basename(video.originalPath)}`
    const outputPath = path.join(
      path.dirname(video.originalPath).replace("original-videos", "processed-videos"),
      outputFilename
    )

    // Trigger backend processing (fire-and-forget)
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Start async processing - don't await
    fetch(`${backendUrl}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_video_path: video.originalPath,
        output_video_path: outputPath,
      }),
    }).then(async (response) => {
      if (response.status === 202) {
        // Processing started - poll for completion
        pollForCompletion(videoId, outputPath)
      } else {
        // Backend error
        console.error(`Backend returned ${response.status} for video ${videoId}`)
        await prisma.video.update({
          where: { id: videoId },
          data: { status: "FAILED" },
        })
      }
    }).catch(async (error) => {
      // Network error
      console.error('Failed to trigger analysis:', error)
      await prisma.video.update({
        where: { id: videoId },
        data: { status: "FAILED" },
      })
    })

   // Return immediately to client
    return NextResponse.json({
      status: "processing_started",
      message: "Video analysis started. Poll /api/videos/[id] for status.",
      videoId: videoId
    }, { status: 202 })

  } catch (error) {
    console.error("Analyze API error:", error)
    return NextResponse.json(
      { error: "Failed to start analysis" },
      { status: 500 }
    )
  }
}

// Background polling function
async function pollForCompletion(videoId: string, outputPath: string) {
  const maxAttempts = 120 // 10 minutes
  let attempts = 0

  const pollInterval = setInterval(async () => {
    attempts++

    try {
      // Check if processed video exists
      const localPath = outputPath.replace('/app/storage/', 'storage/')
      
        if (fs.existsSync(localPath)) {
        // Check if JSON result file exists
        const jsonPath = localPath.replace('.mp4', '.json')
        
        // Wait for JSON file to be written (race condition fix)
        if (!fs.existsSync(jsonPath)) {
             // If MP4 exists but JSON doesn't, wait for next poll cycle
             // unless we are close to timeout, then proceed with partial data
             if (attempts < maxAttempts - 5) {
               return 
             }
        }

        let analysisResults: any = {}
        if (fs.existsSync(jsonPath)) {
          try {
            const jsonContent = fs.readFileSync(jsonPath, 'utf-8')
            analysisResults = JSON.parse(jsonContent)
          } catch (e) {
            console.error('Failed to read analysis results JSON:', e)
          }
        }

        // Processing complete!
        clearInterval(pollInterval)

        await prisma.video.update({
          where: { id: videoId },
          data: {
            status: "COMPLETED",
            processedPath: outputPath,
            // Update analysis results from JSON
            overallStatus: analysisResults.overall_status,
            hipLiftDetected: analysisResults.hip_lift_detected,
            hipLiftStatus: analysisResults.hip_lift_status,
            shallowRepDetected: analysisResults.shallow_rep_detected,
            shallowRepStatus: analysisResults.shallow_rep_status,
            totalFrames: analysisResults.total_frames,
            fps: analysisResults.fps,
            videoDuration: analysisResults.video_duration,
          },
        })

        console.log(`Video ${videoId} completed after ${attempts * 5}s`)
      } else if (attempts >= maxAttempts) {
        // Timeout
        clearInterval(pollInterval)
        await prisma.video.update({
          where: { id: videoId },
          data: { status: "FAILED" },
        })
        console.error(`Video ${videoId} timeout after ${maxAttempts * 5}s`)
      }
    } catch (error) {
      console.error(`Polling error for ${videoId}:`, error)
    }
  }, 5000) // 5 second interval
}
