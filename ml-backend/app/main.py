"""
FastAPI Backend for Workout Video Analysis
Provides REST API endpoints for video analysis using ML models.
"""
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import os
from app.logic import WorkoutAnalyzer

app = FastAPI(
    title="Workout Analysis API",
    description="API for analyzing bench press workout videos using computer vision",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3333", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get model path from environment
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/best.pt")


# --- Request/Response Models ---
class AnalyzeRequest(BaseModel):
    """Request model for video analysis."""
    input_video_path: str = Field(..., description="Absolute path to the input video file")
    output_video_path: str = Field(..., description="Absolute path where processed video will be saved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_video_path": "/app/storage/original-videos/video1.mp4",
                "output_video_path": "/app/storage/processed-videos/video1_processed.mp4"
            }
        }


class TimeSeriesDataPoint(BaseModel):
    """Single frame data point."""
    frame: int
    timestamp: float
    hip_y: Optional[float]
    elbow_y: Optional[float]
    shoulder_y: Optional[float]
    bench_detected: bool
    bar_detected: bool


class AnalyzeResponse(BaseModel):
    """Response model for video analysis."""
    overall_status: str = Field(..., description="Overall analysis status (OK, FAIL: HIP LIFT, FAIL: ELBOW DEPTH)")
    hip_lift_status: bool = Field(..., description="Whether hip lift was detected")
    shallow_rep_status: bool = Field(..., description="Whether shallow reps were detected")
    time_series_data: List[TimeSeriesDataPoint] = Field(..., description="Frame-by-frame metrics")
    total_frames: int
    fps: int
    video_duration: float
    processed_video_path: str = Field(..., description="Path to the generated processed video")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_status": "OK",
                "hip_lift_status": False,
                "shallow_rep_status": False,
                "time_series_data": [],
                "total_frames": 300,
                "fps": 30,
                "video_duration": 10.0,
                "processed_video_path": "/app/storage/processed-videos/video1_processed.mp4"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    model_loaded: bool


# --- API Endpoints ---
@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Health check endpoint."""
    model_exists = os.path.exists(MODEL_PATH)
    return HealthResponse(
        status="ok",
        message="Workout Analysis API is running",
        model_loaded=model_exists
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    model_exists = os.path.exists(MODEL_PATH)
    return HealthResponse(
        status="healthy" if model_exists else "degraded",
        message=f"Model path: {MODEL_PATH}",
        model_loaded=model_exists
    )


@app.post("/analyze", status_code=status.HTTP_202_ACCEPTED, tags=["Analysis"])
async def analyze_video(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Start asynchronous analysis of a bench press video.
    
    This endpoint validates the request and starts background processing.
    The actual ML analysis happens asynchronously - use polling to check status.
    
    Args:
        request: Analysis request containing input/output video paths and video ID
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        202 Accepted with status message
        
    Raises:
        HTTPException: If video file not found or model not loaded
    """
    # Validate input file exists
    if not os.path.exists(request.input_video_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Input video file not found: {request.input_video_path}"
        )
    
    # Validate model exists
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YOLO model not found at {MODEL_PATH}. Please ensure the model is available."
        )
    
    # Add background task for processing
    background_tasks.add_task(
        process_video_background,
        input_path=request.input_video_path,
        output_path=request.output_video_path
    )
    
    return {
        "status": "processing_started",
        "message": "Video analysis started. Poll the video status to check progress."
    }


def process_video_background(input_path: str, output_path: str):
    """
    Background task for video processing.
    
    This runs asynchronously without blocking the API response.
    Updates are handled via the frontend's database polling mechanism.
    """
    try:
        # Create analyzer and process video
        analyzer = WorkoutAnalyzer(model_path=MODEL_PATH)
        results = analyzer.analyze_video(
            input_video_path=input_path,
            output_video_path=output_path
        )
        
        # Note: Database updates happen in the frontend's /api/analyze route
        # This function just performs the ML processing
        # The frontend is responsible for storing results in DB
        
    except Exception as e:
        # Log error for debugging
        print(f"Background processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Note: Status will remain PROCESSING if this fails
        # Frontend should implement timeout detection


@app.delete("/videos/{video_id}", tags=["Videos"])
async def delete_video_files(
    video_id: str,
    original_path: Optional[str] = Query(None),
    processed_path: Optional[str] = Query(None)
):
    """
    Delete physical video files from storage.
    
    This endpoint removes the original and processed video files from the filesystem.
    The database record should be deleted by the frontend before calling this endpoint.
    
    Args:
        video_id: ID of the video (not used for file path, just for logging)
        original_path: Full path to original video file
        processed_path: Full path to processed video file (optional)
        
    Returns:
        Status message with deletion results
    """
    deleted_files = []
    errors = []
    
    # Delete original video
    if original_path and os.path.exists(original_path):
        try:
            os.remove(original_path)
            deleted_files.append(original_path)
        except Exception as e:
            errors.append(f"Failed to delete {original_path}: {str(e)}")
    
    # Delete processed video
    if processed_path and os.path.exists(processed_path):
        try:
            os.remove(processed_path)
            deleted_files.append(processed_path)
        except Exception as e:
            errors.append(f"Failed to delete {processed_path}: {str(e)}")
            
        # Also delete associated JSON analysis file
        json_path = processed_path.replace('.mp4', '.json')
        if os.path.exists(json_path):
            try:
                os.remove(json_path)
                deleted_files.append(json_path)
            except Exception as e:
                errors.append(f"Failed to delete {json_path}: {str(e)}")
    
    return {
        "video_id": video_id,
        "deleted_files": deleted_files,
        "errors": errors if errors else None,
        "success": len(errors) == 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
