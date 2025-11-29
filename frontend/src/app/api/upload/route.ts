import { NextRequest, NextResponse } from "next/server"
import { writeFile, mkdir } from "fs/promises"
import { prisma } from "@/lib/prisma"
import path from "path"
import { randomUUID } from "crypto"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    
    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    // Create storage directory if it doesn't exist
    // Use /app/storage in Docker container (mounted volume)
    const storageDir = "/app/storage/original-videos"
    await mkdir(storageDir, { recursive: true })

    // Generate unique filename
    const fileExt = path.extname(file.name)
    const uniqueFilename = `${randomUUID()}${fileExt}`
    const filePath = path.join(storageDir, uniqueFilename)

    // Save file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    // Create database record
    const video = await prisma.video.create({
      data: {
        filename: file.name,
        originalPath: filePath,
        status: "PENDING",
      },
    })

    return NextResponse.json({
      videoId: video.id,
      filename: file.name,
      filePath: filePath,
    })
  } catch (error) {
    console.error("Upload error:", error)
    return NextResponse.json(
      { error: "Failed to upload file" },
      { status: 500 }
    )
  }
}
