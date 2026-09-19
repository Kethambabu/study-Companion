import { ApiResponse } from "@/types/api";
import { authService } from "./authService";

export interface SpaceVisualMetadata {
  icon?: string;
  color_theme?: string;
  banner_url?: string;
}

export interface SpaceItem {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  visual_metadata?: SpaceVisualMetadata | null;
  owner_id: string;
  role: string;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface PaginatedSpaces {
  items: SpaceItem[];
  total: number;
  page: number;
  limit: number;
}

export const spacesService = {
  async listSpaces(search?: string, page = 1, limit = 20): Promise<PaginatedSpaces> {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (search) params.append("search", search);

    const response = await fetch(`/api/v1/spaces?${params.toString()}`, {
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<PaginatedSpaces> = await response.json();
    if (response.status === 401) {
      authService.clearToken();
      window.location.href = "/login";
      throw new Error("Session expired. Please sign in again.");
    }
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch spaces.");
    }
    return result.data;
  },

  async createSpace(name: string, slug: string, description?: string, visual_metadata?: SpaceVisualMetadata): Promise<SpaceItem> {
    const response = await fetch("/api/v1/spaces", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify({ name, slug, description, visual_metadata }),
    });

    const result: ApiResponse<SpaceItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to create space.");
    }
    return result.data;
  },

  async getSpace(spaceId: string): Promise<SpaceItem> {
    const response = await fetch(`/api/v1/spaces/${spaceId}`, {
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<SpaceItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to load space details.");
    }
    return result.data;
  },

  async updateSpace(spaceId: string, payload: { name?: string; description?: string; visual_metadata?: SpaceVisualMetadata }): Promise<SpaceItem> {
    const response = await fetch(`/api/v1/spaces/${spaceId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const result: ApiResponse<SpaceItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to update space.");
    }
    return result.data;
  },

  async archiveSpace(spaceId: string): Promise<SpaceItem> {
    const response = await fetch(`/api/v1/spaces/${spaceId}`, {
      method: "DELETE",
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<SpaceItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to archive space.");
    }
    return result.data;
  },
};
