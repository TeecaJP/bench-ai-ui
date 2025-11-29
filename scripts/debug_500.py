#!/usr/bin/env python3
"""
Debug 500 Error Script - Direct API Testing
Reproduces the /api/analyze 500 error for debugging
"""
import requests
import json
import sys
import sqlite3

FRONTEND_URL = "http://localhost:3333"
DB_PATH = "db/dev.db"

def get_test_video_id():
    """Get a video ID from database for testing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename FROM videos ORDER BY createdAt DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0], row[1]
    return None, None

def test_analyze_endpoint():
    """Test the /api/analyze endpoint and capture full error details."""
    print("="*70)
    print("DEBUG: Testing POST /api/analyze")
    print("="*70 + "\n")
    
    # Get test video ID
    video_id, filename = get_test_video_id()
    
    if not video_id:
        print("❌ No video found in database. Creating one...")
        # Upload a test video first
        import os
        test_video = "storage/dummy_workout.mp4"
        if not os.path.exists(test_video):
            print("Creating dummy video...")
            os.system("python3 scripts/create_dummy_video.py")
        
        with open(test_video, 'rb') as f:
            files = {'file': ('test.mp4', f, 'video/mp4')}
            resp = requests.post(f"{FRONTEND_URL}/api/upload", files=files, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                video_id = data['videoId']
                filename = data['filename']
                print(f"✓ Uploaded test video: {video_id}")
            else:
                print(f"❌ Upload failed: {resp.status_code}")
                print(resp.text)
                return
    
    print(f"Using video ID: {video_id} ({filename})")
    print()
    
    # Test analyze endpoint
    payload = {"videoId": video_id}
    
    print(f"POST {FRONTEND_URL}/api/analyze")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{FRONTEND_URL}/api/analyze",
            json=payload,
            timeout=120  # 2 minute timeout for ML processing
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        print("Response Body:")
        print("-" * 70)
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        print("-" * 70)
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS: API returned 200 OK")
            return True
        else:
            print(f"❌ FAILURE: API returned {response.status_code}")
            print()
            print("🔍 Next steps:")
            print("1. Check backend logs: docker-compose logs backend --tail 50")
            print("2. Check frontend logs: docker-compose logs frontend --tail 50")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request exceeded 120 seconds")
        print("This suggests the backend ML processing is hanging or very slow")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_analyze_endpoint()
    sys.exit(0 if success else 1)
