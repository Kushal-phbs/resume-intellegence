import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { ROUTES } from "@/constants/routes";

/**
 * Guards public-only routes (login / register).
 * If the user is already authenticated, redirect to the dashboard.
 */
export function PublicRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken) return <Navigate to={ROUTES.dashboard} replace />;
  return <Outlet />;
}
