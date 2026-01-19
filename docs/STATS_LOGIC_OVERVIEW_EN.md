# Stats Display Logic - Overview

This document provides an overview of how the stats displayed on the processed video page are determined.

## Quick Reference

### Overall Status Logic

```
IF (Hip Lift Detected OR Shallow Rep Detected):
    Overall Status = "EGO LIFT" (Red Badge)
ELSE:
    Overall Status = "GOOD REP" (Green Badge)
```

**Files**:
- Logic: `ml-backend/app/logic.py` (lines 276-282, 330-334)
- Display: `frontend/src/app/videos/[id]/page.tsx` (lines 127-137)

### Hip Lift Detection Logic

**Algorithm**:
1. Establish baseline distance between hip and bench (first frame)
2. Calculate dynamic threshold: `baseline × HIP_LIFT_RATIO (0.5)`
3. Detect violation: If `current_distance > baseline + threshold`

**Result**:
- `OK` - No hip lift detected (Green Badge)
- `FAIL: HIP LIFT` - Hip lift detected (Red Badge)

**Files**:
- Logic: `ml-backend/app/logic.py` (lines 206-221)
- Display: `frontend/src/app/videos/[id]/page.tsx` (lines 144-147)
- Config: `HIP_LIFT_RATIO = 0.5`

### Shallow Rep Detection Logic

**Algorithm** (State Machine):
1. **Rep Start**: Bar moves close to shoulders
   - Track minimum elbow position at bottom
2. **Rep End**: Bar moves away from shoulders
   - Check if elbow at lowest point is above bench
   - Threshold: `bench_top + (torso_length × SHALLOW_REP_RATIO)`

**Result**:
- `OK` - No shallow rep detected (Green Badge)
- `FAIL: ELBOW DEPTH` - Shallow rep detected (Red Badge)

**Files**:
- Logic: `ml-backend/app/logic.py` (lines 223-256)
- Display: `frontend/src/app/videos/[id]/page.tsx` (lines 149-154)
- Config: `SHALLOW_REP_RATIO = 0.05`

## Data Flow

```
Video Upload → ML Backend Analysis → JSON Results → Database → UI Display
     ↓              ↓                      ↓            ↓          ↓
  Upload API    YOLO + MediaPipe      Save .json    Update DB   Show Stats
```

### 1. ML Analysis Phase

**File**: `ml-backend/app/logic.py` - `WorkoutAnalyzer.analyze_video()`

```python
for each frame:
    1. YOLO Detection → Detect bench and bar boxes
    2. MediaPipe Pose → Extract hip, elbow, shoulder positions
    3. Hip Lift Check → Compare hip-bench distance to baseline
    4. Shallow Rep Check → State machine tracking bar-shoulder distance
    5. Store frame data → Append to time_series_data
```

**Output**: JSON file with analysis results
```json
{
  "overall_status": "GOOD REP" | "EGO LIFT",
  "hip_lift_status": "OK" | "FAIL: HIP LIFT",
  "shallow_rep_status": "OK" | "FAIL: ELBOW DEPTH",
  "hip_lift_detected": true | false,
  "shallow_rep_detected": true | false,
  "time_series_data": [...],
  "total_frames": 809,
  "fps": 29,
  "video_duration": 27.9
}
```

### 2. Database Update Phase

**File**: `frontend/src/app/api/analyze/route.ts` - `pollForCompletion()`

Polls every 5 seconds checking for:
1. Processed video file exists
2. JSON results file exists
3. Updates database with results

### 3. UI Display Phase

**File**: `frontend/src/app/videos/[id]/page.tsx`

Displays three cards:
1. **Overall Status Card** - Shows GOOD REP or EGO LIFT
2. **Form Analysis Card** - Shows Hip Lift and Shallow Rep status
3. **Video Info Card** - Shows total frames, FPS, duration

## Technology Stack

### Computer Vision Models

1. **YOLO (Object Detection)**
   - Purpose: Detect bench and barbell
   - Model: Custom trained `best.pt`
   - Classes:
     - Class 0: Barbell
     - Class 1: Bench

