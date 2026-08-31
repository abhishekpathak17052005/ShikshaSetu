/**
 * useLearningActivities Hook
 * Manages learning activity state and provides methods to interact with learning activities API
 */

import { useState, useCallback, useEffect } from 'react';
import {
  api,
  LearningActivity,
  LearningActivityListResponse,
  LearningActivityCompleteResponse,
} from '../lib/api';

export interface UseLearningActivitiesReturn {
  // State
  activities: LearningActivity[];
  currentActivity: LearningActivity | null;
  loading: boolean;
  error: string | null;
  
  // Methods
  startActivity: (resourceId: string, competencyId: string) => Promise<LearningActivity | null>;
  listActivities: (status?: string) => Promise<void>;
  getActivity: (activityId: string) => Promise<LearningActivity | null>;
  updateProgress: (activityId: string, progress: number, duration?: number, notes?: string) => Promise<LearningActivity | null>;
  completeActivity: (activityId: string, finalScore?: number, notes?: string) => Promise<LearningActivityCompleteResponse | null>;
  clearError: () => void;
  refresh: () => Promise<void>;
}

/**
 * Hook to manage learning activities
 * Provides state management and methods for interacting with learning activities
 */
export function useLearningActivities(autoLoad: boolean = true): UseLearningActivitiesReturn {
  const [activities, setActivities] = useState<LearningActivity[]>([]);
  const [currentActivity, setCurrentActivity] = useState<LearningActivity | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Start a new learning activity
   */
  const startActivity = useCallback(
    async (resourceId: string, competencyId: string): Promise<LearningActivity | null> => {
      setLoading(true);
      setError(null);
      try {
        const activity = await api.learningActivities.start({ resource_id: resourceId, competency_id: competencyId });
        setCurrentActivity(activity);
        setActivities((prev) => [activity, ...prev]);
        return activity;
      } catch (err: any) {
        const errorMsg = err.message || 'Failed to start learning activity';
        setError(errorMsg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * Load all activities with optional status filter
   */
  const listActivities = useCallback(async (status?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response: LearningActivityListResponse = await api.learningActivities.list(status);
      setActivities(response.activities || []);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load activities';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get details of specific activity
   */
  const getActivity = useCallback(async (activityId: string): Promise<LearningActivity | null> => {
    setLoading(true);
    setError(null);
    try {
      const activity = await api.learningActivities.get(activityId);
      setCurrentActivity(activity);
      return activity;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load activity';
      setError(errorMsg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Update progress on current activity
   */
  const updateProgress = useCallback(
    async (
      activityId: string,
      progress: number,
      duration?: number,
      notes?: string
    ): Promise<LearningActivity | null> => {
      setLoading(true);
      setError(null);
      try {
        const updated = await api.learningActivities.update(
          activityId,
          {
            progress_percent: progress,
            duration_minutes: duration,
            notes,
          }
        );
        setCurrentActivity(updated);
        setActivities((prev) =>
          prev.map((a) => (a.activity_id === activityId ? updated : a))
        );
        return updated;
      } catch (err: any) {
        const errorMsg = err.message || 'Failed to update progress';
        setError(errorMsg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * Complete activity and generate supporting evidence
   */
  const completeActivity = useCallback(
    async (
      activityId: string,
      finalScore?: number,
      notes?: string
    ): Promise<LearningActivityCompleteResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.learningActivities.complete(
          activityId,
          {
            final_score: finalScore,
            notes,
          }
        );
        setCurrentActivity(result.activity);
        setActivities((prev) =>
          prev.map((a) => (a.activity_id === activityId ? result.activity : a))
        );
        return result;
      } catch (err: any) {
        const errorMsg = err.message || 'Failed to complete activity';
        setError(errorMsg);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Refresh activities list
   */
  const refresh = useCallback(async () => {
    await listActivities();
  }, [listActivities]);

  /**
   * Auto-load activities on mount if enabled
   */
  useEffect(() => {
    if (autoLoad) {
      listActivities();
    }
  }, [autoLoad, listActivities]);

  return {
    activities,
    currentActivity,
    loading,
    error,
    startActivity,
    listActivities,
    getActivity,
    updateProgress,
    completeActivity,
    clearError,
    refresh,
  };
}

export default useLearningActivities;
