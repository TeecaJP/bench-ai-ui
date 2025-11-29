import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const skip = parseInt(searchParams.get('skip') || '0')
    const limit = parseInt(searchParams.get('limit') || '100')
    
    const videos = await prisma.video.findMany({
      orderBy: {
        createdAt: 'desc'
      },
      skip,
      take: limit,
      select: {
        id: true,
        filename: true,
        status: true,
        originalPath: true,
        processedPath: true,
        overallStatus: true,
        hipLiftDetected: true,
        shallowRepDetected: true,
        createdAt: true,
        updatedAt: true,
      }
    })

    const total = await prisma.video.count()

    return NextResponse.json({
      videos,
      total,
      skip,
      limit
    })
  } catch (error) {
    console.error("List videos error:", error)
    return NextResponse.json(
      { error: "Failed to list videos" },
      { status: 500 }
    )
  }
}
