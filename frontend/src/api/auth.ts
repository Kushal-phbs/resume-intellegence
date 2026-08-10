import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type {
  LoginRequest,
  RegisterRequest,
  RefreshTokenRequest,
  TokenResponse,
  CurrentUserResponse,
} from "@/types/auth";

export const authApi = {
  register: (payload: RegisterRequest) =>
    apiClient.post<TokenResponse>(API_ROUTES.authRegister, payload).then((r) => r.data),

  login: (payload: LoginRequest) =>
    apiClient.post<TokenResponse>(API_ROUTES.authLogin, payload).then((r) => r.data),

  refresh: (payload: RefreshTokenRequest) =>
    apiClient.post<TokenResponse>(API_ROUTES.authRefresh, payload).then((r) => r.data),

  me: () => apiClient.get<CurrentUserResponse>(API_ROUTES.usersMe).then((r) => r.data),

  // NOTE: the backend has no /auth/logout endpoint — logout is purely a
  // client-side action (discard tokens). See useAuth.ts.
};
