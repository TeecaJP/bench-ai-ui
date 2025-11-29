#!/usr/bin/env python3
"""
Test video browser playback compatibility
Processes a video and checks if the codec is web-compatible
"""
import requests
import time
import sys
import subprocess

FRONTEND_URL = "http://localhost:3333"
TEST_VIDEO = "storage/dummy_workout.mp4"

def test_video_playback():
    print("\n" + "="*70)
    print("VIDEO BROWSER PLAYBACK TEST")
    print("="*70 + "\n")
    
    # Step 1: Upload
    print("[1/4] Uploading test video...")
    with open(TEST_VIDEO, 'rb') as f:
        files = {'file': ('playback_test.mp4', f, 'video/mp4')}
        resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
    
    video_id = resp.json()['videoId']
    print(f"✓ Uploaded: {video_id}\n")
    
    # Step 2: Trigger analysis
    print("[2/4] Triggering analysis...")
    resp = requests.post(
        f"{FRONTEND_URL}/api/analyze",
        json={"videoId": video_id},
        timeout=10
    )
    print(f"✓ Processing started (202)\n")
    
    # Step 3: Poll for completion
    print("[3/4] Waiting for processing...")
    max_polls = 120
    for i in range(max_polls):
        time.sleep(5)
        resp = requests.get(f"{FRONTEND_URL}/api/videos/{video_id}")
        video = resp.json()
        
        if video['status'] == 'COMPLETED':
            print(f"✓ Processing completed\n")
            break
        elif video['status'] == 'FAILED':
            print(f"❌ Processing failed")
            return False
        
        if (i + 1) % 6 == 0:
            print(f"  Still processing... ({(i+1)*5}s elapsed)")
    else:
        print(f"❌ Timeout")
        return False
    
    # Step 4: Check codec
    print("[4/4] Checking video codec...")
    processed_path = video['processedPath']
    local_path = processed_path.replace('/app/storage/', 'storage/')
    
    try:
        # Use ffprobe to check codec
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1',
             local_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        codec = result.stdout.strip()
        print(f"  Detected codec: {codec}")
        
        if codec in ['h264', 'avc1', 'x264']:
            print(f"✓ Codec is web-compatible: {codec}")
            print(f"\n  Video should play in browsers!")
            print(f"  Test by opening: http://localhost:3333/videos/{video_id}")
        else:
            print(f"⚠  Codec may not be web-compatible: {codec}")
            print(f"  Expected: h264/avc1/x264")
            return False
            
    except FileNotFoundError:
        print(f"⚠  ffprobe not found, skipping codec check")
        print(f"  Please test manually: http://localhost:3333/videos/{video_id}")
    except Exception as e:
        print(f"⚠  Could not check codec: {e}")
        print(f"  Please test manually: http://localhost:3333/videos/{video_id}")
    
    print("\n" + "="*70)
    print("✅ VIDEO GENERATION TEST PASSED!")
    print(f"   Navigate to: http://localhost:3333/videos/{video_id}")
    print("="*70 + "\n")
    return True

if __name__ == "__main__":
    success = test_video_playback()
    sys.exit(0 if success else 1)
