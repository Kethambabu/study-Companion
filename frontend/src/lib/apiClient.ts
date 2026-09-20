/// <reference types="vite/client" />
import { ApiResponse } from "@/types/api";

const metaEnv = (import.meta as unknown as { env?: Record<string, string> }).env || {};
const API_BASE_URL = (metaEnv.VITE_API_URL || metaEnv.VITE_API_BASE_URL || "").replace(/\/+$/, "");


export function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  let baseUrl = API_BASE_URL;
  if (!baseUrl && typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname.endsWith(".onrender.com") && !hostname.includes("study-companion-1-q4k8")) {
      baseUrl = "https://study-companion-1-q4k8.onrender.com";
    }
  }

  return baseUrl ? `${baseUrl}${cleanPath}` : cleanPath;
}


export async function parseApiResponse<T>(
  response: Response,
  fallbackError: string = "Request failed"
): Promise<ApiResponse<T>> {
  const text = await response.text();
  let result: any = null;

  if (text && text.trim().length > 0) {
    try {
      result = JSON.parse(text);
    } catch {
      // Non-JSON response (e.g. HTML 404/502 page)
      result = null;
    }
  }

  if (!response.ok) {
    const errorMsg =
      result?.error?.message ||
      result?.detail ||
      result?.message ||
      `${fallbackError} (HTTP ${response.status}${response.statusText ? `: ${response.statusText}` : ""})`;
    throw new Error(errorMsg);
  }

  if (result && typeof result === "object") {
    // Backend wraps responses as { success: true, data: ... }
    if ("success" in result && "data" in result) {
      return result as ApiResponse<T>;
    }
    // For endpoints that return raw objects (not wrapped)
    return {
      success: true,
      data: result as T,
    } as unknown as ApiResponse<T>;
  }

  throw new Error(`${fallbackError}: Server returned an empty or invalid response.`);
}

export async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
  fallbackError: string = "API request failed"
): Promise<ApiResponse<T>> {
  const url = buildUrl(path);
  try {
    const response = await fetch(url, options);
    return await parseApiResponse<T>(response, fallbackError);
  } catch (err) {
    if (err instanceof Error) {
      if (err.message === "Failed to fetch" || err.name === "TypeError") {
        throw new Error(
          `${fallbackError}: Unable to reach backend server. If using Render Free Tier, the backend service may be spinning up (allow 30-60s then click Try Again).`
        );
      }
      throw err;
    }
    throw new Error(`${fallbackError}: Network error or server unreachable.`);
  }
}

