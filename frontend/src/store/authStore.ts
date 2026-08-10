import { create } from "zustand";
import type { CurrentUserResponse } from "@/types/auth";

const ACCESS_TOKEN_KEY = "ri_access_token";
const REFRESH_TOKEN_KEY = "ri_refresh_token";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: CurrentUserResponse | null;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: CurrentUserResponse | null) => void;
  clear: () => void;
}

/**
 * Token persistence: this is a real standalone Vite SPA (not an in-chat
 * artifact), so localStorage is the standard, appropriate place to persist
 * a refresh token between browser sessions — the backend returns tokens in
 * the JSON body rather than setting cookies, so the client is responsible
 * for storage.
 */
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
  refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  user: null,
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    set({ accessToken, refreshToken });
  },
  setUser: (user) => set({ user }),
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}
