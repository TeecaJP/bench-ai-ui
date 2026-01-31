import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import fs from "fs"
import path from "path"

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const video = await prisma.video.findUnique({
      where: { id: params.id },
      include: {
        analysisData: {
          orderBy: {
            frame: 'asc'
          }
        }
      }
    })

    if (!video) {
      return NextResponse.json(
        { error: "Video not found" },
        { status: 404 }
      )
    }

    // [New] Dynamic Rep Data Injection
    // Since 'reps' is a complex object not in the DB, we read it from the JSON file on disk.
    let reps = [];
    if (video.processedPath) {
        let jsonPath = video.processedPath.replace('.mp4', '.json');
        
        // Robust path check (Docker vs Local)
        if (!fs.existsSync(jsonPath)) {
             if (jsonPath.startsWith('/app/storage')) {
                 jsonPath = jsonPath.replace('/app/storage', 'storage');
             }
        }

        if (fs.existsSync(jsonPath)) {
            try {
                const fileContent = fs.readFileSync(jsonPath, 'utf-8');
                const jsonData = JSON.parse(fileContent);
                if (jsonData.reps) {
                    reps = jsonData.reps;
                }
            } catch (jsonErr) {
                console.error("Failed to read analysis JSON:", jsonErr);
            }
        }
    }

    // Return combined data
    return NextResponse.json({
        ...video,
        reps: reps
    })
  } catch (error) {
    console.error("Fetch video error:", error)
    return NextResponse.json(
      { error: "Failed to fetch video" },
      { status: 500 }
    )
  }
}
