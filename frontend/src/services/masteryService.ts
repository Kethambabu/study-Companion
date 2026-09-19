import { authService } from "./authService";
import { fetchWithCache } from "./apiCache";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";

export interface ConceptMasteryItem {
  id: string;
  project_id: string;
  user_id: string;
  concept_id: string;
  mastery_score: number;
  confidence?: number;
  status: "improving" | "stable" | "requiring_attention";
  last_evaluated_at?: string;
  last_updated_at: string;
}

export interface MasteryExplanationItem {
  concept_id: string;
  current_mastery: number;
  previous_mastery: number;
  delta: number;
  status: "improving" | "stable" | "requiring_attention";
  explanation: string;
  evidence_breakdown: Array<{
    event_id: string;
    event_type: string;
    previous_mastery: number;
    new_mastery: number;
    delta: number;
    evidence: Record<string, unknown>;
    timestamp: string;
  }>;
  last_updated_at?: string;
}

export interface GrowthSummaryItem {
  project_id: string;
  user_id: string;
  overall_mastery: number;
  total_concepts: number;
  improving_count: number;
  stable_count: number;
  requiring_attention_count: number;
  improving_concepts: ConceptMasteryItem[];
  stable_concepts: ConceptMasteryItem[];
  weak_concepts: ConceptMasteryItem[];
  has_sufficient_data: boolean;
  last_snapshot_at?: string;
}

export interface GrowthSnapshotItem {
  id: string;
  project_id: string;
  user_id: string;
  snapshot_date: string;
  average_mastery: number;
  status_counts: Record<string, number>;
  weak_concept_count: number;
  snapshot_data: Record<string, unknown>;
}

export const masteryService = {
  listMasteries: async (projectId: string): Promise<ConceptMasteryItem[]> => {
    const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/mastery`), {
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<ConceptMasteryItem[]>(res, "Failed to fetch concept masteries");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch concept masteries.");
    }
    return result.data;
  },

  getExplanation: async (projectId: string, conceptId: string): Promise<MasteryExplanationItem> => {
    const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/mastery/${encodeURIComponent(conceptId)}/explanation`), {
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<MasteryExplanationItem>(res, "Failed to fetch mastery explanation");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch mastery explanation.");
    }
    return result.data;
  },

  getGrowthSummary: async (projectId: string): Promise<GrowthSummaryItem> => {
    return fetchWithCache(`growth:${projectId}`, async () => {
      const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/growth/summary`), {
        headers: { ...authService.getAuthHeaders() },
      });
      const result = await parseApiResponse<GrowthSummaryItem>(res, "Failed to fetch growth summary");
      if (!result.success || !result.data) {
        throw new Error(result.error?.message || "Failed to fetch growth summary.");
      }
      return result.data;
    }, 15000);
  },

  getGrowthSnapshots: async (projectId: string): Promise<GrowthSnapshotItem[]> => {
    const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/growth/snapshots`), {
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<GrowthSnapshotItem[]>(res, "Failed to fetch growth snapshots");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch growth snapshots.");
    }
    return result.data;
  },
};

