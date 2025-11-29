/**
 * VideoUploader Component Tests
 * Tests file selection, upload progress, and API integration
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { VideoUploader } from '../VideoUploader'

// Mock fetch globally
global.fetch = vi.fn()

describe('VideoUploader', () => {
  const mockOnUploadComplete = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as any).mockReset()
  })

  it('renders upload card with title and description', () => {
    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    expect(screen.getByText('Upload Workout Video')).toBeInTheDocument()
    expect(screen.getByText(/Supported formats/i)).toBeInTheDocument()
    expect(screen.getByText('Choose Video File')).toBeInTheDocument()
  })

  it('displays upload button', () => {
    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const button = screen.getByText('Choose Video File')
    expect(button).toBeInTheDocument()
  })

  it('has hidden file input', () => {
    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
    expect(fileInput).toHaveClass('hidden')
  })

  it('accepts video files only', () => {
    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toHaveAttribute('accept', 'video/*')
  })

  it('shows upload progress when file is selected', async () => {
    ;(global.fetch as any).mockImplementation(() =>
      new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ok: true,
            json: async () => ({
              videoId: 'test-id',
              filename: 'test.mp4',
              filePath: '/path/to/test.mp4',
            }),
          })
        }, 100)
      })
    )

    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    
    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    fireEvent.change(fileInput)
    
    // Should show upload progress
    await waitFor(() => {
      expect(screen.getByText('Uploading Video')).toBeInTheDocument()
    })
    
    expect(screen.getByText('test.mp4')).toBeInTheDocument()
  })

  it('calls onUploadComplete after successful upload', async () => {
    const mockResponse = {
      videoId: 'test-video-id',
      filename: 'workout.mp4',
      filePath: '/app/storage/original-videos/workout.mp4',
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'workout.mp4', { type: 'video/mp4' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    fireEvent.change(fileInput)
    
    // Wait for upload completion
    await waitFor(
      () => {
        expect(mockOnUploadComplete).toHaveBeenCalledWith(
          'test-video-id',
          'workout.mp4',
          '/app/storage/original-videos/workout.mp4'
        )
      },
      { timeout: 3000 }
    )
  })

  it('handles upload error gracefully', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    fireEvent.change(fileInput)
    
    // Wait for error handling
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to upload')
      )
    })
    
    // Should not call onUploadComplete
    expect(mockOnUploadComplete).not.toHaveBeenCalled()
    
    alertSpy.mockRestore()
  })

  it('resets state after successful upload', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        videoId: 'test-id',
        filename: 'test.mp4',
        filePath: '/path/to/test.mp4',
      }),
    })

    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    fireEvent.change(fileInput)
    
    // Wait for completion and reset
    await waitFor(
      () => {
        expect(screen.getByText('Choose Video File')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )
    
    // Upload progress should be gone
    expect(screen.queryByText('Uploading Video')).not.toBeInTheDocument()
  })

  it('sends FormData with file to /api/upload', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        videoId: 'test-id',
        filename: 'test.mp4',
        filePath: '/path/to/test.mp4',
      }),
    })
    
    global.fetch = fetchMock

    render(<VideoUploader onUploadComplete={mockOnUploadComplete} />)
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      configurable: true,
    })
    
    fireEvent.change(fileInput)
    
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      )
    })
  })
})
