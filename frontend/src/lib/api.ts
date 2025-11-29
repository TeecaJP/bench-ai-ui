/**
 * API Client for communicating with the ML Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface TimeSeriesDataPoint {
  frame: number;
  timestamp: number;
  hipY: number | null;
  elbowY: number | null;
  shoulderY: number | null;
  benchDetected: boolean;
  barDetected: boolean;
}

export interface AnalyzeResponse {
  overall_status: string;
  hip_lift_status: boolean;
  shallow_rep_status: boolean;
  time_series_data: TimeSeriesDataPoint[];
  total_frames: number;
  fps: number;
  video_duration: number;
  processed_video_path: string;
}

export interface AnalyzeRequest {
  input_video_path: string;
  output_video_path: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Check backend health
   */
  async healthCheck(): Promise<{ status: string; message: string; model_loaded: boolean }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Analyze a video using the ML backend
   */
  async analyzeVideo(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Analysis failed');
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
