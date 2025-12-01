"""
WorkoutAnalyzer: ML logic for analyzing bench press videos.
This class processes video files using YOLO (for bench/bar detection) and MediaPipe (for pose landmarks).
"""
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
import os
import torch

# PyTorch 2.6 Global Fix: Monkey patch torch.load to use weights_only=False by default
# This is safe for local applications with trusted model files (best.pt from known source)
# Avoids "whack-a-mole" of adding individual classes to safe_globals
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    """Patched torch.load that defaults to weights_only=False for compatibility."""
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# NOW import ultralytics (after patching torch.load)
from ultralytics import YOLO


# --- Configuration Constants ---
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


class WorkoutAnalyzer:
    """Analyzes bench press workout videos using computer vision."""
    
    def __init__(self, model_path: str):
        """
        Initialize the analyzer with ML models.
        
        Args:
            model_path: Path to the YOLO model file (.pt)
        """
        self.model_path = model_path
        self.yolo_model = None
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # State variables for rep judgment
        self.is_in_rep = False
        self.min_bar_shoulder_dist = 1000
        self.min_elbow_y_at_bottom = 2000
       

    def _load_models(self):
        """Load YOLO and MediaPipe models."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YOLO model not found at {self.model_path}")
        self.yolo_model = YOLO(self.model_path)
        
    def analyze_video(self, input_video_path: str, output_video_path: str) -> Dict:
        """
        Analyze a bench press video and generate annotated output.
        
        Args:
            input_video_path: Path to the input video file
            output_video_path: Path where the processed video will be saved
            
        Returns:
            Dictionary containing analysis results including:
            - overall_status: str (OK, FAIL: HIP LIFT, FAIL: ELBOW DEPTH)
            - hip_lift_status: bool (True if hip lift detected)
            - shallow_rep_status: bool (True if shallow reps detected)
            - time_series_data: List of frame-by-frame metrics
        """
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found at {input_video_path}")
        
        # Load models
        self._load_models()
        
        # Open video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        # Video writer with MP4V-ES codec (reliable with OpenCV)
        # We'll convert to H.264 afterwards using ffmpeg for browser compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_output = output_video_path.replace('.mp4', '_temp.mp4')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise RuntimeError(
                "Failed to initialize video writer. "
                "Please check OpenCV installation."
            )
        
        # Analysis state
        baseline_hip_bench_dist = None
        dynamic_hip_threshold = None
        hip_lift_status = STATUS_OK
        shallow_rep_status = STATUS_OK
        time_series_data = []
        
        # Smoothing buffer
        elbow_y_buffer = deque(maxlen=SMOOTHING_WINDOW_SIZE)
        
        frame_idx = 0
        
        with self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                annotated_frame = frame.copy()
                
                # --- YOLO Detection (Bench & Bar) ---
                bench_box = None
                bar_box = None
                
                results = self.yolo_model(frame, verbose=False)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Fixed: class 0 = bar, class 1 = bench (corrected mapping)
                        if cls_id == 0 and conf > 0.5:
                            bar_box = (int(x1), int(y1), int(x2), int(y2))
                            cv2.rectangle(annotated_frame, (bar_box[0], bar_box[1]), 
                                        (bar_box[2], bar_box[3]), COLOR_WHITE, 2)
                            cv2.putText(annotated_frame, "Bar", (bar_box[0], bar_box[1] - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 2)
                        elif cls_id == 1 and conf > 0.5:
                            bench_box = (int(x1), int(y1), int(x2), int(y2))
                            cv2.rectangle(annotated_frame, (bench_box[0], bench_box[1]), 
                                        (bench_box[2], bench_box[3]), COLOR_GREEN, 2)
                            cv2.putText(annotated_frame, "Bench", (bench_box[0], bench_box[1] - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GREEN, 2)
                
                # --- MediaPipe Pose Detection ---
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_results = pose.process(rgb_frame)
                
                current_hip_y = None
                current_elbow_y = None
                current_shoulder_y = None
                
                if pose_results.pose_landmarks:
                    # Draw pose skeleton
                    self.mp_drawing.draw_landmarks(
                        annotated_frame,
                        pose_results.pose_landmarks,
                        self.mp_pose.POSE_CONNECTIONS
                    )
                    
                    landmarks = pose_results.pose_landmarks.landmark
                    
                    # Get key points
                    left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
                    left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
                    right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
                    left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                    
                    # Calculate average positions
                    current_hip_y = ((left_hip.y + right_hip.y) / 2) * height
                    current_elbow_y = ((left_elbow.y + right_elbow.y) / 2) * height
                    current_shoulder_y = ((left_shoulder.y + right_shoulder.y) / 2) * height
                    
                    # Apply smoothing to elbow
                    elbow_y_buffer.append(current_elbow_y)
                    smoothed_elbow_y = sum(elbow_y_buffer) / len(elbow_y_buffer)
                    
                    # --- Hip Lift Detection (Original Logic) ---
                    if bench_box:
                        avg_bench_top_y = bench_box[1]
                        current_hip_bench_dist = abs(current_hip_y - avg_bench_top_y)
                        
                        # Establish baseline
                        if baseline_hip_bench_dist is None:
                            baseline_hip_bench_dist = current_hip_bench_dist
                            dynamic_hip_threshold = baseline_hip_bench_dist * HIP_LIFT_RATIO
                        
                        # Check for hip lift
                        if current_hip_bench_dist > (baseline_hip_bench_dist + dynamic_hip_threshold):
                            hip_lift_status = STATUS_FAIL_HIP
                            # Draw red box on bench to indicate violation
                            cv2.rectangle(annotated_frame, (bench_box[0], bench_box[1]),
                                        (bench_box[2], bench_box[3]), COLOR_RED, 3)
                    
                    # --- Shallow Rep Detection (State Machine) ---
                    if bar_box:
                        avg_bar_bottom_y = bar_box[3]
                        avg_shoulder_line_y = current_shoulder_y
                        avg_elbow_line_y = smoothed_elbow_y
                        
                        current_bar_shoulder_dist = abs(avg_bar_bottom_y - avg_shoulder_line_y)
                        
                        # Calculate torso length for dynamic threshold
                        avg_torso_length = abs(current_shoulder_y - current_hip_y) if current_shoulder_y and current_hip_y else 100
                        dynamic_shallow_threshold = avg_torso_length * SHALLOW_REP_RATIO
                        
                        # REP START
                        if not self.is_in_rep and current_bar_shoulder_dist < (self.min_bar_shoulder_dist - 30):
                            self.is_in_rep = True
                            self.min_bar_shoulder_dist = current_bar_shoulder_dist
                            self.min_elbow_y_at_bottom = avg_elbow_line_y
                        
                        # REP IN-PROGRESS (Track minimum)
                        elif self.is_in_rep and current_bar_shoulder_dist < self.min_bar_shoulder_dist:
                            self.min_bar_shoulder_dist = current_bar_shoulder_dist
                            self.min_elbow_y_at_bottom = avg_elbow_line_y
                        
                        # REP END (Judge)
                        elif self.is_in_rep and current_bar_shoulder_dist > (self.min_bar_shoulder_dist + 30):
                            if bench_box:
                                avg_bench_top_y = bench_box[1]
                                if self.min_elbow_y_at_bottom > (avg_bench_top_y + dynamic_shallow_threshold):
                                    shallow_rep_status = STATUS_FAIL_SHALLOW
                            
                            # Reset state for next rep
                            self.is_in_rep = False
                            self.min_bar_shoulder_dist = 1000
                            self.min_elbow_y_at_bottom = 2000
                
                # --- Store time series data ---
                time_series_data.append({
                    "frame": frame_idx,
                    "timestamp": frame_idx / fps,
                    "hip_y": float(current_hip_y) if current_hip_y else None,
                    "elbow_y": float(current_elbow_y) if current_elbow_y else None,
                    "shoulder_y": float(current_shoulder_y) if current_shoulder_y else None,
                    "bench_detected": bench_box is not None,
                    "bar_detected": bar_box is not None
                })
                
                # --- Dashboard Overlay (Original Prototype Feature) ---
                # Draw semi-transparent black box at top
                overlay = annotated_frame.copy()
                cv2.rectangle(overlay, (0, 0), (600, 180), (0, 0, 0), -1)
                alpha = 0.6
                cv2.addWeighted(overlay, alpha, annotated_frame, 1 - alpha, 0, annotated_frame)
                
                # Determine overall status
                if hip_lift_status != STATUS_OK or shallow_rep_status != STATUS_OK:
                    overall_status = STATUS_EGO_LIFT
                    overall_color = COLOR_RED
                else:
                    overall_status = STATUS_GOOD_REP
                    overall_color = COLOR_GREEN
                
                # Draw status text on dashboard
                cv2.putText(annotated_frame, f"OVERALL:     {overall_status}", (20, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, overall_color, 2)
                cv2.putText(annotated_frame, f"HIP LIFT:    {hip_lift_status}", (20, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 1,
                           COLOR_GREEN if hip_lift_status == STATUS_OK else COLOR_RED, 2)
                cv2.putText(annotated_frame, f"SHALLOW REP: {shallow_rep_status}", (20, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 1,
                           COLOR_GREEN if shallow_rep_status == STATUS_OK else COLOR_RED, 2)
                
                # Write frame
                out.write(annotated_frame)
        
        # Cleanup
        cap.release()
        out.release()
        
        # Convert to H.264 for browser compatibility using ffmpeg
        print(f"Converting video to H.264 codec for web playback...")
        import subprocess
        try:
            subprocess.run([
                'ffmpeg',
                '-i', temp_output,
                '-c:v', 'libx264',  # H.264 video codec
                '-preset', 'fast',  # Encoding speed
                '-crf', '23',  # Quality (lower = better, 18-28 is good range)
                '-pix_fmt', 'yuv420p',  # Pixel format for browser compatibility
                '-movflags', '+faststart',  # Enable progressive download
                '-y',  # Overwrite output file
                output_video_path
            ], check=True, capture_output=True)
            
            # Remove temp file
            os.remove(temp_output)
            print(f"✓ Video converted to H.264 successfully")
        except subprocess.CalledProcessError as e:
            print(f"Warning: ffmpeg conversion failed: {e.stderr.decode()}")
            # Fall back to mp4v video if conversion fails
            os.rename(temp_output, output_video_path)
            print(f"⚠  Using mp4v codec (may not play in some browsers)")
        except FileNotFoundError:
            print(f"Warning: ffmpeg not found, using mp4v codec")
            os.rename(temp_output, output_video_path)
            print(f"⚠  Video may not play in browsers without H.264 support")
        
        # --- Determine Overall Status ---
        if hip_lift_status != STATUS_OK or shallow_rep_status != STATUS_OK:
            overall_status = STATUS_EGO_LIFT
        else:
            overall_status = STATUS_GOOD_REP
        
        results = {
            "overall_status": overall_status,
            "hip_lift_status": hip_lift_status,
            "shallow_rep_status": shallow_rep_status,
            "hip_lift_detected": hip_lift_status != STATUS_OK,
            "shallow_rep_detected": shallow_rep_status != STATUS_OK,
            "time_series_data": time_series_data,
            "total_frames": total_frames,
            "fps": fps,
            "video_duration": total_frames / fps if fps > 0 else 0
        }
        
        # Save results to JSON file
        import json
        json_output_path = output_video_path.replace('.mp4', '.json')
        with open(json_output_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
