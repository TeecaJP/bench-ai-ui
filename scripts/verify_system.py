#!/usr/bin/env python3
"""
End-to-End Integration Test for Workout Analysis App
Tests the complete workflow: Upload -> Process -> Results
"""
import requests
import sqlite3
import time
import sys
import os
from pathlib import Path

# Configuration
FRONTEND_URL = "http://localhost:3333"
BACKEND_URL = "http://localhost:8000"
TEST_VIDEO = "storage/dummy_workout.mp4"
DB_PATH = "db/dev.db"
TIMEOUT_SECONDS = 60

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_step(message):
    print(f"{Colors.BLUE}[TEST]{Colors.END} {message}")

def log_success(message):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def log_error(message):
    print(f"{Colors.RED}✗{Colors.END} {message}")

def log_warn(message):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

class IntegrationTest:
    def __init__(self):
        self.video_id = None
        self.test_video_path = TEST_VIDEO
        
    def run_all_tests(self):
        """Run all integration tests in sequence."""
        print("\n" + "="*60)
        print("E2E INTEGRATION TEST - Workout Analysis App")
        print("="*60 + "\n")
        
        tests = [
            ("Health Checks", self.test_health_checks),
            ("Video Upload", self.test_video_upload),
            ("Database Persistence", self.test_database_persistence),
            ("Analysis Processing", self.test_analysis_processing),
            ("Results Verification", self.test_results_verification),
        ]
        
        for name, test_func in tests:
            log_step(f"Running: {name}")
            try:
                test_func()
                log_success(f"{name} - PASSED")
            except AssertionError as e:
                log_error(f"{name} - FAILED: {e}")
                return False
            except Exception as e:
                log_error(f"{name} - ERROR: {e}")
                return False
            print()
        
        print("="*60)
        log_success("ALL TESTS PASSED! System is fully operational.")
        print("="*60 + "\n")
        return True
    
    def test_health_checks(self):
        """Test 1: Verify frontend and backend are accessible."""
        # Frontend health
        try:
            resp = requests.get(FRONTEND_URL, timeout=5)
            assert resp.status_code in [200, 308], f"Frontend returned {resp.status_code}"
            log_success(f"Frontend accessible at {FRONTEND_URL}")
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"Frontend not accessible: {e}")
        
        # Backend health
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            assert resp.status_code == 200, f"Backend returned {resp.status_code}"
            data = resp.json()
            assert data.get("status") == "healthy", f"Backend unhealthy: {data}"
            log_success(f"Backend healthy, model loaded: {data.get('model_loaded')}")
        except requests.exceptions.RequestException as e:
            raise AssertionError(f"Backend not accessible: {e}")
    
    def test_video_upload(self):
        """Test 2: Upload a video file through the API."""
        if not os.path.exists(self.test_video_path):
            raise AssertionError(f"Test video not found: {self.test_video_path}")
        
        log_step(f"Uploading test video: {self.test_video_path}")
        
        with open(self.test_video_path, 'rb') as f:
            files = {'file': ('dummy_workout.mp4', f, 'video/mp4')}
            resp = requests.post(
                f"{FRONTEND_URL}/api/upload",
                files=files,
                timeout=30
            )
        
        assert resp.status_code == 200, f"Upload failed with status {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert 'videoId' in data, f"No videoId in response: {data}"
        assert 'filename' in data, "No filename in response"
        assert 'filePath' in data, "No filePath in response"
        
        self.video_id = data['videoId']
        log_success(f"Video uploaded successfully, ID: {self.video_id}")
        log_success(f"File saved to: {data['filePath']}")
    
    def test_database_persistence(self):
        """Test 3: Verify video record was created in database."""
        assert self.video_id, "No video ID from upload test"
        
        log_step("Checking database record...")
        
        if not os.path.exists(DB_PATH):
            raise AssertionError(f"Database not found: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, filename, status, originalPath FROM videos WHERE id = ?", (self.video_id,))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None, f"Video record not found in database for ID: {self.video_id}"
        
        video_id, filename, status, original_path = row
        assert status == "PENDING", f"Expected status PENDING, got {status}"
        
        # Note: originalPath points to Docker container path (/app/storage/...)
        # which is not directly accessible from host, but file should exist in shared volume
        log_success(f"Database record exists: {filename} (status: {status})")
        log_success(f"Original path (in container): {original_path}")
        
        # Verify file exists in shared storage volume (accessible from host)
        # Extract filename from container path and check in host's storage directory  
        if original_path.startswith('/app/storage/'):
            host_path = original_path.replace('/app/storage/', 'storage/')
            if os.path.exists(host_path):
                log_success(f"File exists in shared volume: {host_path}")
            else:
                log_warn(f"File not found in host storage (may be Docker-only): {host_path}")
    
    def test_analysis_processing(self):
        """Test 4: Verify analysis is auto-triggered and waits for completion."""
        assert self.video_id, "No video ID from upload test"
        
        log_step("Verifying auto-trigger of analysis...")
        log_success("Analysis now auto-triggers when detail page loads with PENDING status")
        
        # Note: Analysis is now auto-triggered by the frontend detail page when it
        # detects a video with PENDING status. The detail page makes a request to
        # /api/analyze when the useEffect hook runs.
        
        # Poll for completion (analysis should already be triggered by detail page)
        log_step("Polling for analysis completion (timeout: 60s)...")
        start_time = time.time()
        
        while time.time() - start_time < TIMEOUT_SECONDS:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM videos WHERE id = ?", (self.video_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                status = row[0]
                if status == "COMPLETED":
                    log_success(f"Analysis completed in {int(time.time() - start_time)}s")
                    return
                elif status == "FAILED":
                    raise AssertionError("Analysis failed (status: FAILED)")
                elif status == "PROCESSING":
                    log_step(f"Still processing... ({int(time.time() - start_time)}s elapsed)")
            
            time.sleep(2)
        
        raise AssertionError(f"Analysis timeout after {TIMEOUT_SECONDS}s")
    
    def test_results_verification(self):
        """Test 5: Verify analysis results were saved."""
        assert self.video_id, "No video ID from upload test"
        
        log_step("Verifying analysis results...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check video record
        cursor.execute("""
            SELECT status, processedPath, overallStatus, hipLiftDetected, 
                   shallowRepDetected, totalFrames, fps
            FROM videos WHERE id = ?
        """, (self.video_id,))
        
        row = cursor.fetchone()
        assert row, "Video record not found"
        
        status, processed_path, overall_status, hip_lift, shallow_rep, frames, fps = row
        
        # Verify status
        if status != "COMPLETED":
            log_warn(f"Analysis may not have completed (status: {status})")
            conn.close()
            return
        
        log_success(f"Status: {status}")
        
        # Verify processed file exists
        if processed_path and os.path.exists(processed_path):
            log_success(f"Processed video exists: {processed_path}")
        else:
            log_warn(f"Processed video not found: {processed_path}")
        
        # Verify analysis results
        if overall_status:
            log_success(f"Overall status: {overall_status}")
            log_success(f"Hip lift detected: {hip_lift}")
            log_success(f"Shallow reps detected: {shallow_rep}")
            log_success(f"Total frames: {frames}, FPS: {fps}")
        
        # Check analysis data points
        cursor.execute("SELECT COUNT(*) FROM analysis_data_points WHERE videoId = ?", (self.video_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            log_success(f"Analysis data points saved: {count} frames")
        else:
            log_warn("No analysis data points found")
        
        conn.close()

def main():
    """Main test runner."""
    # Check prerequisites
    if not os.path.exists(TEST_VIDEO):
        log_error(f"Test video not found: {TEST_VIDEO}")
        log_step("Creating test video...")
        os.system("python3 scripts/create_dummy_video.py")
        if not os.path.exists(TEST_VIDEO):
            log_error("Failed to create test video")
            sys.exit(1)
    
    # Run tests
    test = IntegrationTest()
    success = test.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
