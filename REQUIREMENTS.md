# Project Requirements Document: Local Workout Analysis App

## 1. Project Overview
This project is a local-first web application that analyzes workout videos (specifically bench press) using computer vision.
Users run the application locally using Docker. It consists of a Next.js frontend and a Python (FastAPI) backend.

## 2. Architecture & Infrastructure
- **Monorepo Structure**: Managed in a single repository.
- **Docker Compose**: Orchestrates the frontend and backend services via `docker-compose.yml`.
- **Local Execution**: No cloud dependency. All data (DB, Videos) resides on the user's machine.
- **Volumes**:
  - `storage/`: Shared volume for storing raw (`original-videos/`) and processed (`processed-videos/`) files.
  - `db/`: Volume for the SQLite database file (`dev.db`).

## 3. Tech Stack

### Frontend
- **Framework**: Next.js (App Router)
- **Language**: TypeScript
- **Rendering**: CSR (Client-Side Rendering) primarily. Use `"use client"` directive for interactive components.
- **Styling**: Tailwind CSS + shadcn/ui (recommended).
- **Design Pattern**: **Atomic Design** (`src/components/{atoms,molecules,organisms,templates}`).
- **API Client**: Auto-generated type-safe client using `openapi-typescript-codegen` based on Backend's OpenAPI spec.
- **ORM**: Prisma (SQLite) - *Managed by Frontend for video metadata.*

### Backend (ML Service)
- **Framework**: FastAPI (Python)
- **Libraries**: OpenCV, Ultralytics (YOLO), MediaPipe, NumPy.
- **Role**:
  - Expose API endpoints (Auto-generated Swagger/OpenAPI docs required).
  - Process videos using the logic defined in the **Appendix**.
  - Return analysis results and paths to processed videos.

## 4. Functional Requirements

### A. Video Upload
- User uploads a video file via the UI.
- Frontend saves the file to `storage/original-videos/`.
- Frontend creates a record in SQLite (via Prisma) with status `PENDING`.

### Video Analysis
1. **Asynchronous Processing**: Analysis runs in the background via `BackgroundTasks`, returning 202 Accepted immediately
2. **Real-time Status Polling**: Frontend polls `/api/videos/{id}` every 5 seconds for status updates
3. **Detection Capabilities**:
   - **Hip Lift Detection**: Monitors hip displacement from bench using dynamic thresholds
   - **Shallow Rep Detection**: State machine tracks bar-to-shoulder distance through rep phases (START → IN-PROGRESS → END)
   - **Pose Landmark Tracking**: 33-point skeletal tracking via MediaPipe
   - **Object Detection**: Bench and barbell detection using YOLO
4. **Dashboard Overlay**: Processed videos include semi-transparent black overlay (600x180px) at top displaying:
   - **OVERALL** status (GOOD REP / EGO LIFT) in GREEN or RED
   - **HIP LIFT** status (OK / FAIL: HIP LIFT)
   - **SHALLOW REP** status (OK / FAIL: ELBOW DEPTH)
5. **Result Persistence**: Backend saves analysis results to JSON file alongside video; Frontend reads this JSON to update DB.
6. **H.264 Encoding**: Videos automatically converted to H.264 via ffmpeg for browser compatibility

### Status Values
- `STATUS_OK`: "OK"
- `STATUS_FAIL_HIP`: "FAIL: HIP LIFT"
- `STATUS_FAIL_SHALLOW`: "FAIL: ELBOW DEPTH"
- `STATUS_EGO_LIFT`: Overall status when any failure detected
- `STATUS_GOOD_REP`: Overall success status

**Architecture Benefits**:
- ✅ Non-blocking: User can close browser during processing
- ✅ Scalable: Multiple videos can process simultaneously  
- ✅ Resilient: Server restart doesn't lose processing state
- ✅  UX: Immediate feedback with progress indication

### C. Video Management (CRUD)

#### Video Library (List)
- **Page**: `/videos` - Displays all uploaded videos in a grid layout.
- **Data**: Fetched from `GET /api/videos` endpoint.
- **Display**: Video cards showing filename, upload date, status badge, overall result (if completed).
- **Features**:
  - Real-time status updates (polling for PROCESSING videos)
  - Responsive grid layout
  - Empty state with upload CTA
  - Delete button per video

