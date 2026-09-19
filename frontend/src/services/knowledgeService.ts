import { authService } from "./authService";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";

export interface CitationItem {
  citation_id: string;
  material_id: string;
  material_name: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
}

export interface RetrievalDiagnosticsItem {
  query: string;
  candidate_count: number;
  selected_count: number;
  similarity_scores: number[];
  reranking_scores: number[];
  source_pages: number[];
}

export interface RetrievalSearchResult {
  context: string;
  citations: CitationItem[];
  diagnostics: RetrievalDiagnosticsItem;
}

export interface ConceptItem {
  id: string;
  project_id: string;
  name: string;
  definition?: string | null;
  domain?: string | null;
  created_at: string;
}

export interface KnowledgeChunkItem {
  id: string;
  project_id: string;
  material_id: string;
  page_number: number;
  chunk_index: number;
  section_title?: string | null;
  content: string;
  metadata_json?: {
    word_count?: number;
    char_count?: number;
  } | null;
  created_at: string;
}

export interface PaginatedKnowledgeChunks {
  items: KnowledgeChunkItem[];
  total: number;
  page: number;
  limit: number;
}

export const knowledgeService = {
  async indexMaterial(projectId: string, materialId: string): Promise<{ chunks_indexed: number }> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/knowledge/index/${materialId}`), {
      method: "POST",
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<{ chunks_indexed: number }>(response, "Failed to index material knowledge");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to index material knowledge.");
    }
    return result.data;
  },

  async searchKnowledge(
    projectId: string,
    query: string,
    topK = 5,
    threshold = 0.05,
    materialId?: string
  ): Promise<RetrievalSearchResult> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/knowledge/search`), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify({ query, top_k: topK, threshold, material_id: materialId || null }),
    });

    const result = await parseApiResponse<RetrievalSearchResult>(response, "Failed to execute knowledge search query");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to execute knowledge search query.");
    }
    return result.data;
  },

  async listConcepts(projectId: string): Promise<ConceptItem[]> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/knowledge/concepts`), {
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<ConceptItem[]>(response, "Failed to fetch project concepts");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch project concepts.");
    }
    return result.data;
  },

  async listChunks(
    projectId: string,
    page = 1,
    limit = 50
  ): Promise<PaginatedKnowledgeChunks> {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/knowledge/chunks?${params.toString()}`), {
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<PaginatedKnowledgeChunks>(response, "Failed to fetch knowledge chunks");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch knowledge chunks.");
    }
    return result.data;
  },
};

