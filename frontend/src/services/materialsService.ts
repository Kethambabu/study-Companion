import { authService } from "./authService";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";
import { fetchWithCache, invalidateCache } from "./apiCache";

export interface MaterialItem {
  id: string;
  project_id: string;
  owner_id: string;
  filename: string;
  content_type: string;
  storage_path: string;
  file_size: number;
  checksum: string;
  status: "uploaded" | "queued" | "processing" | "ready" | "failed";
  progress_pct?: number;
  current_step?: string;
  error_code?: string | null;
  word_count?: number;
  estimated_reading_minutes?: number;
  attempt_count: number;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  failed_at?: string | null;
  page_count: number;
}

export interface PaginatedMaterials {
  items: MaterialItem[];
  total: number;
  page: number;
  limit: number;
}

export interface MaterialPageItem {
  id: string;
  material_id: string;
  page_number: number;
  extracted_text: string;
  metadata_json?: {
    char_count?: number;
    word_count?: number;
    extraction_method?: string;
  } | null;
  created_at: string;
}

export interface PaginatedMaterialPages {
  items: MaterialPageItem[];
  total: number;
  page: number;
  limit: number;
}

export const materialsService = {
  async listMaterials(
    projectId?: string,
    search?: string,
    page = 1,
    limit = 20
  ): Promise<PaginatedMaterials> {
    const key = `materials:${projectId || ""}:${search || ""}:${page}:${limit}`;
    return fetchWithCache(
      key,
      async () => {
        const params = new URLSearchParams({ page: String(page), limit: String(limit) });
        if (search) params.append("search", search);

        const path = projectId
          ? `/api/v1/projects/${projectId}/materials?${params.toString()}`
          : `/api/v1/materials?${params.toString()}`;

        const response = await fetch(buildUrl(path), {
          headers: { ...authService.getAuthHeaders() },
        });

        const result = await parseApiResponse<PaginatedMaterials>(response, "Failed to fetch materials");
        if (!result.success || !result.data) {
          throw new Error(result.error?.message || "Failed to fetch materials.");
        }
        return result.data;
      },
      10000
    );
  },

  async uploadMaterial(
    projectId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<MaterialItem> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", buildUrl(`/api/v1/projects/${projectId}/materials`));

      const headers = authService.getAuthHeaders();
      Object.entries(headers).forEach(([key, val]) => {
        xhr.setRequestHeader(key, val);
      });

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        try {
          const result = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300 && result.success && result.data) {
            invalidateCache("materials:");
            resolve(result.data);
          } else {
            reject(new Error(result?.error?.message || result?.detail || "Material upload failed."));
          }
        } catch {
          reject(new Error("Failed to parse server upload response."));
        }
      };

      xhr.onerror = () => reject(new Error("Network error during material upload."));

      const formData = new FormData();
      formData.append("file", file);
      xhr.send(formData);
    });
  },

  async getMaterial(materialId: string): Promise<MaterialItem> {
    return fetchWithCache(
      `material:${materialId}`,
      async () => {
        const response = await fetch(buildUrl(`/api/v1/materials/${materialId}`), {
          headers: { ...authService.getAuthHeaders() },
        });

        const result = await parseApiResponse<MaterialItem>(response, "Failed to fetch material details");
        if (!result.success || !result.data) {
          throw new Error(result.error?.message || "Failed to fetch material details.");
        }
        return result.data;
      },
      10000
    );
  },

  async getMaterialPages(
    materialId: string,
    page = 1,
    limit = 50
  ): Promise<PaginatedMaterialPages> {
    return fetchWithCache(
      `material_pages:${materialId}:${page}:${limit}`,
      async () => {
        const params = new URLSearchParams({ page: String(page), limit: String(limit) });
        const response = await fetch(buildUrl(`/api/v1/materials/${materialId}/pages?${params.toString()}`), {
          headers: { ...authService.getAuthHeaders() },
        });

        const result = await parseApiResponse<PaginatedMaterialPages>(response, "Failed to fetch material pages");
        if (!result.success || !result.data) {
          throw new Error(result.error?.message || "Failed to fetch material pages.");
        }
        return result.data;
      },
      30000
    );
  },

  async retryMaterial(materialId: string): Promise<MaterialItem> {
    const response = await fetch(buildUrl(`/api/v1/materials/${materialId}/retry`), {
      method: "POST",
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<MaterialItem>(response, "Failed to retry material processing");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to retry material processing.");
    }
    invalidateCache("materials:");
    invalidateCache(`material:${materialId}`);
    return result.data;
  },
};
