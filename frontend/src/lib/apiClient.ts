/// <reference types="vite/client" />
import { ApiResponse } from "@/types/api";

const metaEnv = (import.meta as unknown as { env?: Record<string, string> }).env || {};
const API_BASE_URL = (metaEnv.VITE_API_URL || metaEnv.VITE_API_BASE_URL || "").replace(/\/+$/, "");


export function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return API_BASE_URL ? `${API_BASE_URL}${cleanPath}` : cleanPath;
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
    return result as ApiResponse<T>;
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
      throw err;
    }
    throw new Error(`${fallbackError}: Network error or server unreachable.`);
  }
}
