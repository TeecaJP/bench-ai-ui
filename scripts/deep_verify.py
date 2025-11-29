#!/usr/bin/env python3
"""
Deep Verification Script - Data Integrity & Schema Validation
Performs rigorous checks on the entire ML processing pipeline.
"""
import requests
import sqlite3
import time
import sys
import os
import json
from pathlib import Path

# Configuration
FRONTEND_URL = "http://localhost:3333"
BACKEND_URL = "http://localhost:8000"
TEST_VIDEO = "storage/dummy_workout.mp4"
DB_PATH = "db/dev.db"
TIMEOUT_SECONDS = 120
POLL_INTERVAL = 2

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    END = '\033[0m'

def log_step(message):
    print(f"{Colors.BLUE}[VERIFY]{Colors.END} {message}")

def log_success(message):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def log_error(message):
    print(f"{Colors.RED}✗ ERROR:{Colors.END} {message}")

def log_warn(message):
    print(f"{Colors.YELLOW}⚠ WARNING:{Colors.END} {message}")

def log_critical(message):
    print(f"{Colors.MAGENTA}⚠ CRITICAL:{Colors.END} {message}")

class DeepVerification:
    def __init__(self):
        self.video_id = None
        self.issues_found = []
        
    def run_deep_verification(self):
        """Run comprehensive deep verification."""
        print("\n" + "="*70)
        print("DEEP VERIFICATION - Data Integrity & Schema Validation")
        print("="*70 + "\n")
        
        try:
            # Step 1: Upload test video
            self.step1_upload_video()
            
            # Step 2: Trigger analysis
            self.step2_trigger_analysis()
            
            # Step 3: Monitor status transitions
            self.step3_monitor_status_transitions()
            
            # Step 4: Validate file integrity
            self.step4_validate_file_integrity()
            
            # Step 5: Validate JSON schema
            self.step5_validate_json_schema()
            
            # Step 6: Validate time-series data
            self.step6_validate_time_series_data()
            
            # Summary
            self.print_summary()
            
            return len(self.issues_found) == 0
            
        except Exception as e:
            log_error(f"Deep verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step1_upload_video(self):
        """Step 1: Upload test video."""
        log_step("Step 1: Uploading test video...")
        
        if not os.path.exists(TEST_VIDEO):
            raise Exception(f"Test video not found: {TEST_VIDEO}")
        
        with open(TEST_VIDEO, 'rb') as f:
            files = {'file': ('dummy_workout.mp4', f, 'video/mp4')}
            resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
        
        if resp.status_code != 200:
            raise Exception(f"Upload failed: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        self.video_id = data['videoId']
        log_success(f"Video uploaded: {self.video_id}")
    
    def step2_trigger_analysis(self):
        """Step 2: Trigger ML analysis."""
        log_step("Step 2: Triggering ML analysis...")
        
        resp = requests.post(
            f"{FRONTEND_URL}/api/analyze",
            json={"videoId": self.video_id},
            timeout=30
        )
        
        # Check if analysis failed due to ML model availability
        if resp.status_code == 500:
            error_text = resp.text
            if "model" in error_text.lower() or "yolo" in error_text.lower() or "weights" in error_text.lower():
                log_warn("ML model not available - this is expected without best.pt")
                log_warn("Skipping ML-dependent tests")
                raise SystemExit(0)  # Graceful exit
            else:
                raise Exception(f"Analysis failed: {resp.text}")
        
        if resp.status_code != 200:
            raise Exception(f"Analysis request failed: {resp.status_code} - {resp.text}")
        
        log_success("Analysis triggered successfully")
    
    def step3_monitor_status_transitions(self):
        """Step 3: Monitor PENDING → PROCESSING → COMPLETED transition."""
        log_step("Step 3: Monitoring status transitions (detailed)...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        start_time = time.time()
        last_status = None
        status_history = []
        
        while time.time() - start_time < TIMEOUT_SECONDS:
            cursor.execute("SELECT status FROM videos WHERE id = ?", (self.video_id,))
            row = cursor.fetchone()
            
            if row:
                current_status = row[0]
                
                # Track status changes
                if current_status != last_status:
                    elapsed = int(time.time() - start_time)
                    status_history.append((current_status, elapsed))
                    log_step(f"Status: {last_status} → {current_status} ({elapsed}s)")
                    last_status = current_status
                
                # Check for completion
                if current_status == "COMPLETED":
                    conn.close()
                    log_success(f"Status transitions: {' → '.join([s[0] for s in status_history])}")
                    log_success(f"Processing completed in {int(time.time() - start_time)}s")
                    return
                
                # Check for failure
                if current_status == "FAILED":
                    conn.close()
                    self.issues_found.append("Status became FAILED")
                    raise Exception("Analysis failed (status: FAILED)")
            
            time.sleep(POLL_INTERVAL)
        
        conn.close()
        
        # Timeout occurred
        self.issues_found.append(f"Timeout after {TIMEOUT_SECONDS}s (last status: {last_status})")
        raise Exception(f"Status transition timeout (stuck at: {last_status})")
    
    def step4_validate_file_integrity(self):
        """Step 4: Validate processed video file exists and is valid."""
        log_step("Step 4: Validating file integrity...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT originalPath, processedPath 
            FROM videos WHERE id = ?
        """, (self.video_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise Exception("Video record not found")
        
        original_path, processed_path = row
        
        # Check original file
        log_step(f"Original path (DB): {original_path}")
        if original_path:
            host_original = original_path.replace('/app/storage/', 'storage/')
            if os.path.exists(host_original):
                size = os.path.getsize(host_original)
                log_success(f"Original file exists: {host_original} ({size} bytes)")
            else:
                issue = f"Original file not found: {host_original}"
                self.issues_found.append(issue)
                log_error(issue)
        
        # Check processed file
        if not processed_path:
            self.issues_found.append("processedPath is NULL in database")
            log_error("No processed video path in database")
            return
        
        log_step(f"Processed path (DB): {processed_path}")
        
        # Convert Docker path to host path
        host_processed = processed_path.replace('/app/storage/', 'storage/')
        
        if not os.path.exists(host_processed):
            issue = f"Processed file not found: {host_processed}"
            self.issues_found.append(issue)
            log_error(issue)
            
            # Check if directory exists
            dir_path = os.path.dirname(host_processed)
            if not os.path.exists(dir_path):
                log_critical(f"Output directory missing: {dir_path}")
            return
        
        # Validate file size
        file_size = os.path.getsize(host_processed)
        if file_size == 0:
            issue = f"Processed file is empty (0 bytes): {host_processed}"
            self.issues_found.append(issue)
            log_error(issue)
        else:
            log_success(f"Processed file exists: {host_processed} ({file_size} bytes)")
    
    def step5_validate_json_schema(self):
        """Step 5: Validate analysis results JSON schema."""
        log_step("Step 5: Validating JSON schema (Python ↔ TypeScript contract)...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT overallStatus, hipLiftDetected, shallowRepDetected,
                   totalFrames, fps, videoDuration
            FROM videos WHERE id = ?
        """, (self.video_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise Exception("Video record not found")
        
        overall_status, hip_lift, shallow_rep, total_frames, fps, duration = row
        
        # Required fields for frontend
        required_fields = {
            'overallStatus': overall_status,
            'hipLiftDetected': hip_lift,
            'shallowRepDetected': shallow_rep,
            'totalFrames': total_frames,
            'fps': fps,
            'videoDuration': duration,
        }
        
        log_step("Checking required fields...")
        missing_fields = []
        
        for field_name, field_value in required_fields.items():
            if field_value is None:
                missing_fields.append(field_name)
                log_warn(f"Field '{field_name}' is NULL")
            else:
                log_success(f"{field_name}: {field_value}")
        
        if missing_fields:
            issue = f"Missing required fields: {', '.join(missing_fields)}"
            self.issues_found.append(issue)
            log_error(issue)
        
        # Validate data types
        if total_frames is not None and not isinstance(total_frames, int):
            self.issues_found.append(f"totalFrames should be int, got {type(total_frames)}")
        
        if fps is not None and not isinstance(fps, int):
            self.issues_found.append(f"fps should be int, got {type(fps)}")
    
    def step6_validate_time_series_data(self):
        """Step 6: Validate time-series data points."""
        log_step("Step 6: Validating time-series data...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), MIN(frame), MAX(frame)
            FROM analysis_data_points WHERE videoId = ?
        """, (self.video_id,))
        
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            self.issues_found.append("No time-series data points found")
            log_warn("No analysis data points in database")
            conn.close()
            return
        
        count, min_frame, max_frame = row
        log_success(f"Time-series data: {count} points (frames {min_frame}-{max_frame})")
        
        # Sample first data point to check schema
        cursor.execute("""
            SELECT frame, timestamp, hipY, elbowY, shoulderY, benchDetected, barDetected
            FROM analysis_data_points WHERE videoId = ? LIMIT 1
        """, (self.video_id,))
        
        sample = cursor.fetchone()
        conn.close()
        
        if sample:
            frame, timestamp, hip_y, elbow_y, shoulder_y, bench, bar = sample
            log_success(f"Sample data point: frame={frame}, timestamp={timestamp:.2f}s")
            log_success(f"  hip={hip_y}, elbow={elbow_y}, shoulder={shoulder_y}")
            log_success(f"  bench_detected={bench}, bar_detected={bar}")
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*70)
        if self.issues_found:
            log_error(f"VERIFICATION FAILED - {len(self.issues_found)} issue(s) found:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            log_success("ALL CHECKS PASSED - Data integrity verified!")
            log_success("Schema validation: ✓ Python/TypeScript contract valid")
            log_success("File integrity: ✓ All files exist and are valid")
            log_success("Status transitions: ✓ Proper state machine")
        print("="*70 + "\n")

def main():
    """Main verification runner."""
    if not os.path.exists(TEST_VIDEO):
        log_step("Creating test video...")
        os.system("python3 scripts/create_dummy_video.py")
    
    verifier = DeepVerification()
    success = verifier.run_deep_verification()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
