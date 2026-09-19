import { authService } from "./authService";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";

export interface ConversationItem {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessageItem {
  id: string;
  conversation_id: string;
  sender: "user" | "assistant" | "system" | "tool";
  content: string;
  citations?: Array<{
    citation_id: string;
    excerpt: string;
    material_name?: string;
    page_number?: number;
  }> | null;
  metadata_json?: {
    confidence_status?: string;
    suggested_followups?: string[];
    model?: string;
    provider?: string;
    latency_ms?: number;
  } | null;
  created_at: string;
}

export interface PaginatedMessages {
  items: ConversationMessageItem[];
  total: number;
  page: number;
  limit: number;
}

export interface TutorChatResult {
  conversation_id: string;
  message_id: string;
  answer: string;
  citations: Array<{
    citation_id: string;
    excerpt: string;
    material_name?: string;
    page_number?: number;
  }>;
  confidence_status: string;
  suggested_followups: string[];
  response_metadata: {
    model: string;
    provider: string;
    latency_ms: number;
    tokens_used: number;
    request_id: string;
  };
}

export const tutorService = {
  async createConversation(projectId: string, title?: string): Promise<ConversationItem> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/tutor/conversations`), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify({ title }),
    });

    const result = await parseApiResponse<ConversationItem>(response, "Failed to create conversation");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to create conversation.");
    }
    return result.data;
  },

  async listConversations(projectId: string): Promise<ConversationItem[]> {
    const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/tutor/conversations`), {
      headers: { ...authService.getAuthHeaders() },
    });

    const result = await parseApiResponse<ConversationItem[]>(response, "Failed to list conversations");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to list conversations.");
    }
    return result.data;
  },

  async getMessages(
    projectId: string,
    conversationId: string,
    page = 1,
    limit = 50
  ): Promise<PaginatedMessages> {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    const response = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/tutor/conversations/${conversationId}/messages?${params.toString()}`),
      {
        headers: { ...authService.getAuthHeaders() },
      }
    );

    const result = await parseApiResponse<PaginatedMessages>(response, "Failed to fetch conversation messages");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch conversation messages.");
    }
    return result.data;
  },

  async sendMessage(
    projectId: string,
    conversationId: string,
    content: string,
    mode: "default" | "explain_simpler" | "give_example" | "test_me" = "default"
  ): Promise<TutorChatResult> {
    const response = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/tutor/conversations/${conversationId}/messages`),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authService.getAuthHeaders(),
        },
        body: JSON.stringify({ content, mode }),
      }
    );

    const result = await parseApiResponse<TutorChatResult>(response, "Failed to send message to AI Tutor");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to send message to AI Tutor.");
    }
    return result.data;
  },

  async getLearningContext(projectId: string): Promise<string> {
    try {
      const response = await fetch(buildUrl(`/api/v1/projects/${projectId}/tutor/learning-context`), {
        headers: { ...authService.getAuthHeaders() },
      });
      const result = await parseApiResponse<{ learning_context: string }>(response, "Failed to fetch learning context");
      if (!result.success || !result.data) {
        return "Learner Context: Target mastery goals and active course practice.";
      }
      return result.data.learning_context;
    } catch {
      return "Learner Context: Target mastery goals and active course practice.";
    }
  },

  async streamMessage(
    projectId: string,
    conversationId: string,
    content: string,
    mode: "default" | "explain_simpler" | "give_example" | "test_me" = "default",
    onMetadata: (metadata: Record<string, unknown>) => void,
    onToken: (token: string) => void,
    onComplete: () => void
  ): Promise<void> {
    const response = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/tutor/conversations/${conversationId}/stream`),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authService.getAuthHeaders(),
        },
        body: JSON.stringify({ content, mode }),
      }
    );

    if (!response.ok || !response.body) {
      throw new Error("Failed to initialize SSE streaming connection with AI Tutor.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ") || trimmed.startsWith("data:")) {
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === "metadata") {
              onMetadata(data);
            } else if (data.type === "token" && data.content) {
              onToken(data.content);
            } else if (data.type === "completed" || data.status === "completed") {
              onComplete();
            }
          } catch {
            // Ignore partial SSE JSON chunks
          }
        }
      }
    }
    onComplete();
  },
};

