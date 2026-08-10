import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import { queryKeys } from "@/constants/queryKeys";
import { ROUTES } from "@/constants/routes";
import type { LoginRequest, RegisterRequest } from "@/types/auth";

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.me,
    enabled: !!accessToken,
    staleTime: 5 * 60_000,
  });
}

export function useLogin() {
  const setTokens = useAuthStore((s) => s.setTokens);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LoginRequest) => authApi.login(payload),
    onSuccess: async (data) => {
      setTokens(data.access_token, data.refresh_token);
      await queryClient.invalidateQueries({ queryKey: queryKeys.me });
      navigate(ROUTES.dashboard);
    },
  });
}

export function useRegister() {
  const setTokens = useAuthStore((s) => s.setTokens);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RegisterRequest) => authApi.register(payload),
    onSuccess: async (data) => {
      setTokens(data.access_token, data.refresh_token);
      await queryClient.invalidateQueries({ queryKey: queryKeys.me });
      navigate(ROUTES.dashboard);
    },
  });
}

/** Backend has no /auth/logout — this just discards local tokens/cache. */
export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return () => {
    clear();
    queryClient.clear();
    navigate(ROUTES.login);
  };
}
