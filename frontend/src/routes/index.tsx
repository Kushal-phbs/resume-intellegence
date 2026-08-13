import { GlobalLoader } from "@/components/common/GlobalLoader";
import { PageLoader } from "@/components/common/PageLoader";
import { ROUTES } from "@/constants/routes";
import { AppLayout } from "@/layouts/AppLayout";
import { AuthLayout } from "@/layouts/AuthLayout";
import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { PublicRoute } from "./PublicRoute";

// Lazy-loaded pages
const LoginPage = lazy(() => import("@/pages/auth/LoginPage").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/auth/RegisterPage").then((m) => ({ default: m.RegisterPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const ResumesPage = lazy(() => import("@/pages/resume/ResumesPage").then((m) => ({ default: m.ResumesPage })));
const ResumeDetailPage = lazy(() => import("@/pages/resume/ResumeDetailPage").then((m) => ({ default: m.ResumeDetailPage })));
const ResumeAnalysisPage = lazy(() => import("@/pages/analysis/ResumeAnalysisPage").then((m) => ({ default: m.ResumeAnalysisPage })));
const TailoringPage = lazy(() => import("@/pages/tailoring/TailoringPage").then((m) => ({ default: m.TailoringPage })));
const ChatPage = lazy(() => import("@/pages/chat/ChatPage").then((m) => ({ default: m.ChatPage })));
const ProfilePage = lazy(() => import("@/pages/profile/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const CareerInsightPage = lazy(() => import("@/pages/career/CareerInsightPage").then((m) => ({ default: m.CareerInsightPage })));
const SettingsPage = lazy(() => import("@/pages/settings/SettingsPage").then((m) => ({ default: m.SettingsPage })));
const JobAnalysisPage = lazy(() => import("@/pages/analysis/JobAnalysisPage").then((m) => ({ default: m.JobAnalysisPage })));
const JobAnalysisDetailPage = lazy(() => import("@/pages/analysis/JobAnalysisDetailPage").then((m) => ({ default: m.JobAnalysisDetailPage })));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));

const wrap = (el: React.ReactNode) => <Suspense fallback={<PageLoader />}>{el}</Suspense>;

const router = createBrowserRouter([
  // ── Public (auth) routes ─────────────────────────────────────────────
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: ROUTES.login, element: wrap(<LoginPage />) },
          { path: ROUTES.register, element: wrap(<RegisterPage />) },
        ],
      },
    ],
  },

  // ── Protected (app) routes ────────────────────────────────────────────
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: ROUTES.dashboard, element: wrap(<DashboardPage />) },
          { path: ROUTES.resumes, element: wrap(<ResumesPage />) },
          { path: "/resumes/:id", element: wrap(<ResumeDetailPage />) },
          { path: "/resumes/:id/analysis", element: wrap(<ResumeAnalysisPage />) },
          { path: ROUTES.tailoring, element: wrap(<TailoringPage />) },
          { path: ROUTES.jobAnalysis, element: wrap(<JobAnalysisPage />) },
          { path: "/job-analysis/:id", element: wrap(<JobAnalysisDetailPage />) },
          { path: ROUTES.chat, element: wrap(<ChatPage />) },
          { path: ROUTES.careerInsight, element: wrap(<CareerInsightPage />) },
          { path: ROUTES.profile, element: wrap(<ProfilePage />) },
          { path: ROUTES.settings, element: wrap(<SettingsPage />) },
        ],
      },
    ],
  },

  // ── 404 ──────────────────────────────────────────────────────────────
  { path: "*", element: wrap(<NotFoundPage />) },
]);

export function AppRouter() {
  return <RouterProvider router={router} fallbackElement={<GlobalLoader />} />;
}
