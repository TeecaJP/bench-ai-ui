import { NextRequest, NextResponse } from "next/server"
import { createReadStream, statSync, existsSync } from "fs"
import path from "path"

export async function GET(request: NextRequest) {
  try {
    // Get file path from query parameter
    const searchParams = request.nextUrl.searchParams
    const filePath = searchParams.get('path')

    if (!filePath) {
      return NextResponse.json({ error: "File path required" }, { status: 400 })
    }

    // Convert Docker path to host path if necessary
    const localPath = filePath.startsWith('/app/storage/')
      ? filePath.replace('/app/storage/', 'storage/')
      : filePath

    // Security: Prevent directory traversal
    const normalizedPath = path.normalize(localPath)
    if (normalizedPath.includes('..') || !normalizedPath.startsWith('storage/')) {
      return NextResponse.json({ error: "Invalid file path" }, { status: 403 })
    }

    // Check if file exists
    if (!existsSync(normalizedPath)) {
      return NextResponse.json({ error: "Video file not found" }, { status: 404 })
    }

    // Get file stats
    const stat = statSync(normalizedPath)
    const fileSize = stat.size

    // Check for Range header (for seeking support)
    const range = request.headers.get('range')

    if (range) {
      // Parse range header
      const parts = range.replace(/bytes=/, "").split("-")
      const start = parseInt(parts[0], 10)
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1
      const chunksize = (end - start) + 1

      // Create read stream for the requested range
      const stream = createReadStream(normalizedPath, { start, end })

      // Convert Node.js stream to Web ReadableStream
      const webStream = new ReadableStream({
        start(controller) {
          stream.on('data', (chunk: Buffer) => {
            controller.enqueue(new Uint8Array(chunk))
          })
          stream.on('end', () => {
            controller.close()
          })
          stream.on('error', (err) => {
            controller.error(err)
          })
        },
        cancel() {
          stream.destroy()
        }
      })

      // Return partial content (206)
      return new NextResponse(webStream, {
        status: 206,
        headers: {
          'Content-Range': `bytes ${start}-${end}/${fileSize}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': chunksize.toString(),
          'Content-Type': 'video/mp4',
        }
      })
    } else {
      // No range requested, stream entire file
      const stream = createReadStream(normalizedPath)

      // Convert Node.js stream to Web ReadableStream
      const webStream = new ReadableStream({
        start(controller) {
          stream.on('data', (chunk: Buffer) => {
            controller.enqueue(new Uint8Array(chunk))
          })
          stream.on('end', () => {
            controller.close()
          })
          stream.on('error', (err) => {
            controller.error(err)
          })
        },
        cancel() {
          stream.destroy()
        }
      })

      return new NextResponse(webStream, {
        status: 200,
        headers: {
          'Content-Length': fileSize.toString(),
          'Content-Type': 'video/mp4',
          'Accept-Ranges': 'bytes',
        }
      })
    }
  } catch (error) {
    console.error("Stream error:", error)
    return NextResponse.json(
      { error: "Failed to stream video" },
      { status: 500 }
    )
  }
}