2. **MediaPipe Pose (Pose Estimation)**
   - Purpose: Extract body landmarks (33 points)
   - Key points used:
     - Hip (LEFT_HIP, RIGHT_HIP)
     - Elbow (LEFT_ELBOW, RIGHT_ELBOW)
     - Shoulder (LEFT_SHOULDER, RIGHT_SHOULDER)

### Processing Pipeline

```
Input Video → OpenCV → Frame by Frame Processing
                ↓
         ┌──────┴──────┐
    YOLO Detection   MediaPipe Pose
         │                │
         └────────┬───────┘
                  ↓
         Analysis Logic
         (Hip Lift + Shallow Rep)
                  ↓
         Annotated Video Output
         (H.264 codec for web)
                  ↓
         JSON Results File
```

## Configuration Constants

**File**: `ml-backend/app/logic.py` (lines 28-32)

```python
# Hip Lift Detection Sensitivity (0.0 - 1.0)
# Lower = stricter detection
HIP_LIFT_RATIO = 0.5  # 50% of baseline distance

# Shallow Rep Detection Sensitivity (0.0 - 1.0)
# Lower = stricter detection
SHALLOW_REP_RATIO = 0.05  # 5% of torso length

# Elbow Position Smoothing
# Higher = smoother but slower response
SMOOTHING_WINDOW_SIZE = 5  # frames
```

## Database Schema

**File**: `frontend/prisma/schema.prisma`

```prisma
model Video {
  id                 String   @id
  filename           String
  status             String   // PENDING, PROCESSING, COMPLETED, FAILED
  
  // Analysis Results
  overallStatus      String?  // "GOOD REP", "EGO LIFT"
  hipLiftDetected    Boolean?
  hipLiftStatus      String?  // "OK", "FAIL: HIP LIFT"
  shallowRepDetected Boolean?
  shallowRepStatus   String?  // "OK", "FAIL: ELBOW DEPTH"
  totalFrames        Int?
  fps                Int?
  videoDuration      Float?
  
  // Relations
  analysisData       AnalysisDataPoint[]
}
```

## Debugging Tips

### Check Analysis Results

```bash
# View JSON results file
cat storage/processed-videos/processed_<video_name>.json

# Check backend logs
docker-compose logs ml-backend -f

# Check frontend logs
docker-compose logs frontend -f
```

### Common Issues

1. **Stats show "N/A"**
   - Cause: Analysis not completed or JSON file missing
   - Solution: Check if JSON file exists in `storage/processed-videos/`

2. **False positive detections**
   - Cause: Poor bench/bar detection by YOLO
   - Solution: Check video quality, ensure bench and bar are visible

3. **No detection at all**
   - Cause: Models not loaded or video codec issue
   - Solution: Verify YOLO model exists, check OpenCV can read video

## Customization Guide

To adjust detection sensitivity, modify constants in `ml-backend/app/logic.py`:

```python
# Make Hip Lift detection stricter (detect smaller lifts)
HIP_LIFT_RATIO = 0.3  # Reduced from 0.5

# Make Shallow Rep detection more lenient
SHALLOW_REP_RATIO = 0.08  # Increased from 0.05

# Increase smoothing (less jittery but slower response)
SMOOTHING_WINDOW_SIZE = 10  # Increased from 5
```

After changes, restart the backend:
```bash
docker-compose restart ml-backend
```

## Key Files Reference

### Backend (ML Analysis)
- `ml-backend/app/logic.py` - Core analysis logic
- `ml-backend/app/main.py` - FastAPI endpoints
- `ml-backend/models/best.pt` - YOLO model

### Frontend (UI Display)
- `frontend/src/app/videos/[id]/page.tsx` - Video detail page
- `frontend/src/app/api/analyze/route.ts` - Analysis trigger and polling
- `frontend/prisma/schema.prisma` - Database schema
- `frontend/src/hooks/useVideoStatus.ts` - Video status hook

### Configuration
- `ml-backend/app/logic.py` - Detection thresholds (lines 28-32)
- `docker-compose.yml` - Service configuration
- `frontend/.env` - Environment variables

## Related Documentation

- Main README: `README.md`
- Implementation Notes: `IMPLEMENTATION_NOTES.md`
- Japanese Documentation: `STATS_LOGIC_DOCUMENTATION.md`

---

Last Updated: 2026-01-19
