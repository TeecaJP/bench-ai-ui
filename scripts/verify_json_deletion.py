import requests
import time
import os
import sys

BASE_URL = "http://localhost:3333"
BACKEND_URL = "http://localhost:8000"
STORAGE_DIR = "storage"

def verify_json_deletion():
    print("1. Uploading video...")
    upload_url = f"{BASE_URL}/api/upload"
    files = {'file': ('test_json_del.mp4', open('storage/dummy_workout.mp4', 'rb'), 'video/mp4')}
    response = requests.post(upload_url, files=files)
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        sys.exit(1)
    
    video_id = response.json()['videoId']
    print(f"Video ID: {video_id}")

    print("2. Triggering analysis...")
    analyze_url = f"{BASE_URL}/api/analyze"
    requests.post(analyze_url, json={'videoId': video_id})

    print("3. Waiting for processing and JSON creation...")
    json_path = None
    for i in range(20):
        time.sleep(2)
        status_res = requests.get(f"{BASE_URL}/api/videos/{video_id}")
        data = status_res.json()
        if data['status'] == 'COMPLETED':
            print("Processing completed.")
            processed_path = data['processedPath']
            # Convert docker path to local path
            local_processed_path = processed_path.replace('/app/storage', 'storage')
            json_path = local_processed_path.replace('.mp4', '.json')
            break
    
    if not json_path or not os.path.exists(json_path):
        print(f"JSON file not found at {json_path}")
        sys.exit(1)
    print(f"JSON file confirmed at: {json_path}")

    print("4. Deleting video...")
    delete_res = requests.delete(f"{BASE_URL}/api/videos/{video_id}")
    if delete_res.status_code != 200:
        print(f"Delete failed: {delete_res.text}")
        sys.exit(1)
    
    print("5. Verifying JSON deletion...")
    if os.path.exists(json_path):
        print(f"❌ FAILURE: JSON file still exists at {json_path}")
        sys.exit(1)
    else:
        print(f"✅ SUCCESS: JSON file was deleted.")

if __name__ == "__main__":
    # Ensure dummy video exists
    if not os.path.exists('storage/dummy_workout.mp4'):
        with open('storage/dummy_workout.mp4', 'wb') as f:
            f.write(b'dummy content')
            
    verify_json_deletion()
