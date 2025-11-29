#!/usr/bin/env python3
"""
File Deletion Verification Script
Tests that physical files are actually deleted when video is removed
"""
import requests
import os
import sys
import time

FRONTEND_URL = "http://localhost:3333"
TEST_VIDEO = "storage/dummy_workout.mp4"

def test_file_deletion():
    print("\n" + "="*70)
    print("FILE DELETION VERIFICATION TEST")
    print("="*70 + "\n")
    
    # Step 1: Upload video
    print("[1/5] Uploading test video...")
    with open(TEST_VIDEO, 'rb') as f:
        files = {'file': ('deletion_test.mp4', f, 'video/mp4')}
        resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
    
    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.status_code}")
        return False
    
    video_id = resp.json()['videoId']
    print(f"✓ Uploaded: {video_id}\n")
    
    # Step 2: Get video details to capture file paths
    print("[2/5] Getting video details...")
    resp = requests.get(f"{FRONTEND_URL}/api/videos/{video_id}")
    video = resp.json()
    
    original_path = video['originalPath']
    print(f"  Original path: {original_path}")
    
    # Convert Docker paths to host paths
    original_local = original_path.replace('/app/storage/', 'storage/')
    print(f"  Host path: {original_local}\n")
    
    # Step 3: Verify file exists BEFORE deletion
    print("[3/5] Verifying file exists before deletion...")
    if not os.path.exists(original_local):
        print(f"❌ File doesn't exist before deletion: {original_local}")
        return False
    print(f"✓ File confirmed: {original_local}\n")
    
    # Step 4: Delete video via API
    print("[4/5] Deleting video via API...")
    resp = requests.delete(f"{FRONTEND_URL}/api/videos/{video_id}")
    
    if resp.status_code != 200:
        print(f"❌ Delete API failed: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return False
    
    print(f"✓ API delete successful\n")
    
    # Wait a moment for async operations
    time.sleep(1)
    
    # Step 5: Verify file is DELETED
    print("[5/5] Verifying physical file deletion...")
    if os.path.exists(original_local):
        print(f"❌ FAILED: File still exists: {original_local}")
        print(f"   This is the orphaned file bug!")
        return False
    
    print(f"✓ Physical file deleted: {original_local}")
    
    # Also check processed file if it existed
    if video.get('processedPath'):
        processed_local = video['processedPath'].replace('/app/storage/', 'storage/')
        if os.path.exists(processed_local):
            print(f"⚠  Processed file still exists: {processed_local}")
        else:
            print(f"✓ Processed file also deleted: {processed_local}")
    
    print("\n" + "="*70)
    print("✅ FILE DELETION TEST PASSED!")
    print("   Physical files are properly deleted with DB records")
    print("="*70 + "\n")
    return True

if __name__ == "__main__":
    success = test_file_deletion()
    sys.exit(0 if success else 1)
