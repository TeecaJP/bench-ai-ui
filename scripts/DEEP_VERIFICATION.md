# Deep Verification Script

## Purpose
Comprehensive data integrity and schema validation for the ML processing pipeline.

## What It Checks

### 1. Status Transitions
- Monitors DB status: `PENDING` → `PROCESSING` → `COMPLETED`
- Detects stuck or failed states
- Records timing for each transition

### 2. File Integrity
- Validates original video file exists
- Validates processed video file exists
- Checks file sizes (non-zero)
- Handles Docker path → Host path conversion

### 3. JSON Schema Validation
- Verifies all required fields are present:
  - `overallStatus`
  - `hipLiftDetected`
  - `shallowRepDetected`
  - `totalFrames`
  - `fps`
  - `videoDuration`
- Validates data types match expectations

### 4. Time-Series Data
- Counts analysis data points
- Validates frame range
- Checks data point schema

## Running the Script

```bash
python3 scripts/deep_verify.py
```

## Current Status

✅ **Upload Flow**: Validated
✅ **Database Persistence**: Validated  
✅ **Path Handling**: Validated (Docker ↔ Host)
✅ **Schema Structure**: Validated

⚠️ **ML Processing**: Requires `ml-backend/models/best.pt` YOLO model to test end-to-end

## Notes

The script gracefully handles missing ML model and validates all non-ML-dependent portions of the system.
