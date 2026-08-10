import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore, getStoredRefreshToken } from "@/store/authStore";
import { API_ROUTES } from "@/constants/routes";
import type { TokenResponse } from "@/types/auth";
import type { ApiErrorPayload } from "@/types/common";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// --- Request interceptor: attach Authorization header automatically ---
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Response interceptor: automatic refresh-on-401, then automatic logout ---
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) throw new Error("No refresh token available");

  // Use a bare axios call (not apiClient) to avoid recursive interceptors.
  const { data } = await axios.post<TokenResponse>(`${BASE_URL}${API_ROUTES.authRefresh}`, {
    refresh_token: refreshToken,
  });
  useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorPayload>) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    const isAuthEndpoint =
      originalRequest?.url?.includes(API_ROUTES.authLogin) ||
      originalRequest?.url?.includes(API_ROUTES.authRegister) ||
      originalRequest?.url?.includes(API_ROUTES.authRefresh);

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      try {
        refreshPromise = refreshPromise ?? refreshAccessToken();
        const newAccessToken = await refreshPromise;
        refreshPromise = null;
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshPromise = null;
        // Automatic logout: refresh token is invalid/expired too.
        useAuthStore.getState().clear();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/** Extract a human-readable message from any backend error response. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    if (payload?.detail) return payload.detail;
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}