#### Navigation
- **Global Header**: Present on all pages with navigation links.
- **Links**:
  - "Upload" → `/` (Upload page)
  - "Library" → `/videos` (Video list)
- **Active State**: Visual indication of current page.

#### Delete Function
- **Trigger**: Delete button on video card (with confirmation).
- **API**: `DELETE /api/videos/[id]`
- **Process**:
  1. Delete from database (cascades to `analysisDataPoints`)
  2. Call backend `DELETE /videos/{id}` to remove physical files
  3. Update UI immediately
- **File Deletion**: Removes both `original-videos/` and `processed-videos/` files.

#### Detail View
- **Route**: `/videos/[id]` - Dynamic routing to individual video.
- **Display**:
  - Video player (processed video if completed)
  - Analysis results (form issues, metrics)
  - Status badges
  - Video information (frames, FPS, duration)
- **Navigation**: Back to library button.

### D. Visualization
- User views the processed video (skeleton/box overlay).
- User sees a dashboard of analysis metrics (graphs/tables) derived from the ML output.

## 5. Directory Structure Plan

```text
.
├── docker-compose.yml
├── REQUIREMENTS.md
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── atoms/
│   │   │   ├── molecules/
│   │   │   ├── organisms/
│   │   │   └── templates/
│   │   └── lib/ (API client)
│   ├── prisma/
│   │   └── schema.prisma (Datasource: "file:../../db/dev.db")
│   └── Dockerfile
├── ml-backend/
│   ├── app/
│   │   ├── main.py
│   │   └── logic.py (The refactored ML class)
│   ├── models/
│   │   └── best.pt (YOLO model)
│   ├── requirements.txt
│   └── Dockerfile
├── db/ (gitignored)
└── storage/ (gitignored)
```

## 6. Appendix: ML Logic (Source Code)
Instruction: Refactor the following script into a reusable Python class (e.g., WorkoutAnalyzer) in ml-backend/app/logic.py.

- Inputs: input_video_path, output_video_path, model_path.

- Outputs: Dictionary containing overall_status, hip_lift_status, shallow_rep_status, and time-series data for graphs.

- Note: Ensure the script runs within the Docker container context (paths might differ).

```python
import cv2
import mediapipe as mp
from ultralytics import YOLO
import numpy as np
import os
from collections import deque 

# --- (!!!) THRESHOLDS & CONFIG (Keep these) ---
# YOLO_MODEL_PATH will be passed dynamically
HIP_LIFT_RATIO = 0.5    
SHALLOW_REP_RATIO = 0.05   
SMOOTHING_WINDOW_SIZE = 5 

STATUS_OK = "OK"
STATUS_FAIL_HIP = "FAIL: HIP LIFT"
STATUS_FAIL_SHALLOW = "FAIL: ELBOW DEPTH"
STATUS_GOOD_REP = "GOOD REP"
STATUS_EGO_LIFT = "EGO LIFT"

COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)

# ... (Logic Implementation) ...
# The AI must implement the processing loop based on the logic below:
# 1. Initialize YOLO and MediaPipe.
# 2. Iterate through frames.
# 3. Detect Bench and Bar (YOLO).
# 4. Detect Pose Landmarks (MediaPipe).
# 5. Calculate Hip Lift (using baseline_hip_bench_dist).
# 6. Calculate Shallow Rep (using dynamic_shallow_threshold).
# 7. Draw overlays and text.
# 8. Return structured results.
```

## 7. Testing Strategy

### A. Backend Testing (Pytest)
- **Unit Tests**: Test the logic in `ml-backend/app/logic.py` independently. Mock the heavy ML models (YOLO/MediaPipe) to test business logic purely.
- **Integration Tests**: Use FastAPI's `TestClient` to test API endpoints (`/analyze`). Verify that:
  - Valid requests return 200 OK.
  - Invalid paths return 400/404.
  - Database records are correctly updated after processing (mocking the actual ML inference if necessary for speed).

### B. Frontend Testing (Vitest + React Testing Library)
- **Component Tests**: Verify that key components (`VideoUploader`, `AnalysisDashboard`) render correctly.
- **Mocking**: Mock the API client to ensure the frontend handles success/error responses correctly without needing a running backend.

### C. System Sanity Check (Smoke Test)
- A script (e.g., `test_integration.sh`) that:
  1. Checks if Docker containers are running.
  2. Hits the Backend health check endpoint (`GET /`).
  3. Verifies Database connection.