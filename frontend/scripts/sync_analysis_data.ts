import { PrismaClient } from '@prisma/client'
import fs from 'fs'
import path from 'path'

const prisma = new PrismaClient()

async function syncAnalysisData() {
  console.log('Starting sync of analysis data points...')

  try {
    // 1. Get all COMPLETED videos
    const videos = await prisma.video.findMany({
      where: { status: 'COMPLETED' },
      include: {
        analysisData: {
          take: 1
        }
      }
    })

    console.log(`Found ${videos.length} completed videos.`)

    for (const video of videos) {
      // 2. Skip if it already has data points
      if (video.analysisData.length > 0) {
        console.log(`Video ${video.filename} (${video.id}) already has data points. Skipping.`)
        continue
      }

      console.log(`Syncing data for video: ${video.filename} (${video.id})`)

      if (!video.processedPath) {
        console.warn(`Video ${video.id} has no processedPath. Skipping.`)
        continue
      }

      // 3. Locate JSON file
      // Convert /app/storage/ to local storage/ path if needed
      const localProcessedPath = video.processedPath.replace('/app/storage/', 'storage/')
      const jsonPath = localProcessedPath.replace('.mp4', '.json')

      if (!fs.existsSync(jsonPath)) {
        console.warn(`JSON file not found for video ${video.id} at ${jsonPath}`)
        continue
      }

      // 4. Read and parse JSON
      try {
        const jsonContent = fs.readFileSync(jsonPath, 'utf-8')
        const analysisResults = JSON.parse(jsonContent)

        if (analysisResults.time_series_data && Array.isArray(analysisResults.time_series_data)) {
          console.log(`  Found ${analysisResults.time_series_data.length} data points in JSON.`)

          // 5. Insert data points individually for SQLite compatibility
          for (const point of analysisResults.time_series_data) {
            await prisma.analysisDataPoint.create({
              data: {
                videoId: video.id,
                frame: point.frame,
                timestamp: point.timestamp,
                hipY: point.hip_y,
                elbowY: point.elbow_y,
                shoulderY: point.shoulder_y,
                barY: point.bar_y,
                benchDetected: point.bench_detected || false,
                barDetected: point.bar_detected || false,
              }
            })
          }

          console.log(`  Successfully synced ${video.filename}`)
        } else {
          console.warn(`  No time_series_data found in JSON for ${video.filename}`)
        }
      } catch (err) {
        console.error(`  Failed to process JSON for ${video.id}:`, err)
      }
    }

    console.log('Sync complete!')
  } catch (error) {
    console.error('Error during sync:', error)
  } finally {
    await prisma.$disconnect()
  }
}

syncAnalysisData()
