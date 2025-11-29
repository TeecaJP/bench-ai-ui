import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const video = await prisma.video.findUnique({
      where: { id: params.id },
      include: {
        analysisData: {
          orderBy: { frame: 'asc' }
        }
      }
    })

    if (!video) {
      return NextResponse.json({ error: "Video not found" }, { status: 404 })
    }

    return NextResponse.json(video)
  } catch (error) {
    console.error("Error fetching video:", error)
    return NextResponse.json(
      { error: "Failed to fetch video" },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const videoId = params.id

    // Get video info before deleting
    const video = await prisma.video.findUnique({
      where: { id: videoId }
    })

    if (!video) {
      return NextResponse.json({ error: "Video not found" }, { status: 404 })
    }

    // Delete from database (cascades to analysisDataPoints)
    await prisma.video.delete({
      where: { id: videoId }
    })

    // Delete physical files via backend API
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const queryParams = new URLSearchParams()
    if (video.originalPath) {
      queryParams.append('original_path', video.originalPath)
    }
    if (video.processedPath) {
      queryParams.append('processed_path', video.processedPath)
    }

    try {
      const response = await fetch(
        `${backendUrl}/videos/${videoId}?${queryParams.toString()}`,
        { method: 'DELETE' }
      )
      
      if (!response.ok) {
        console.error(`Backend file deletion failed: ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to delete files from backend:', error)
      // Continue anyway - DB is already deleted
    }

    return NextResponse.json({
      success: true,
      message: "Video deleted successfully"
    })
  } catch (error) {
    console.error("Delete video error:", error)
    return NextResponse.json(
      { error: "Failed to delete video" },
      { status: 500 }
    )
  }
}
