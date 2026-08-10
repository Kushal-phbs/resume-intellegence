import { useEffect } from "react";
import { useThemeStore } from "@/store/themeStore";

/** Applies the persisted theme class to <html> on every render cycle and
 *  re-applies when the OS preference changes (for "system" theme). */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (theme === "system") setTheme("system"); // re-triggers applyTheme
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme, setTheme]);

  return <>{children}</>;
}
