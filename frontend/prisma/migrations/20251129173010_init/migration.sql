-- CreateTable
CREATE TABLE "videos" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "filename" TEXT NOT NULL,
    "originalPath" TEXT NOT NULL,
    "processedPath" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "overallStatus" TEXT,
    "hipLiftDetected" BOOLEAN,
    "hipLiftStatus" TEXT,
    "shallowRepDetected" BOOLEAN,
    "shallowRepStatus" TEXT,
    "totalFrames" INTEGER,
    "fps" INTEGER,
    "videoDuration" REAL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "analysis_data_points" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "videoId" TEXT NOT NULL,
    "frame" INTEGER NOT NULL,
    "timestamp" REAL NOT NULL,
    "hipY" REAL,
    "elbowY" REAL,
    "shoulderY" REAL,
    "benchDetected" BOOLEAN NOT NULL,
    "barDetected" BOOLEAN NOT NULL,
    CONSTRAINT "analysis_data_points_videoId_fkey" FOREIGN KEY ("videoId") REFERENCES "videos" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "analysis_data_points_videoId_idx" ON "analysis_data_points"("videoId");
