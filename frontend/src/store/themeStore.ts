import { create } from "zustand";

type Theme = "dark" | "light" | "system";

interface ThemeState {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

function getSystemTheme(): "dark" | "light" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const resolved = theme === "system" ? getSystemTheme() : theme;
  root.classList.toggle("dark", resolved === "dark");
  localStorage.setItem("ri_theme", theme);
}

const stored = (localStorage.getItem("ri_theme") as Theme | null) ?? "dark";

export const useThemeStore = create<ThemeState>((set) => ({
  theme: stored,
  setTheme: (t) => {
    applyTheme(t);
    set({ theme: t });
  },
}));

// Apply on initial load
applyTheme(stored);
