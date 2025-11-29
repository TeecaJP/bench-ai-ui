"""
Backend API Tests using pytest and FastAPI TestClient
Tests cover health endpoints and the /analyze endpoint with mocking.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "model_loaded" in data
    
    def test_health_endpoint(self):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "model_loaded" in data


class TestAnalyzeEndpoint:
    """Test the /analyze endpoint with various scenarios."""
    
    @patch('app.main.WorkoutAnalyzer')
    @patch('app.main.os.path.exists')
    def test_analyze_success(self, mock_exists, mock_analyzer_class):
        """Test successful video analysis."""
        # Mock file existence checks
        mock_exists.return_value = True
        
        # Mock WorkoutAnalyzer
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock analysis results
        mock_analyzer.analyze_video.return_value = {
            "overall_status": "OK",
            "hip_lift_status": False,
            "shallow_rep_status": False,
            "time_series_data": [
                {
                    "frame": 1,
                    "timestamp": 0.033,
                    "hip_y": 100.5,
                    "elbow_y": 150.2,
                    "shoulder_y": 120.8,
                    "bench_detected": True,
                    "bar_detected": True,
                }
            ],
            "total_frames": 300,
            "fps": 30,
            "video_duration": 10.0,
        }
        
        # Make request
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/test.mp4",
                "output_video_path": "/app/storage/processed-videos/test_processed.mp4",
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "OK"
        assert data["hip_lift_status"] is False
        assert data["shallow_rep_status"] is False
        assert len(data["time_series_data"]) == 1
        assert data["total_frames"] == 300
        assert data["fps"] == 30
        assert data["video_duration"] == 10.0
        assert data["processed_video_path"] == "/app/storage/processed-videos/test_processed.mp4"
    
    @patch('app.main.os.path.exists')
    def test_analyze_input_not_found(self, mock_exists):
        """Test analysis with non-existent input file."""
        # Mock input file doesn't exist
        mock_exists.return_value = False
        
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/nonexistent.mp4",
                "output_video_path": "/app/storage/processed-videos/output.mp4",
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @patch('app.main.WorkoutAnalyzer')
    @patch('app.main.os.path.exists')
    def test_analyze_with_failures(self, mock_exists, mock_analyzer_class):
        """Test analysis detecting form failures."""
        mock_exists.return_value = True
        
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock results with hip lift failure
        mock_analyzer.analyze_video.return_value = {
            "overall_status": "FAIL: HIP LIFT",
            "hip_lift_status": True,
            "shallow_rep_status": False,
            "time_series_data": [],
            "total_frames": 150,
            "fps": 30,
            "video_duration": 5.0,
        }
        
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/test.mp4",
                "output_video_path": "/app/storage/processed-videos/test_processed.mp4",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "FAIL: HIP LIFT"
        assert data["hip_lift_status"] is True
    
    def test_analyze_missing_input_path(self):
        """Test analysis with missing input_video_path."""
        response = client.post(
            "/analyze",
            json={
                "output_video_path": "/app/storage/processed-videos/output.mp4",
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_missing_output_path(self):
        """Test analysis with missing output_video_path."""
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/test.mp4",
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.WorkoutAnalyzer')
    @patch('app.main.os.path.exists')
    def test_analyze_processing_error(self, mock_exists, mock_analyzer_class):
        """Test analysis when processing fails."""
        mock_exists.return_value = True
        
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Simulate processing error
        mock_analyzer.analyze_video.side_effect = Exception("Processing failed")
        
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/test.mp4",
                "output_video_path": "/app/storage/processed-videos/test_processed.mp4",
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


class TestAnalyzeEndpointIntegration:
    """Integration-style tests (still mocked but testing more of the flow)."""
    
    @patch('app.main.WorkoutAnalyzer')
    @patch('app.main.os.path.exists')
    def test_full_analysis_flow(self, mock_exists, mock_analyzer_class):
        """Test complete analysis flow with realistic data."""
        mock_exists.return_value = True
        
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create realistic time series data
        time_series = [
            {
                "frame": i,
                "timestamp": i / 30.0,
                "hip_y": 200.0 + (i % 10) * 2,
                "elbow_y": 180.0 + (i % 15) * 3,
                "shoulder_y": 150.0 + (i % 5) * 1,
                "bench_detected": True,
                "bar_detected": i % 3 == 0,  # Bar detection intermittent
            }
            for i in range(1, 31)
        ]
        
        mock_analyzer.analyze_video.return_value = {
            "overall_status": "OK",
            "hip_lift_status": False,
            "shallow_rep_status": False,
            "time_series_data": time_series,
            "total_frames": 900,
            "fps": 30,
            "video_duration": 30.0,
        }
        
        response = client.post(
            "/analyze",
            json={
                "input_video_path": "/app/storage/original-videos/workout.mp4",
                "output_video_path": "/app/storage/processed-videos/workout_processed.mp4",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["time_series_data"]) == 30
        
        # Verify time series structure
        first_point = data["time_series_data"][0]
        assert "frame" in first_point
        assert "timestamp" in first_point
        assert "hipY" in first_point or "hip_y" in first_point
        assert "benchDetected" in first_point or "bench_detected" in first_point


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
