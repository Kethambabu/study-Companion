import { authService } from "./authService";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";

export interface ConceptTrendPoint {
  concept_id: string;
  concept_name: string;
  current_mastery: number;
  previous_mastery: number;
  trend: "improving" | "stable" | "requiring_attention";
  change_delta: number;
}

export interface ActivityTimePoint {
  date: string;
  study_time_minutes: number;
  quizzes_taken: number;
  tutor_messages: number;
  mastery_change: number;
}

export interface ProjectAnalyticsData {
  project_id: string;
  learning_activity: ActivityTimePoint[];
  total_study_time_minutes: number;
  assessment_performance: Record<string, unknown>;
  mastery_summary: Record<string, unknown>;
  concept_trends: ConceptTrendPoint[];
  tutor_activity: Record<string, unknown>;
  material_activity: Record<string, unknown>;
  quiz_activity: Record<string, unknown>;
  // Section 18 Specific Fields
  tutor_questions_count: number;
  quiz_attempts_count: number;
  questions_answered_count: number;
  assessments_count: number;
  quiz_accuracy_pct: number;
  assessment_average_score: number;
  mastery_trend_weeks: Array<{ week: string; mastery: number }>;
  ai_tutor_interactions: number;
  ai_average_response_time_seconds: number;
}

export interface StudentGlobalAnalyticsData {
  total_projects: number;
  completed_projects: number;
  active_projects: number;
  overall_mastery_pct: number;
  learning_time_formatted: string;
  strongest_areas: string[];
  areas_to_improve: string[];
  recent_activity: Array<{
    event_type: string;
    title: string;
    project_name: string;
    timestamp: string;
  }>;
}

export const analyticsService = {
  getProjectAnalytics: async (projectId: string): Promise<ProjectAnalyticsData> => {
    const res = await fetch(buildUrl(`/api/v1/analytics/project/${projectId}`), {
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<ProjectAnalyticsData>(res, "Failed to fetch project analytics");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch project analytics.");
    }
    return result.data;
  },

  getStudentGlobalAnalytics: async (): Promise<StudentGlobalAnalyticsData> => {
    const res = await fetch(buildUrl(`/api/v1/analytics/student/global`), {
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<StudentGlobalAnalyticsData>(res, "Failed to fetch student global analytics");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch student global analytics.");
    }
    return result.data;
  },
};

