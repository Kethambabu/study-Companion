import { authService } from "./authService";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";
import { fetchWithCache, invalidateCache } from "./apiCache";

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
    const key = `projects:${spaceId || ""}:${statusFilter || ""}:${search || ""}:${page}:${limit}`;
    return fetchWithCache(
      key,
      async () => {
        const params = new URLSearchParams({ page: String(page), limit: String(limit) });
        if (spaceId) params.append("space_id", spaceId);
        if (statusFilter) params.append("status", statusFilter);
        if (search) params.append("search", search);

        const response = await fetch(buildUrl(`/api/v1/projects?${params.toString()}`), {
          headers: { ...authService.getAuthHeaders() },
        });

        if (response.status === 401) {
          authService.clearToken();
          window.location.href = "/login";
          throw new Error("Session expired. Please sign in again.");
        }

        const result = await parseApiResponse<PaginatedProjects>(response, "Failed to fetch projects");
        if (!result.success || !result.data) {
          throw new Error(result.error?.message || "Failed to fetch projects.");
        }
        return result.data;
      },
      15000
    );
  },

  async createProject(payload: CreateProjectPayload): Promise<ProjectItem> {
    const response = await fetch(buildUrl("/api/v1/projects"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const result = await parseApiResponse<ProjectItem>(response, "Failed to create project");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to create project.");
    }
    invalidateCache("projects:");
    invalidateCache("analytics:");
    return result.data;
  },

  async getProject(projectId: string): Promise<ProjectItem> {
    return fetchWithCache(
      `project:${projectId}`,
      async () => {
        const response = await fetch(buildUrl(`/api/v1/projects/${projectId}`), {
          headers: { ...authService.getAuthHeaders() },
        });

        const result = await parseApiResponse<ProjectItem>(response, "Failed to fetch project details");
        if (!result.success || !result.data) {
          throw new Error(result.error?.message || "Failed to fetch project details.");
        }
        return result.data;
      },
      15000
    );
  },

  async updateProject(projectId: string, payload: UpdateProjectPayload): Promise<ProjectItem> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}`), {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const result = await parseApiResponse<ProjectItem>(response, "Failed to update project");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to update project.");
    }
    invalidateCache("projects:");
    invalidateCache(`project:${projectId}`);
    invalidateCache("analytics:");
    return result.data;
  },

  async archiveProject(projectId: string): Promise<ProjectItem> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}`), {
      method: "DELETE",
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<ProjectItem>(response, "Failed to archive project");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to archive project.");
    }
    invalidateCache("projects:");
    invalidateCache(`project:${projectId}`);
    invalidateCache("analytics:");
    return result.data;
  },
};
