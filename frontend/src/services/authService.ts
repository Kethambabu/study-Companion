import { ApiResponse, HealthStatus } from "@/types/api";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role?: string;
  is_admin?: boolean;
}

export interface TokenResponseData {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

const TOKEN_KEY = "ai_study_companion_token";

export const authService = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  },

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  async login(email: string, password: string): Promise<TokenResponseData> {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const result: ApiResponse<TokenResponseData> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Failed to authenticate.");
    }

    this.setToken(result.data.access_token);
    return result.data;
  },

  async signup(email: string, password: string, fullName: string): Promise<TokenResponseData> {
    const response = await fetch("/api/v1/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    const result: ApiResponse<TokenResponseData> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Registration failed.");
    }

    this.setToken(result.data.access_token);
    return result.data;
  },

  async getMe(): Promise<UserProfile> {
    const token = this.getToken();
    if (!token) {
      throw new Error("No token stored.");
    }

    const response = await fetch("/api/v1/auth/me", {
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
    });

    const result: ApiResponse<UserProfile> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      this.clearToken();
      throw new Error(result.error?.message || "Session expired.");
    }

    return result.data;
  },

  async logout(): Promise<void> {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...this.getAuthHeaders(),
        },
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      this.clearToken();
    }
  },

  async fetchHealth(): Promise<HealthStatus> {
    const response = await fetch("/api/v1/health");
    const result: ApiResponse<HealthStatus> = await response.json();
    if (!response.ok || !result.success || !result.data) {
      throw new Error(result.error?.message || "Health check failed");
    }
    return result.data;
  },
};
