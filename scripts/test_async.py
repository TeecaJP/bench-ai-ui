#!/usr/bin/env python3
"""
End-to-End Test for Async Processing with Polling
Verifies the complete async workflow from upload to completion
"""
import requests
import time
import sys

FRONTEND_URL = "http://localhost:3333"
TEST_VIDEO = "storage/dummy_workout.mp4"

def test_async_workflow():
    print("\n" + "="*70)
    print("E2E TEST - Async Processing with Polling")
    print("="*70 + "\n")
    
    # Step 1: Upload video
    print("[1/4] Uploading test video...")
    with open(TEST_VIDEO, 'rb') as f:
        files = {'file': ('test.mp4', f, 'video/mp4')}
        resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
    
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.status_code}")
        return False
    
    video_id = resp.json()['videoId']
    print(f"✓ Uploaded: {video_id}\n")
    
    # Step 2: Trigger analysis
    print("[2/4] Triggering async analysis...")
    resp = requests.post(
        f"{FRONTEND_URL}/api/analyze",
        json={"videoId": video_id},
        timeout=10
    )
    
    if resp.status_code != 202:
        print(f"❌ Expected 202, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"✓ Got 202 Accepted: {data['status']}\n")
    
    # Step 3: Poll for completion
    print("[3/4] Polling for completion...")
    max_polls = 60  # 5 minutes max
    poll_count = 0
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(5)
        
        resp = requests.get(f"{FRONTEND_URL}/api/videos/{video_id}")
        video = resp.json()
        
        status = video['status']
        print(f"  Poll {poll_count}: {status}")
        
        if status == 'COMPLETED':
            print(f"✓ Processing completed after {poll_count * 5}s\n")
            
            # Step 4: Verify results
            print("[4/4] Verifying results...")
            if video.get('processedPath'):
                print(f"✓ Processed video: {video['processedPath']}")
            else:
                print("⚠  No processed video path")
            
            print("\n" + "="*70)
            print("✅ ALL TESTS PASSED - Async workflow working!")
            print("="*70 + "\n")
            return True
        
        elif status == 'FAILED':
            print(f"❌ Processing failed")
            return False
    
    print(f"❌ Timeout after {max_polls * 5}s")
    return False

if __name__ == "__main__":
    success = test_async_workflow()
    sys.exit(0 if success else 1)
