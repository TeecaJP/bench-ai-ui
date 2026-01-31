"""
WorkoutAnalyzer: ML logic for analyzing bench press videos.
This class processes video files using YOLO (for bar detection) and MediaPipe (for pose landmarks).
"""
import cv2
import mediapipe as mp
import numpy as np
import math
import time
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
import os
import torch
from app.llm import GeminiClient

# PyTorch 2.6 Global Fix: Monkey patch torch.load to use weights_only=False by default
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

from ultralytics import YOLO


# --- Configuration Constants ---
STATUS_OK = "OK"  # Restored constant
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_ORANGE = (0, 165, 255)


class OneEuroFilter:
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = 0.0
        self.t_prev = float(t0)

    def smoothing_factor(self, t_e, cutoff):
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def exponential_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev

    def __call__(self, t, x):
        t_e = t - self.t_prev
        if t_e <= 0.0: return self.x_prev
        a_d = self.smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self.smoothing_factor(t_e, cutoff)
        x_hat = self.exponential_smoothing(a, x, self.x_prev)
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat


class RepStateMachine:
    STATE_IDLE = "IDLE"
    STATE_SETUP = "SETUP"
    STATE_DESCENDING = "DESCEND"
    STATE_BOTTOM = "BOTTOM"
    STATE_ASCENDING = "ASCEND"
    STATE_COMPLETE = "COMPLETE"

    def __init__(self):
        self.current_state = self.STATE_IDLE
        self.prev_bar_y = None
        self.setup_bar_y = None
        
        self.state_start_time = 0
        self.prev_bar_velocity = 0
        
        # Rep Tracking
        self.current_rep_data = self._init_rep_data()
        self.completed_reps = []
        
        # Dynamic Baseline for Hip (Lowest point seen)
        self.max_hip_y_baseline = 0

    def _init_rep_data(self):
        return {
            "start_time": None,
            "end_time": None,
            "max_hip_deviation_px": 0.0,
            "max_hip_deviation_ratio": 0.0, # (Deviation / Torso)
            "min_elbow_depth_ratio": 1.0, # (ElbowY - ShoulderY) / Torso. Lower is deeper. 
            # We want minimum algebraic value (Highest Y value is Deeper). 
            # Actually, depth ratio: (ElbowY - ShoulderY) / Torso. Positive = Deeper.
            # We want to track the MAX depth reached.
            "max_elbow_depth_ratio": -1.0,
            "max_upward_acceleration_ratio": 0.0,
            "rep_duration": 0.0
        }

    def update(self, current_time, bar_y, elbow_y, shoulder_y, hip_y, torso_len, 
               hip_lift_metric, elbow_depth_metric):
        """
        hip_lift_metric: >0 means lifting (ratio)
        elbow_depth_metric: >0 means deep (ratio)
        """
        if self.state_start_time == 0:
            self.state_start_time = current_time

        # --- Bar velocity & Acceleration ---
        bar_velocity = 0
        acceleration_up = 0
        if bar_y is not None and self.prev_bar_y is not None:
            bar_velocity = bar_y - self.prev_bar_y 
            # Acceleration Up: (prev_v - curr_v) 
            # Positive value when slowing down descent or speeding up ascent
            acceleration_up = self.prev_bar_velocity - bar_velocity

        self.prev_bar_velocity = bar_velocity

        # Update Hip Baseline
        if hip_y is not None:
            if hip_y > self.max_hip_y_baseline:
                self.max_hip_y_baseline = hip_y

        # Update current rep metrics if in active state
        if self.current_state in [self.STATE_DESCENDING, self.STATE_BOTTOM, self.STATE_ASCENDING]:
            if self.current_rep_data["start_time"] is None:
                self.current_rep_data["start_time"] = current_time
            
            # Track Max Hip Lift (Ratio)
            if hip_lift_metric > self.current_rep_data["max_hip_deviation_ratio"]:
                self.current_rep_data["max_hip_deviation_ratio"] = hip_lift_metric
                
            # Track Max Depth (Ratio) - Higher is deeper
            if elbow_depth_metric > self.current_rep_data["max_elbow_depth_ratio"]:
                 self.current_rep_data["max_elbow_depth_ratio"] = elbow_depth_metric

            # Track Max Acceleration (Normalized by Torso)
            if torso_len > 0:
                acc_ratio = acceleration_up / torso_len
                if acc_ratio > self.current_rep_data["max_upward_acceleration_ratio"]:
                    self.current_rep_data["max_upward_acceleration_ratio"] = acc_ratio
        
        # --- Transitions ---
        if self.current_state == self.STATE_IDLE:
            if bar_y is not None:
                self.current_state = self.STATE_SETUP
                self.setup_bar_y = bar_y
                self.state_start_time = current_time

        elif self.current_state == self.STATE_SETUP:
            if self.setup_bar_y is None: self.setup_bar_y = bar_y
            if bar_y < self.setup_bar_y: self.setup_bar_y = bar_y

            # Descent triggers
            if bar_y > (self.setup_bar_y + 30): 
                self.current_state = self.STATE_DESCENDING
                self.state_start_time = current_time
                self.current_rep_data = self._init_rep_data() # New Rep Start
                self.current_rep_data["start_time"] = current_time

        elif self.current_state == self.STATE_DESCENDING:
            if bar_velocity < -1.0: 
                self.current_state = self.STATE_BOTTOM
                # Note: Still keeping rep data active
                self.state_start_time = current_time
        
        elif self.current_state == self.STATE_BOTTOM:
             self.current_state = self.STATE_ASCENDING
             self.state_start_time = current_time

        elif self.current_state == self.STATE_ASCENDING:
            # Complete when back near top and stopped
            if bar_y <= (self.setup_bar_y + 30) and abs(bar_velocity) < 2.0:
                self.current_state = self.STATE_COMPLETE
                self.state_start_time = current_time
                
                # Finalize Rep
                self.current_rep_data["end_time"] = current_time
                self.current_rep_data["rep_duration"] = current_time - (self.current_rep_data["start_time"] or current_time)
                # Store it
                self.completed_reps.append(self.current_rep_data)

        elif self.current_state == self.STATE_COMPLETE:
            if current_time - self.state_start_time > 1.0: 
                self.current_state = self.STATE_SETUP
                self.state_start_time = current_time
                self.max_hip_y_baseline = 0 

        self.prev_bar_y = bar_y


