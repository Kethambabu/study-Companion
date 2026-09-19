import { ApiResponse } from "@/types/api";
import { authService } from "./authService";

export interface WeakConceptItem {
  concept_id: string;
  mastery_score: number;
  confidence: number;
  status: string;
  recent_errors_count: number;
  recommendation: string;
}

export interface StrengthConceptItem {
  concept_id: string;
  mastery_score: number;
  confidence: number;
  status: string;
  mastery_level: string;
}

export interface RepeatedMistakeItem {
  concept_id: string;
  topic_question: string;
  mistake_count: number;
  last_error_at: string;
  suggested_fix: string;
}

export interface NextActionItem {
  id: string;
  action_type: "review_document" | "practice_quiz" | "ask_tutor" | "take_assessment";
  title: string;
  description: string;
  concept_id: string;
  priority: "high" | "medium" | "low";
  target_url?: string;
  page_reference?: string;
}

export interface LearningGoalItem {
  goal_id: string;
  title: string;
  target_mastery_pct: number;
  current_mastery_pct: number;
  is_achieved: boolean;
  progress_percentage: number;
}

export interface LearningIntelligenceSummaryResponse {
  project_id: string;
  user_id: string;
  weak_concepts: WeakConceptItem[];
  strong_concepts: StrengthConceptItem[];
  repeated_mistakes: RepeatedMistakeItem[];
  next_actions: NextActionItem[];
  learning_goals: LearningGoalItem[];
  generated_at: string;
}

export const intelligenceService = {
  getIntelligenceSummary: async (projectId: string): Promise<LearningIntelligenceSummaryResponse> => {
    const res = await fetch(`/api/v1/projects/${projectId}/intelligence`, {
      headers: { ...authService.getAuthHeaders() },
    });
    const result: ApiResponse<LearningIntelligenceSummaryResponse> = await res.json();
    if (!res.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch learning intelligence summary.");
    }
    return result.data;
  },
};
