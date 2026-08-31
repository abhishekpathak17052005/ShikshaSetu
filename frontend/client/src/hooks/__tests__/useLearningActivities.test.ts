/**
 * useLearningActivities Hook Tests
 * Tests for learning activity state management and API interactions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLearningActivities } from '../useLearningActivities';
import { api } from '../../lib/api';

// Mock the API module
vi.mock('../../lib/api', () => ({
  api: {
    learningActivities: {
      start: vi.fn(),
      list: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      complete: vi.fn(),
    },
  },
}));

describe('useLearningActivities Hook', () => {
  const mockActivity = {
    activity_id: 'act-001',
    user_id: 'user-001',
    resource_id: 'resource-python',
    competency_id: 'PA01',
    status: 'in_progress' as const,
    started_at: '2026-08-27T10:00:00Z',
    completed_at: null,
    last_accessed_at: '2026-08-27T14:30:00Z',
    progress_percent: 45,
    duration_minutes: 120,
  };

  const mockCompletedActivity = {
    ...mockActivity,
    activity_id: 'act-002',
    status: 'completed' as const,
    progress_percent: 100,
    completed_at: '2026-08-27T15:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with empty activities', () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [],
        total_count: 0,
      });

      const { result } = renderHook(() => useLearningActivities(false));

      expect(result.current.activities).toEqual([]);
      expect(result.current.currentActivity).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should auto-load activities on mount when enabled', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [mockActivity],
        total_count: 1,
      });

      const { result } = renderHook(() => useLearningActivities(true));

      await waitFor(() => {
        expect(result.current.activities).toHaveLength(1);
      });
    });

    it('should not auto-load activities when disabled', () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [mockActivity],
        total_count: 1,
      });

      const { result } = renderHook(() => useLearningActivities(false));

      expect(result.current.activities).toEqual([]);
    });
  });

  describe('startActivity', () => {
    it('should start a new learning activity', async () => {
      mockAPI.learningActivitiesAPI.startActivity.mockResolvedValue(mockActivity);

      const { result } = renderHook(() => useLearningActivities(false));

      let newActivity;
      await act(async () => {
        newActivity = await result.current.startActivity('resource-python', 'PA01');
      });

      expect(newActivity).toEqual(mockActivity);
      expect(result.current.currentActivity).toEqual(mockActivity);
      expect(result.current.activities).toContain(mockActivity);
    });

    it('should handle start activity errors', async () => {
      mockAPI.learningActivitiesAPI.startActivity.mockRejectedValue(
        new Error('Start failed')
      );

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.startActivity('resource-python', 'PA01');
      });

      expect(result.current.error).toBeDefined();
      expect(result.current.currentActivity).toBeNull();
    });
  });

  describe('listActivities', () => {
    it('should load all activities', async () => {
      const mockResponse = {
        activities: [mockActivity, mockCompletedActivity],
        total_count: 2,
      };
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.listActivities();
      });

      expect(result.current.activities).toHaveLength(2);
      expect(result.current.loading).toBe(false);
    });

    it('should filter activities by status', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [mockActivity],
        total_count: 1,
      });

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.listActivities('in_progress');
      });

      expect(mockAPI.learningActivitiesAPI.getActivities).toHaveBeenCalledWith(
        'in_progress'
      );
    });

    it('should set loading state', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  activities: [mockActivity],
                  total_count: 1,
                }),
              100
            )
          )
      );

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        const promise = result.current.listActivities();
        expect(result.current.loading).toBe(true);
        await promise;
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe('getActivity', () => {
    it('should get specific activity', async () => {
      mockAPI.learningActivitiesAPI.getActivity.mockResolvedValue(mockActivity);

      const { result } = renderHook(() => useLearningActivities(false));

      let activity;
      await act(async () => {
        activity = await result.current.getActivity('act-001');
      });

      expect(activity).toEqual(mockActivity);
      expect(result.current.currentActivity).toEqual(mockActivity);
    });

    it('should handle get activity errors', async () => {
      mockAPI.learningActivitiesAPI.getActivity.mockRejectedValue(
        new Error('Activity not found')
      );

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.getActivity('invalid-id');
      });

      expect(result.current.error).toBeDefined();
    });
  });

  describe('updateProgress', () => {
    it('should update activity progress', async () => {
      const updatedActivity = { ...mockActivity, progress_percent: 65 };
      mockAPI.learningActivitiesAPI.updateProgress.mockResolvedValue(
        updatedActivity
      );

      const { result } = renderHook(() => useLearningActivities(false));

      // Set current activity first
      await act(async () => {
        result.current.startActivity('resource-python', 'PA01');
        await new Promise((resolve) => setTimeout(resolve, 0));
      });

      // Update progress
      let updated;
      await act(async () => {
        updated = await result.current.updateProgress('act-001', 65, 90);
      });

      expect(updated?.progress_percent).toBe(65);
      expect(result.current.currentActivity?.progress_percent).toBe(65);
    });

    it('should update activity in list', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [mockActivity],
        total_count: 1,
      });
      const updatedActivity = { ...mockActivity, progress_percent: 75 };
      mockAPI.learningActivitiesAPI.updateProgress.mockResolvedValue(
        updatedActivity
      );

      const { result } = renderHook(() => useLearningActivities(true));

      await waitFor(() => {
        expect(result.current.activities).toHaveLength(1);
      });

      await act(async () => {
        await result.current.updateProgress('act-001', 75);
      });

      expect(result.current.activities[0].progress_percent).toBe(75);
    });
  });

  describe('completeActivity', () => {
    it('should complete activity', async () => {
      const mockCompleteResponse = {
        activity: mockCompletedActivity,
        evidence_created: true,
        evidence_id: 'ev-001',
        evidence_type: 'LEARNING_ACTIVITY',
        evidence_confidence: 0.3,
        note: 'Learning activity completed',
        current_competency_level: 2.5,
        current_skill_gap: 1.5,
        next_step: 'Take an assessment',
      };
      mockAPI.learningActivitiesAPI.completeActivity.mockResolvedValue(
        mockCompleteResponse
      );

      const { result } = renderHook(() => useLearningActivities(false));

      let completed;
      await act(async () => {
        completed = await result.current.completeActivity('act-001', 85);
      });

      expect(completed?.activity.status).toBe('completed');
      expect(completed?.evidence_confidence).toBe(0.3);
      expect(result.current.currentActivity?.status).toBe('completed');
    });

    it('should handle completion errors', async () => {
      mockAPI.learningActivitiesAPI.completeActivity.mockRejectedValue(
        new Error('Completion failed')
      );

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.completeActivity('act-001');
      });

      expect(result.current.error).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should clear errors', async () => {
      mockAPI.learningActivitiesAPI.startActivity.mockRejectedValue(
        new Error('Error')
      );

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.startActivity('resource', 'competency');
      });

      expect(result.current.error).toBeDefined();

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should handle API errors gracefully', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockRejectedValue({
        response: { data: { detail: 'Server error' } },
      });

      const { result } = renderHook(() => useLearningActivities(true));

      await waitFor(() => {
        expect(result.current.error).toBeDefined();
      });
    });
  });

  describe('refresh', () => {
    it('should refresh activities list', async () => {
      mockAPI.learningActivitiesAPI.getActivities.mockResolvedValue({
        activities: [mockActivity],
        total_count: 1,
      });

      const { result } = renderHook(() => useLearningActivities(false));

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.activities).toHaveLength(1);
      expect(mockAPI.learningActivitiesAPI.getActivities).toHaveBeenCalled();
    });
  });
});
