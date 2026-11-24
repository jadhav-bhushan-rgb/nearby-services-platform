import { useAuthStore } from "@/store/auth";
import type {
  Admin,
  Bounds,
  BulkResult,
  CategoryId,
  MapResponse,
  NearbyResponse,
  Service,
  ServiceInput,
  ServicePage,
  StatsResponse,
  TokenResponse,
} from "@/lib/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/backend-api";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    useAuthStore.getState().clear();
    return null;
  }
  const data = (await response.json()) as TokenResponse;
  useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  form?: FormData;
  auth?: boolean;
  retry?: boolean;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers();
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.auth) {
    const token = useAuthStore.getState().accessToken;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? (options.body !== undefined || options.form ? "POST" : "GET"),
    headers,
    body: options.form ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
  });
  if (response.status === 204) return undefined as T;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const canRefresh = options.auth && options.retry !== false && !path.startsWith("/api/v1/auth/");
    if (response.status === 401 && canRefresh) {
      if (!refreshPromise) {
        refreshPromise = refreshAccess().finally(() => {
          refreshPromise = null;
        });
      }
      const nextToken = await refreshPromise;
      if (nextToken) return apiRequest<T>(path, { ...options, retry: false });
      useAuthStore.getState().clear();
    }
    throw new ApiError(payload?.error?.message || "Request failed", response.status, payload?.error?.code);
  }
  return payload as T;
}

function queryString(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  listServices(params: { category?: CategoryId | ""; q?: string; page?: number; page_size?: number }) {
    return apiRequest<ServicePage>(`/api/v1/services${queryString(params)}`);
  },
  mapServices(bounds: Bounds & { category?: CategoryId | ""; limit?: number }) {
    return apiRequest<MapResponse>(`/api/v1/services/map${queryString(bounds)}`);
  },
  nearby(params: {
    latitude: number;
    longitude: number;
    radius_km: number;
    category?: CategoryId | "";
    limit?: number;
  }) {
    return apiRequest<NearbyResponse>(`/api/v1/services/nearby${queryString(params)}`);
  },
  service(id: string, origin?: { latitude: number; longitude: number }) {
    return apiRequest<Service>(`/api/v1/services/${id}${queryString(origin ?? {})}`);
  },
  login(email: string, password: string) {
    return apiRequest<TokenResponse>("/api/v1/auth/login", { method: "POST", body: { email, password } });
  },
  me() {
    return apiRequest<Admin>("/api/v1/auth/me", { auth: true });
  },
  logout() {
    const refreshToken = useAuthStore.getState().refreshToken;
    return apiRequest<void>("/api/v1/auth/logout", {
      method: "POST",
      auth: true,
      retry: false,
      body: { refresh_token: refreshToken },
    });
  },
  stats() {
    return apiRequest<StatsResponse>("/api/v1/admin/stats", { auth: true });
  },
  adminServices(params: { category?: CategoryId | ""; q?: string; page?: number; page_size?: number }) {
    return apiRequest<ServicePage>(`/api/v1/admin/services${queryString(params)}`, { auth: true });
  },
  createService(body: ServiceInput) {
    return apiRequest<Service>("/api/v1/admin/services", { method: "POST", auth: true, body });
  },
  updateService(id: string, body: Partial<ServiceInput>) {
    return apiRequest<Service>(`/api/v1/admin/services/${id}`, { method: "PUT", auth: true, body });
  },
  deleteService(id: string) {
    return apiRequest<void>(`/api/v1/admin/services/${id}`, { method: "DELETE", auth: true });
  },
  bulkUpload(file: File) {
    const form = new FormData();
    form.set("file", file);
    return apiRequest<BulkResult>("/api/v1/admin/services/bulk", { method: "POST", auth: true, form });
  },
};
