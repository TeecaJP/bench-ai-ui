import { NextRequest, NextResponse } from "next/server"
import { readFile } from "fs/promises"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const filePath = searchParams.get("path")

    if (!filePath) {
      return NextResponse.json({ error: "Path required" }, { status: 400 })
    }

    const fileBuffer = await readFile(filePath)
    
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "video/mp4",
        "Content-Length": fileBuffer.length.toString(),
      },
    })
  } catch (error) {
    console.error("Video serve error:", error)
    return NextResponse.json(
      { error: "Failed to load video" },
      { status: 500 }
    )
  }
}
