import { authService } from './authService';

export interface AdminOverview {
  total_users: number;
  total_spaces: number;
  total_projects: number;
  total_materials: number;
  total_quizzes: number;
  total_ai_tokens: number;
  active_users_24h: number;
  system_health_status: string;
  tutor_requests?: number;
  quiz_generations?: number;
  jobs_processing?: number;
  jobs_failed?: number;
  api_health?: string;
  database_health?: string;
  ai_provider_health?: string;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role?: string;
  is_admin: boolean;
  projects_count?: number;
  last_active?: string;
  space_count: number;
  created_at: string;
}

export interface ProjectProgressItem {
  id: string;
  title: string;
  progress_percentage: number;
}

export interface RecentActivityItem {
  id: string;
  timestamp: string;
  user_name: string;
  activity: string;
  project_title: string;
}

export interface UserLearningJourney {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  total_projects: number;
  active_projects: number;
  assessments_count: number;
  quiz_attempts_count: number;
  tutor_chats_count: number;
  overall_progress: number;
  projects: ProjectProgressItem[];
  recent_activity: RecentActivityItem[];
  tutor_requests: number;
  quiz_generations: number;
  ai_evaluations: number;
}

export interface AdminSpace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  owner_email: string;
  project_count: number;
  member_count: number;
  created_at: string;
}

export interface AdminProject {
  id: string;
  title: string;
  space_id: string;
  space_name: string;
  owner_id: string;
  material_count: number;
  concept_count: number;
  created_at: string;
}

export interface AdminActivity {
  id: string;
  event_type: string;
  user_id: string | null;
  user_name?: string | null;
  space_id?: string | null;
  space_name?: string | null;
  project_id: string | null;
  project_title?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AILog {
  id: string;
  request_id: string;
  user_id: string | null;
  project_id: string | null;
  feature: string;
  provider: string;
  model: string;
  latency_ms: number;
  tokens_used: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  success: boolean;
  error_category: string | null;
  retrieval_stats: Record<string, unknown> | null;
  created_at: string;
}

export interface AIEvaluation {
  total_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  groundedness_ratio: number;
  citation_accuracy: number;
  prompt_injection_attempts: number;
  error_breakdown: Record<string, number>;
  provider_token_share: Record<string, number>;
  tutor_eval?: Record<string, number>;
  retrieval_eval?: Record<string, number>;
  assessment_eval?: Record<string, number>;
  recommendations_eval?: Record<string, number>;
}

export interface BackgroundJob {
  id: string;
  job_type: string;
  status: string;
  attempts: number;
  duration_ms: number | null;
  error_message: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
}

export interface SystemHealth {
  status: string;
  database: string;
  redis: string;
  vector_store: string;
  event_stream: string;
  uptime_seconds: number;
  memory_usage_mb: number;
}

export interface ActivityTimePoint {
  date: string;
  study_time_minutes: number;
  quizzes_taken: number;
  tutor_messages: number;
  mastery_change: number;
}

export interface GlobalAnalytics {
  total_users: number;
  total_spaces: number;
  total_projects: number;
  total_materials: number;
  total_quizzes: number;
  total_tutor_messages: number;
  total_ai_tokens_used: number;
  avg_concept_mastery: number;
  activity_timeline: ActivityTimePoint[];
  top_active_projects: Array<{ project_id: string; title: string; activity_count: number }>;
}

async function handleArrayResponse<T>(res: Response): Promise<T[]> {
  if (!res.ok) {
    let msg = `Admin API request failed with status ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.message || msg;
    } catch {
      // ignore json parse error
    }
    throw new Error(msg);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

async function handleObjectResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `Admin API request failed with status ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.message || msg;
    } catch {
      // ignore json parse error
    }
    throw new Error(msg);
  }
  return res.json();
}

import { fetchWithCache } from './apiCache';

export const adminService = {
  getOverview: async (): Promise<AdminOverview> => {
    return fetchWithCache('admin_overview', async () => {
      const res = await fetch('/api/v1/admin/overview', {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleObjectResponse<AdminOverview>(res);
    }, 15000);
  },

  getUsers: async (search?: string): Promise<AdminUser[]> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchWithCache(`admin_users_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/users${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<AdminUser>(res);
    }, 15000);
  },

  getUserJourney: async (userId: string): Promise<UserLearningJourney> => {
    return fetchWithCache(`admin_user_journey_${userId}`, async () => {
      const res = await fetch(`/api/v1/admin/users/${userId}/journey`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleObjectResponse<UserLearningJourney>(res);
    }, 15000);
  },

  getSpaces: async (search?: string): Promise<AdminSpace[]> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchWithCache(`admin_spaces_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/spaces${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<AdminSpace>(res);
    }, 15000);
  },

  getProjects: async (search?: string): Promise<AdminProject[]> => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchWithCache(`admin_projects_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/projects${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<AdminProject>(res);
    }, 15000);
  },

  getActivity: async (params?: {
    user_id?: string;
    space_id?: string;
    project_id?: string;
    event_type?: string;
    time_range?: string;
  }): Promise<AdminActivity[]> => {
    const searchParams = new URLSearchParams();
    if (params?.user_id) searchParams.append('user_id', params.user_id);
    if (params?.space_id) searchParams.append('space_id', params.space_id);
    if (params?.project_id) searchParams.append('project_id', params.project_id);
    if (params?.event_type) searchParams.append('event_type', params.event_type);
    if (params?.time_range) searchParams.append('time_range', params.time_range);

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return fetchWithCache(`admin_activity_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/activity${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<AdminActivity>(res);
    }, 15000);
  },

  getAIUsage: async (provider?: string): Promise<AILog[]> => {
    const query = provider ? `?provider=${encodeURIComponent(provider)}` : '';
    return fetchWithCache(`admin_ai_usage_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/ai-usage${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<AILog>(res);
    }, 15000);
  },

  getAIEvaluation: async (): Promise<AIEvaluation> => {
    return fetchWithCache('admin_ai_eval', async () => {
      const res = await fetch('/api/v1/admin/ai-evaluation', {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleObjectResponse<AIEvaluation>(res);
    }, 15000);
  },

  getJobs: async (status?: string): Promise<BackgroundJob[]> => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return fetchWithCache(`admin_jobs_${query}`, async () => {
      const res = await fetch(`/api/v1/admin/jobs${query}`, {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleArrayResponse<BackgroundJob>(res);
    }, 15000);
  },

  getSystemHealth: async (): Promise<SystemHealth> => {
    return fetchWithCache('admin_system_health', async () => {
      const res = await fetch('/api/v1/admin/system-health', {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleObjectResponse<SystemHealth>(res);
    }, 15000);
  },

  getGlobalAnalytics: async (): Promise<GlobalAnalytics> => {
    return fetchWithCache('admin_global_analytics', async () => {
      const res = await fetch('/api/v1/analytics/global', {
        headers: { ...authService.getAuthHeaders() },
      });
      return handleObjectResponse<GlobalAnalytics>(res);
    }, 15000);
  },
};


