import { authService } from "./authService";
import { fetchWithCache, invalidateCache } from "./apiCache";
import { buildUrl, parseApiResponse } from "@/lib/apiClient";

export interface QuizQuestionPublicItem {
  id: string;
  question_type: "mcq" | "open_ended";
  question_text: string;
  options?: string[];
  concept_id: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  order_index: number;
}

export interface QuizItem {
  id: string;
  project_id: string;
  user_id: string;
  title: string;
  description?: string;
  target_concept_id?: string;
  questions: QuizQuestionPublicItem[];
  attempt?: QuizAttemptItem;
  created_at: string;
}

export interface QuizAttemptItem {
  id: string;
  quiz_id: string;
  project_id: string;
  user_id: string;
  status: "in_progress" | "completed";
  started_at: string;
  completed_at?: string;
  score: number;
  max_score: number;
  current_question_index: number;
  submitted_question_ids: string[];
}

export interface OpenEndedEvaluationItem {
  score_percentage: number;
  is_correct: boolean;
  understanding_level: "excellent" | "partial" | "poor";
  key_concepts_demonstrated: string[];
  missing_concepts: string[];
  reasoning_quality: string;
  feedback_what_was_understood: string;
  feedback_what_was_missing: string;
  feedback_how_to_improve: string;
}

export interface QuestionAttemptResultItem {
  id: string;
  attempt_id: string;
  question_id: string;
  user_answer: string;
  is_correct: boolean;
  score_percentage: number;
  explanation: string;
  correct_answer?: string;
  feedback: OpenEndedEvaluationItem | Record<string, unknown>;
  submitted_at: string;
}

export interface QuizSummaryItem {
  attempt_id: string;
  quiz_id: string;
  project_id: string;
  overall_score: number;
  max_score: number;
  score_percentage: number;
  status: string;
  completed_at?: string;
  concepts_tested: Record<string, number[]>;
  weak_concepts: string[];
  strong_concepts: string[];
  recommendations: string[];
  question_attempts: QuestionAttemptResultItem[];
}

export interface CreateQuizRequest {
  title?: string;
  target_concept_id?: string;
  num_questions?: number;
  difficulty_preference?: "adaptive" | "beginner" | "intermediate" | "advanced";
}

export interface LearningProgressItem {
  project_id: string;
  user_id: string;
  current_concept_id: string;
  current_position: number;
  total_concepts: number;
  completed_concepts: string[];
  all_concepts: string[];
  learning_status: string;
}

export const assessmentService = {
  createQuiz: async (projectId: string, req: CreateQuizRequest = {}): Promise<QuizItem> => {
    invalidateCache(`quizzes:${projectId}`);
    const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/quizzes`), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authService.getAuthHeaders(),
      },
      body: JSON.stringify(req),
    });
    const result = await parseApiResponse<QuizItem>(res, "Failed to create quiz session");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to create quiz session.");
    }
    return result.data;
  },

  listQuizzes: async (projectId: string): Promise<QuizItem[]> => {
    return fetchWithCache(`quizzes:${projectId}`, async () => {
      const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/quizzes`), {
        headers: { ...authService.getAuthHeaders() },
      });
      const result = await parseApiResponse<QuizItem[]>(res, "Failed to list quizzes");
      if (!result.success || !result.data) {
        throw new Error(result.error?.message || "Failed to list quizzes.");
      }
      return result.data;
    }, 15000);
  },

  startOrGetAttempt: async (
    projectId: string,
    quizId: string
  ): Promise<{ quiz: QuizItem; attempt: QuizAttemptItem }> => {
    const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/quizzes/${quizId}/attempts`), {
      method: "POST",
      headers: { ...authService.getAuthHeaders() },
    });
    const result = await parseApiResponse<{ quiz: QuizItem; attempt: QuizAttemptItem }>(res, "Failed to start or resume quiz attempt");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to start or resume quiz attempt.");
    }
    return result.data;
  },

  submitAnswer: async (
    projectId: string,
    quizId: string,
    attemptId: string,
    questionId: string,
    userAnswer: string
  ): Promise<QuestionAttemptResultItem> => {
    const res = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/quizzes/${quizId}/attempts/${attemptId}/questions/${questionId}/submit`),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authService.getAuthHeaders(),
        },
        body: JSON.stringify({ user_answer: userAnswer }),
      }
    );
    const result = await parseApiResponse<QuestionAttemptResultItem>(res, "Failed to submit question answer");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to submit question answer.");
    }
    return result.data;
  },

  finishAttempt: async (
    projectId: string,
    quizId: string,
    attemptId: string
  ): Promise<QuizSummaryItem> => {
    invalidateCache(`growth:${projectId}`);
    invalidateCache(`quizzes:${projectId}`);
    const res = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/quizzes/${quizId}/attempts/${attemptId}/finish`),
      {
        method: "POST",
        headers: { ...authService.getAuthHeaders() },
      }
    );
    const result = await parseApiResponse<QuizSummaryItem>(res, "Failed to finalize quiz attempt");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to finalize quiz attempt.");
    }
    return result.data;
  },

  getSummary: async (
    projectId: string,
    quizId: string,
    attemptId: string
  ): Promise<QuizSummaryItem> => {
    const res = await fetch(
      buildUrl(`/api/v1/projects/${projectId}/quizzes/${quizId}/attempts/${attemptId}/summary`),
      {
        headers: { ...authService.getAuthHeaders() },
      }
    );
    const result = await parseApiResponse<QuizSummaryItem>(res, "Failed to fetch quiz summary");
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to fetch quiz summary.");
    }
    return result.data;
  },

  getLearningProgress: async (projectId: string): Promise<LearningProgressItem> => {
    return fetchWithCache(`progress:${projectId}`, async () => {
      const res = await fetch(buildUrl(`/api/v1/projects/${projectId}/quizzes/learning-progress`), {
        headers: { ...authService.getAuthHeaders() },
      });
      const result = await parseApiResponse<LearningProgressItem>(res, "Failed to fetch learning progress");
      if (!result.success || !result.data) {
        throw new Error(result.error?.message || "Failed to fetch learning progress.");
      }
      return result.data;
    }, 15000);
  },
};

