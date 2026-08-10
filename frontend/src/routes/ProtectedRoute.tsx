import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants/routes";
import { GlobalLoader } from "@/components/common/GlobalLoader";
import { useCurrentUser } from "@/hooks/useAuth";

/**
 * Guards routes that require authentication.
 * - If no access token → redirect to /login
 * - While fetching /users/me for the first time → show GlobalLoader
 * - Once resolved → render children
 */
export function ProtectedRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  
  const { isLoading } = useCurrentUser();

  if (!accessToken) {
    return <Navigate to={ROUTES.login} replace />;
  }

  if (isLoading) return <GlobalLoader />;

  return <Outlet />;
}
