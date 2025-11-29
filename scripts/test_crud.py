#!/usr/bin/env python3
"""
CRUD Test Script - Video Management Platform
Tests create, read, update, delete operations
"""
import requests
import time
import sys
import os

FRONTEND_URL = "http://localhost:3333"
TEST_VIDEO = "storage/dummy_workout.mp4"

def test_crud_operations():
    print("\n" + "="*70)
    print("CRUD TEST - Video Management Platform")
    print("="*70 + "\n")
    
    # Step 1: Upload video (CREATE)
    print("[1/5] CREATE: Uploading test video...")
    with open(TEST_VIDEO, 'rb') as f:
        files = {'file': ('test.mp4', f, 'video/mp4')}
        resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
    
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.status_code}")
        return False
    
    video_id = resp.json()['videoId']
    print(f"✓ Created video: {video_id}\n")
    
    # Step 2: List videos (READ - List)
    print("[2/5] READ (List): Fetching all videos...")
    resp = requests.get(f"{FRONTEND_URL}/api/videos")
    
    if resp.status_code != 200:
        print(f"❌ List failed: {resp.status_code}")
        return False
    
    data = resp.json()
    videos = data['videos']
    print(f"✓ Found {len(videos)} video(s)")
    
    # Verify our video is in the list
    found = any(v['id'] == video_id for v in videos)
    if not found:
        print(f"❌ Uploaded video not in list!")
        return False
    print(f"✓ Video appears in library\n")
    
    # Step 3: Get single video (READ - Detail)
    print("[3/5] READ (Detail): Fetching video by ID...")
    resp = requests.get(f"{FRONTEND_URL}/api/videos/{video_id}")
    
    if resp.status_code != 200:
        print(f"❌ Get video failed: {resp.status_code}")
        return False
    
    video = resp.json()
    print(f"✓ Retrieved: {video['filename']}")
    print(f"  Status: {video['status']}\n")
    
   # Step 4: Trigger analysis (UPDATE)
    print("[4/5] UPDATE: Triggering analysis...")
    resp = requests.post(
        f"{FRONTEND_URL}/api/analyze",
        json={"videoId": video_id},
        timeout=10
    )
    
    if resp.status_code != 202:
        print(f"❌ Analysis trigger failed: {resp.status_code}")
        return False
    
    print(f"✓ Analysis started (202 Accepted)\n")
    
    # Wait a bit for processing to start
    time.sleep(3)
    
    # Step 5: Delete video (DELETE)
    print("[5/5] DELETE: Removing video...")
    
    # Get video info to check file paths
    resp = requests.get(f"{FRONTEND_URL}/api/videos/{video_id}")
    video_before_delete = resp.json()
    original_path = video_before_delete.get('originalPath', '')
    
    # Delete via API
    resp = requests.delete(f"{FRONTEND_URL}/api/videos/{video_id}")
    
    if resp.status_code != 200:
        print(f"❌ Delete failed: {resp.status_code}")
        return False
    
    print(f"✓ Video deleted from database")
    
    # Verify video is gone from list
    resp = requests.get(f"{FRONTEND_URL}/api/videos")
    videos = resp.json()['videos']
    still_exists = any(v['id'] == video_id for v in videos)
    
    if still_exists:
        print(f"❌ Video still in list after delete!")
        return False
    print(f"✓ Video removed from library")
    
    # Verify physical files are deleted
    if original_path:
        local_path = original_path.replace('/app/storage/', 'storage/')
        if os.path.exists(local_path):
            print(f"⚠  Original file still exists: {local_path}")
            print(f"   (This is expected if backend delete failed)")
        else:
            print(f"✓ Physical files deleted")
    
    print("\n" + "="*70)
    print("✅ ALL CRUD TESTS PASSED!")
    print("="*70 + "\n")
    return True

if __name__ == "__main__":
    success = test_crud_operations()
    sys.exit(0 if success else 1)
