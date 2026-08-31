/**
 * API Client Tests
 * Tests for learning activities, skill gaps, recommendations, evidence, and competency APIs
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import {
  learningActivitiesAPI,
  skillGapsAPI,
  recommendationsAPI,
  evidenceAPI,
  competencyAPI,
  setAuthToken,
  clearAuth,
  isAuthenticated,
  LearningActivity,
} from '../api';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as any;

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Authentication', () => {
    it('should set auth token in localStorage', () => {
      setAuthToken('test-token');
      expect(localStorage.getItem('shikshasetu_demo_token')).toBe('test-token');
    });

    it('should clear auth token', () => {
      localStorage.setItem('shikshasetu_demo_token', 'test-token');
      clearAuth();
      expect(localStorage.getItem('shikshasetu_demo_token')).toBeNull();
    });

    it('should check if authenticated', () => {
      expect(isAuthenticated()).toBe(false);
      setAuthToken('test-token');
      expect(isAuthenticated()).toBe(true);
      clearAuth();
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('Learning Activities API', () => {
    const mockActivity: LearningActivity = {
      activity_id: 'act-001',
      user_id: 'user-001',
      resource_id: 'resource-python',
      competency_id: 'PA01',
      status: 'in_progress',
      started_at: '2026-08-27T10:00:00Z',
      completed_at: null,
      last_accessed_at: '2026-08-27T14:30:00Z',
      progress_percent: 45,
      duration_minutes: 120,
      notes: 'Learning in progress',
    };

    it('should start a learning activity', async () => {
      mockedAxios.post.mockResolvedValue({ data: mockActivity });
      
      const result = await learningActivitiesAPI.startActivity('resource-python', 'PA01');
      
      expect(result).toEqual(mockActivity);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/learning-activities',
        expect.objectContaining({
          resource_id: 'resource-python',
          competency_id: 'PA01',
        })
      );
    });

    it('should get list of activities', async () => {
      const mockResponse = {
        activities: [mockActivity],
        total_count: 1,
      };
      mockedAxios.get.mockResolvedValue({ data: mockResponse });
      
      const result = await learningActivitiesAPI.getActivities();
      
      expect(result.activities).toEqual([mockActivity]);
      expect(result.total_count).toBe(1);
    });

    it('should get specific activity', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockActivity });
      
      const result = await learningActivitiesAPI.getActivity('act-001');
      
      expect(result).toEqual(mockActivity);
      expect(mockedAxios.get).toHaveBeenCalledWith('/learning-activities/act-001');
    });

    it('should update progress', async () => {
      const updatedActivity = { ...mockActivity, progress_percent: 65 };
      mockedAxios.put.mockResolvedValue({ data: updatedActivity });
      
      const result = await learningActivitiesAPI.updateProgress('act-001', 65, 90);
      
      expect(result.progress_percent).toBe(65);
      expect(mockedAxios.put).toHaveBeenCalledWith(
        '/learning-activities/act-001',
        expect.objectContaining({
          progress_percent: 65,
          duration_minutes: 90,
        })
      );
    });

    it('should complete activity', async () => {
      const completedActivity = { ...mockActivity, status: 'completed', progress_percent: 100 };
      const mockCompleteResponse = {
        activity: completedActivity,
        evidence_created: true,
        evidence_id: 'ev-001',
        evidence_type: 'LEARNING_ACTIVITY',
        evidence_confidence: 0.3,
        note: 'Learning activity completed',
        current_competency_level: 2.5,
        current_skill_gap: 1.5,
        next_step: 'Take an assessment to update competency',
      };
      mockedAxios.post.mockResolvedValue({ data: mockCompleteResponse });
      
      const result = await learningActivitiesAPI.completeActivity('act-001', 85);
      
      expect(result.activity.status).toBe('completed');
      expect(result.evidence_created).toBe(true);
      expect(result.evidence_confidence).toBe(0.3);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/learning-activities/act-001/complete',
        expect.objectContaining({
          final_score: 85,
        })
      );
    });

    it('should get completed resources', async () => {
      const completedActivity = { ...mockActivity, status: 'completed' };
      mockedAxios.get.mockResolvedValue({
        data: {
          activities: [completedActivity],
          total_count: 1,
        },
      });
      
      const result = await learningActivitiesAPI.getCompletedResources();
      
      expect(result).toContain('resource-python');
    });

    it('should get in-progress resources', async () => {
      mockedAxios.get.mockResolvedValue({
        data: {
          activities: [mockActivity],
          total_count: 1,
        },
      });
      
      const result = await learningActivitiesAPI.getInProgressResources();
      
      expect(result).toContain('resource-python');
    });
  });

  describe('Skill Gaps API', () => {
    it('should fetch skill gaps', async () => {
      const mockGaps = [
        {
          competency_id: 'PA01',
          competency_name: 'Python',
          domain: 'Technical',
          current_level: 2.5,
          required_level: 4.0,
          gap: 1.5,
          priority: 'high',
        },
      ];
      mockedAxios.get.mockResolvedValue({ data: mockGaps });
      
      const result = await skillGapsAPI.getGaps();
      
      expect(result).toEqual(mockGaps);
      expect(result[0].gap).toBe(1.5);
    });

    it('should handle array response format', async () => {
      const mockGaps = [{ competency_id: 'PA01', gap: 1.5 }];
      mockedAxios.get.mockResolvedValue({ data: mockGaps });
      
      const result = await skillGapsAPI.getGaps();
      
      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(1);
    });
  });

  describe('Recommendations API', () => {
    it('should fetch recommendations', async () => {
      const mockRecommendations = [
        {
          resource_id: 'res-001',
          title: 'Python for Public Data Analysis',
          provider: 'iGOT',
          competency_id: 'PA01',
          target: 'Python',
          difficulty: 'Intermediate',
          duration_minutes: 380,
          match_score: 94.5,
          meta: 'Intermediate · 6h 20m',
        },
      ];
      mockedAxios.get.mockResolvedValue({ data: mockRecommendations });
      
      const result = await recommendationsAPI.getRecommendations();
      
      expect(result).toEqual(mockRecommendations);
      expect(result[0].match_score).toBe(94.5);
    });

    it('should fetch recommendations for specific competency', async () => {
      const mockRecommendations = [{ resource_id: 'res-001' }];
      mockedAxios.get.mockResolvedValue({ data: mockRecommendations });
      
      const result = await recommendationsAPI.getRecommendations('PA01');
      
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/learning-resources/recommendations',
        expect.objectContaining({
          params: expect.objectContaining({
            competency_id: 'PA01',
          }),
        })
      );
    });

    it('should get resource details', async () => {
      const mockResource = {
        resource_id: 'res-001',
        title: 'Python for Data Analysis',
      };
      mockedAxios.get.mockResolvedValue({ data: mockResource });
      
      const result = await recommendationsAPI.getResourceDetails('res-001');
      
      expect(result).toEqual(mockResource);
      expect(mockedAxios.get).toHaveBeenCalledWith('/learning-resources/res-001');
    });
  });

  describe('Evidence API', () => {
    it('should fetch evidence for competency', async () => {
      const mockEvidence = [
        {
          id: 'ev-001',
          type: 'LEARNING_ACTIVITY',
          confidence: 0.3,
          score: 85,
          recorded_at: '2026-08-27T14:30:00Z',
          source: { activity_id: 'act-001', resource_id: 'res-001' },
          notes: 'Learning activity completed',
        },
      ];
      mockedAxios.get.mockResolvedValue({ data: mockEvidence });
      
      const result = await evidenceAPI.getEvidence('PA01');
      
      expect(result).toEqual(mockEvidence);
      expect(result[0].confidence).toBe(0.3);
    });

    it('should fetch all evidence', async () => {
      const mockEvidence = [{ id: 'ev-001', type: 'LEARNING_ACTIVITY' }];
      mockedAxios.get.mockResolvedValue({ data: mockEvidence });
      
      const result = await evidenceAPI.getAllEvidence();
      
      expect(result).toEqual(mockEvidence);
      expect(mockedAxios.get).toHaveBeenCalledWith('/competency-evidence');
    });
  });

  describe('Competency API', () => {
    it('should fetch competency profile', async () => {
      const mockProfile = {
        competencies: [
          { id: 'PA01', name: 'Python', current_level: 2.5 },
        ],
      };
      mockedAxios.get.mockResolvedValue({ data: mockProfile });
      
      const result = await competencyAPI.getProfile();
      
      expect(result.competencies).toHaveLength(1);
      expect(result.competencies[0].name).toBe('Python');
    });

    it('should get specific competency', async () => {
      const mockCompetency = {
        id: 'PA01',
        name: 'Python',
        current_level: 2.5,
        required_level: 4.0,
      };
      mockedAxios.get.mockResolvedValue({ data: mockCompetency });
      
      const result = await competencyAPI.getCompetency('PA01');
      
      expect(result.name).toBe('Python');
      expect(result.current_level).toBe(2.5);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const mockError = {
        response: { data: { detail: 'Activity not found' } },
        message: 'Not Found',
      };
      mockedAxios.get.mockRejectedValue(mockError);
      
      try {
        await learningActivitiesAPI.getActivity('invalid-id');
      } catch (error: any) {
        expect(error).toEqual(mockError);
      }
    });

    it('should return empty array on skill gaps error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      
      const result = await skillGapsAPI.getGaps();
      
      expect(result).toEqual([]);
    });

    it('should return empty array on recommendations error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      
      const result = await recommendationsAPI.getRecommendations();
      
      expect(result).toEqual([]);
    });

    it('should return empty array on evidence error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      
      const result = await evidenceAPI.getAllEvidence();
      
      expect(result).toEqual([]);
    });
  });
});
