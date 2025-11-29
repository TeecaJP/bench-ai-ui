#!/usr/bin/env python3
"""
Generate a simple dummy video file for testing.
Creates a 2-second black video with audio.
"""
import subprocess
import sys
import os

def create_dummy_video(output_path: str):
    """Create a simple 2-second black video using ffmpeg."""
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: ffmpeg not found. Installing via homebrew...")
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
    
    # Create a 2-second black video
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-f", "lavfi",
        "-i", "color=c=black:s=640x480:d=2",  # 2 second black video
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",  # Silent audio
        "-c:v", "libx264",
        "-t", "2",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        output_path
    ]
    
    print(f"Creating dummy video: {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error creating video: {result.stderr}")
        sys.exit(1)
    
    print(f"✓ Dummy video created: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    output = "storage/dummy_workout.mp4"
    os.makedirs("storage", exist_ok=True)
    create_dummy_video(output)
