import { ApiResponse } from "@/types/api";
import { authService } from "./authService";

export interface RecommendationItem {
  id: string;
  project_id: string;
  user_id: string;
  action_type: "review_material" | "take_quiz" | "practice_concept" | "review_mistakes" | "ask_tutor";
  title: string;
  description: string;
  reason?: string;
  action?: string;
  concept_id?: string;
  target_concept_id?: string;
  target_resource_id?: string;
  priority_score: number;
  status: "active" | "completed" | "dismissed";
  reason_evidence: Record<string, unknown>;
  created_at: string;
  completed_at?: string;
}

export interface NextActionCardData {
  recommendation: RecommendationItem | null;
  reason: string;
  cta_label: string;
  cta_path: string;
  evidence_summary: string[];
}

export const recommendationService = {
  getNextActionCard: async (projectId: string): Promise<NextActionCardData> => {
    const res = await fetch(`/api/v1/projects/${projectId}/recommendations/next-action`, {
      headers: { ...authService.getAuthHeaders() },
    });
    const result: ApiResponse<NextActionCardData> = await res.json();
    if (!res.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch Next Action recommendation.");
    }
    return result.data;
  },

  listRecommendations: async (projectId: string): Promise<RecommendationItem[]> => {
    const res = await fetch(`/api/v1/projects/${projectId}/recommendations`, {
      headers: { ...authService.getAuthHeaders() },
    });
    const result: ApiResponse<RecommendationItem[]> = await res.json();
    if (!res.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to list recommendations.");
    }
    return result.data;
  },

  completeRecommendation: async (
    projectId: string,
    recommendationId: string
  ): Promise<RecommendationItem> => {
    const res = await fetch(
      `/api/v1/projects/${projectId}/recommendations/${recommendationId}/complete`,
      {
        method: "POST",
        headers: { ...authService.getAuthHeaders() },
      }
    );
    const result: ApiResponse<RecommendationItem> = await res.json();
    if (!res.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to complete recommendation.");
    }
    return result.data;
  },
};
