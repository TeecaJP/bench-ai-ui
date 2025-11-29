# Workout Analysis App

A local-first web application for analyzing bench press workout videos using computer vision and machine learning.

## Features

- 🎥 **Video Upload**: Upload workout videos directly through the web interface
- 🤖 **AI Analysis**: Automatic form analysis using YOLO and MediaPipe
- 📊 **Detailed Metrics**: View hip lift detection, shallow rep detection, and movement tracking
- 📈 **Visualizations**: Interactive charts showing body position over time
- 🎬 **Processed Videos**: Download annotated videos with skeletal overlay
- 💾 **Local Storage**: All data stays on your machine - no cloud required

## Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** + shadcn/ui
- **Prisma** (SQLite)
- **Recharts** (Data visualization)
- **Atomic Design** pattern

### Backend
- **FastAPI** (Python)
- **YOLO** (Object detection - bench/bar)
- **MediaPipe** (Pose estimation)
- **OpenCV** (Video processing)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- YOLO model file (`best.pt`) placed in `ml-backend/models/`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bench-ai-ui
```

2. Place your YOLO model:
```bash
# Copy your trained YOLO model to:
ml-backend/models/best.pt
```

3. Start the application:
```bash
docker-compose up --build
```

4. Access the application:
- **Frontend**: http://localhost:3333
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### First Run Setup

On the first run, initialize the database:

```bash
docker-compose exec frontend npx prisma db push
```

This creates the SQLite database tables (`videos` and `analysis_data_points`).

## Usage

1. **Upload Video**: Click "Choose Video File" and select a bench press video
2. **Wait for Analysis**: The AI will analyze your form (this may take a few minutes)
3. **View Results**: See your analysis results including:
   - Overall status (OK/FAIL)
   - Hip lift detection
   - Shallow rep detection
   - Movement charts
   - Annotated video

## Development

### Running Tests

**Backend Tests**:
```bash
cd ml-backend
pytest tests/ -v
```

**Frontend Tests**:
```bash
cd frontend
npm test
```

**Health Check**:
```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

### Project Structure

```
.
├── docker-compose.yml          # Docker orchestration
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/               # Next.js pages and API routes
│   │   ├── components/        # Atomic Design components
│   │   │   ├── atoms/
│   │   │   ├── molecules/
│   │   │   ├── organisms/
│   │   │   └── templates/
│   │   └── lib/               # Utilities and API client
│   └── prisma/                # Database schema
├── ml-backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   └── logic.py           # ML analysis logic
│   ├── models/                # YOLO models
│   └── tests/                 # Backend tests
├── storage/                    # Video storage (gitignored)
│   ├── original-videos/
│   └── processed-videos/
└── db/                        # SQLite database (gitignored)
```

## API Endpoints

### Backend (Port 8000)

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /analyze` - Analyze a video
  - Body: `{ "input_video_path": "...", "output_video_path": "..." }`
  - Returns: Analysis results with time-series data

### Frontend API Routes (Port 3000)

- `POST /api/upload` - Upload video file
- `POST /api/analyze` - Trigger analysis
- `GET /api/video?path=...` - Stream video
- `GET /api/download?path=...` - Download processed video
- `GET /api/videos/[id]` - Get video metadata and analysis data

## Architecture

The application follows a monorepo structure with Docker Compose orchestration:

1. **Frontend** (Next.js) handles:
   - User interface
   - Video upload
   - Database management (Prisma + SQLite)
   - API integration

2. **Backend** (FastAPI) handles:
   - ML inference (YOLO + MediaPipe)
   - Video processing
   - Analysis logic

3. **Shared Volumes**:
   - `storage/`: Videos (original and processed)
   - `db/`: SQLite database file

## Testing Strategy

- **Backend**: Pytest with TestClient, mocked ML models for fast testing
- **Frontend**: Vitest + React Testing Library for component tests
- **Integration**: Health check script validates service availability

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request