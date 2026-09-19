export interface ErrorDetail {
  field?: string;
  issue: string;
}

export interface ErrorBody {
  code: string;
  message: string;
  details?: ErrorDetail[];
}

export interface ResponseMeta {
  timestamp: string;
  request_id?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ErrorBody | null;
  meta: ResponseMeta;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
}
