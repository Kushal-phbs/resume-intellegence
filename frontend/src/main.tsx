import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";
import { ThemeProvider } from "@/components/common/ThemeProvider";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { ToastContainer } from "@/components/common/Toast";
import { AppRouter } from "@/routes/index";
import "@/index.css";

// Ensure theme class is applied before first paint (themeStore import side-effect)
import "@/store/themeStore";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ErrorBoundary>
          <AppRouter />
          <ToastContainer />
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>
);