class WorkoutAnalyzer:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.yolo_model = None
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.llm = GeminiClient()

    def _load_models(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YOLO model not found at {self.model_path}")
        self.yolo_model = YOLO(self.model_path)
        
    def analyze_video(self, input_video_path: str, output_video_path: str) -> Dict:
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found at {input_video_path}")
        
        self._load_models()
        
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {input_video_path}")
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_output = output_video_path.replace('.mp4', '_temp.mp4')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        
        sm = RepStateMachine()
        filters = {} 
        time_series_data = []
        
        frame_idx = 0
        
        with self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                frame_idx += 1
                current_time = frame_idx / fps
                annotated_frame = frame.copy()
                
                # --- YOLO (Bar) ---
                bar_box = None
                results = self.yolo_model(frame, verbose=False)
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        if cls_id == 0 and float(box.conf[0]) > 0.4:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            bar_box = (int(x1), int(y1), int(x2), int(y2))
                            cv2.rectangle(annotated_frame, (bar_box[0], bar_box[1]), (bar_box[2], bar_box[3]), COLOR_YELLOW, 2)
                            break 
                
                current_bar_y_raw = float(bar_box[3]) if bar_box else None
                current_bar_x_raw = float((bar_box[0] + bar_box[2]) / 2) if bar_box else None
                
                current_bar_y = None
                current_bar_x = None

                if bar_box:
                    if 'bar_x' not in filters:
                        filters['bar_x'] = OneEuroFilter(current_time, current_bar_x_raw)
                        filters['bar_y'] = OneEuroFilter(current_time, current_bar_y_raw)
                    current_bar_x = filters['bar_x'](current_time, current_bar_x_raw)
                    current_bar_y = filters['bar_y'](current_time, current_bar_y_raw)
                
                # --- MediaPipe Pose ---
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_results = pose.process(rgb_frame)
                
                current_shoulder_y = None
                current_elbow_y = None
                current_hip_y = None
                current_knee_y = None
                
                # Coords for Linearity Check
                s_coords = None
                h_coords = None
                k_coords = None
                
                torso_length = 0
                
                # Metric Placeholders (Raw Ratio)
                raw_hip_lift_ratio = 0.0
                raw_elbow_depth_ratio = 0.0
                
                if pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    
                    def get_weighted_coord(idx_left, idx_right):
                        lm_l = landmarks[idx_left]
                        lm_r = landmarks[idx_right]
                        vis_l = lm_l.visibility
                        vis_r = lm_r.visibility
                        if vis_l + vis_r < 0.1:
                            return (lm_l.x * width + lm_r.x * width) / 2, (lm_l.y * height + lm_r.y * height) / 2
                        x = (lm_l.x * vis_l + lm_r.x * vis_r) / (vis_l + vis_r) * width
                        y = (lm_l.y * vis_l + lm_r.y * vis_r) / (vis_l + vis_r) * height
                        return x, y, (vis_l + vis_r)/2

                    # Get coords with avg coordinates
                    sh_x, sh_y, sh_vis = get_weighted_coord(11, 12)
                    el_x, el_y, _ = get_weighted_coord(13, 14)
                    hip_x, hip_y, hip_vis = get_weighted_coord(23, 24)
                    knee_x, knee_y, knee_vis = get_weighted_coord(25, 26)
                    
                    # Filtering
                    if 'shoulder_x' not in filters: 
                        filters['shoulder_x'] = OneEuroFilter(current_time, sh_x)
                        filters['shoulder_y'] = OneEuroFilter(current_time, sh_y)
                        filters['hip_x'] = OneEuroFilter(current_time, hip_x)
                        filters['hip_y'] = OneEuroFilter(current_time, hip_y)
                        filters['knee_x'] = OneEuroFilter(current_time, knee_x)
                        filters['knee_y'] = OneEuroFilter(current_time, knee_y)
                        
                    curr_sh_x = filters['shoulder_x'](current_time, sh_x)
                    current_shoulder_y = filters['shoulder_y'](current_time, sh_y)
                    curr_hip_x = filters['hip_x'](current_time, hip_x)
                    current_hip_y = filters['hip_y'](current_time, hip_y)
                    curr_knee_x = filters['knee_x'](current_time, knee_x)
                    current_knee_y = filters['knee_y'](current_time, knee_y)
                    
                    current_elbow_y = el_y 
                    
                    s_coords = (curr_sh_x, current_shoulder_y)
                    h_coords = (curr_hip_x, current_hip_y)
                    k_coords = (curr_knee_x, current_knee_y)
                    
                    dx = curr_sh_x - curr_hip_x
                    dy = current_shoulder_y - current_hip_y
                    torso_length = math.sqrt(dx*dx + dy*dy)
                    
                    # Draw
                    cv2.circle(annotated_frame, (int(curr_sh_x), int(current_shoulder_y)), 5, COLOR_GREEN, -1)
                    cv2.circle(annotated_frame, (int(curr_hip_x), int(current_hip_y)), 5, COLOR_GREEN, -1)
                    if knee_vis > 0.3:
                         cv2.circle(annotated_frame, (int(curr_knee_x), int(current_knee_y)), 5, COLOR_GREEN, -1)

                    # --- CALCULATE RAW METRICS (No Thresholds) ---
                    # 1. Hip Lift Ratio
                    if torso_length > 0:
                        # Logic A: Dynamic Baseline (Distance from lowest point)
                        lift_a = 0.0
                        if hasattr(sm, 'max_hip_y_baseline') and sm.max_hip_y_baseline > 0:
                            dist = sm.max_hip_y_baseline - current_hip_y 
                            if dist > 0: lift_a = dist / torso_length

                        # Logic B: Linearity (Distance from S-K line)
                        lift_b = 0.0
                        if knee_vis > 0.3 and current_bar_y is not None:
                             vx_sk = k_coords[0] - s_coords[0]
                             vy_sk = k_coords[1] - s_coords[1]
                             vx_sh = h_coords[0] - s_coords[0]
                             vy_sh = h_coords[1] - s_coords[1]
                             vx_sb = current_bar_x - s_coords[0]
                             vy_sb = current_bar_y - s_coords[1]
                             cp_hip = vx_sk * vy_sh - vy_sk * vx_sh
                             cp_bar = vx_sk * vy_sb - vy_sk * vx_sb
                             
                             if cp_hip * cp_bar > 0: # Same side
                                 len_sk = math.sqrt(vx_sk*vx_sk + vy_sk*vy_sk)
                                 if len_sk > 0:
                                     lift_b = abs(cp_hip) / len_sk / torso_length
                        
                        # Take the MAX of detected lifts
                        raw_hip_lift_ratio = max(lift_a, lift_b)
                        
                        # 2. Elbow Depth Ratio
                        # (Elbow Y - Shoulder Y) / Torso
                        # Positive = Below shoulder (Deep)
                        # Negative = Above shoulder (Shallow)
                        raw_elbow_depth_ratio = (current_elbow_y - current_shoulder_y) / torso_length

                # --- State Machine Update ---
                # Pass raw metrics to SM to aggregate per Rep
                sm.update(current_time, current_bar_y, current_elbow_y, current_shoulder_y, current_hip_y, torso_length,
                          raw_hip_lift_ratio, raw_elbow_depth_ratio)
                
                # --- Visualizations (Clean, No FAIL text) ---
                cv2.rectangle(annotated_frame, (10, 10), (250, 60), (0, 0, 0), -1)
                cv2.putText(annotated_frame, f"STATE: {sm.current_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_WHITE, 2)
                
                if torso_length > 0:
                     cv2.putText(annotated_frame, f"Torso: {torso_length:.1f} px", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1)

                out.write(annotated_frame)
                
                time_series_data.append({
                    "frame": frame_idx,
                    "timestamp": current_time,
                    "bar_y": current_bar_y,
                    "bar_detected": current_bar_y is not None,
                    "bench_detected": False,
                    "elbow_y": float(current_elbow_y) if current_elbow_y else None,
                    "shoulder_y": float(current_shoulder_y) if current_shoulder_y else None,
                    "hip_y": float(current_hip_y) if current_hip_y else None, 
                    "state": sm.current_state,
                    # Save raw metrics for graphing if needed
                    "hip_lift_metric": raw_hip_lift_ratio,
                    "elbow_depth_metric": raw_elbow_depth_ratio
                })

        cap.release()
        out.release()
        import subprocess
        try:
            subprocess.run(['ffmpeg', '-i', temp_output, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-y', output_video_path], check=True, capture_output=True)
            os.remove(temp_output)
        except Exception:
            if os.path.exists(temp_output): os.rename(temp_output, output_video_path)

        # Result - Return Rep List instead of binary status
        # Note: 'overall_status' is now ambiguous, defaulting to OK or client-side decision.
        # We will keep the legacy fields for backward compat but purely informational.
        
        results = {
            "overall_status": STATUS_OK, # Client will determine this
            "time_series_data": time_series_data,
            "reps": sm.completed_reps, # NEW: List of Reps with metrics
            "fps": fps,
            "total_frames": total_frames,
            "video_duration": total_frames / fps if fps > 0 else 0,
            "llm_feedback": self.llm.generate_feedback(sm.completed_reps)
        }
        
        import json
        json_output_path = output_video_path.replace('.mp4', '.json')
        with open(json_output_path, 'w') as f:
            json.dump(results, f, indent=2)

        return results
