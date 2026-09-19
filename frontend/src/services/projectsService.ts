import { ApiResponse } from "@/types/api";
import { authService } from "./authService";

export interface ProjectItem {
  id: string;
  space_id: string;
  owner_id: string;
  name: string;
  description?: string | null;
  learning_goal?: string | null;
  status: "active" | "archived" | "completed";
  materials_count?: number;
  progress?: number;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface PaginatedProjects {
  items: ProjectItem[];
  total: number;
  page: number;
  limit: number;
}

export interface CreateProjectPayload {
  space_id: string;
  name: string;
  description?: string;
  learning_goal?: string;
}

export interface UpdateProjectPayload {
  name?: string;
  description?: string;
  learning_goal?: string;
  status?: "active" | "archived" | "completed";
}

export const projectsService = {
  async listProjects(
    spaceId?: string,
    statusFilter?: string,
    search?: string,
    page = 1,
    limit = 20
  ): Promise<PaginatedProjects> {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (spaceId) params.append("space_id", spaceId);
    if (statusFilter) params.append("status", statusFilter);
    if (search) params.append("search", search);

    const response = await fetch(`/api/v1/projects?${params.toString()}`, {
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<PaginatedProjects> = await response.json();
    if (response.status === 401) {
      authService.clearToken();
      window.location.href = "/login";
      throw new Error("Session expired. Please sign in again.");
    }
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch projects.");
    }
    return result.data;
  },

  async createProject(payload: CreateProjectPayload): Promise<ProjectItem> {
    const response = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const result: ApiResponse<ProjectItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to create project.");
    }
    return result.data;
  },

  async getProject(projectId: string): Promise<ProjectItem> {
    const response = await fetch(`/api/v1/projects/${projectId}`, {
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<ProjectItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch project details.");
    }
    return result.data;
  },

  async updateProject(projectId: string, payload: UpdateProjectPayload): Promise<ProjectItem> {
    const response = await fetch(`/api/v1/projects/${projectId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const result: ApiResponse<ProjectItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to update project.");
    }
    return result.data;
  },

  async archiveProject(projectId: string): Promise<ProjectItem> {
    const response = await fetch(`/api/v1/projects/${projectId}`, {
      method: "DELETE",
      headers: { ...authService.getAuthHeaders() },
    });

    const result: ApiResponse<ProjectItem> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to archive project.");
    }
    return result.data;
  },
};
