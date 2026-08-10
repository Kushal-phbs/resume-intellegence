import { useState, useRef, useEffect } from "react";
import { LogOut, Settings, User, ChevronDown, Sun, Moon, Monitor } from "lucide-react";
import { Link } from "react-router-dom";
import { useLogout } from "@/hooks/useAuth";
import { useThemeStore } from "@/store/themeStore";
import { ROUTES } from "@/constants/routes";
import type { CurrentUserResponse } from "@/types/auth";

export function UserDropdown({ user }: { user: CurrentUserResponse }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const logout = useLogout();
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const themes: { value: "light" | "dark" | "system"; icon: typeof Sun; label: string }[] = [
    { value: "light", icon: Sun, label: "Light" },
    { value: "dark", icon: Moon, label: "Dark" },
    { value: "system", icon: Monitor, label: "System" },
  ];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full bg-muted px-2 py-1 transition-colors hover:bg-muted/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        aria-label="User menu"
        aria-expanded={open}
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[11px] font-bold text-primary-foreground">
          {initials}
        </div>
        <span className="hidden text-sm font-semibold md:block">{user.full_name.split(" ")[0]}</span>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-lg border border-border bg-card shadow-lg">
          {/* User info */}
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-semibold">{user.full_name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>

          {/* Navigation */}
          <div className="py-1">
            <Link
              to={ROUTES.profile}
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-muted"
            >
              <User className="h-4 w-4 text-muted-foreground" />
              Profile
            </Link>
            <Link
              to={ROUTES.settings}
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-4 py-2 text-sm text-foreground hover:bg-muted"
            >
              <Settings className="h-4 w-4 text-muted-foreground" />
              Settings
            </Link>
          </div>

          {/* Theme switcher */}
          <div className="border-t border-border px-4 py-2">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Theme
            </p>
            <div className="flex gap-1">
              {themes.map(({ value, icon: Icon, label }) => (
                <button
                  key={value}
                  onClick={() => { setTheme(value); setOpen(false); }}
                  className={`flex flex-1 flex-col items-center gap-0.5 rounded-md py-1.5 text-[10px] font-medium transition-colors ${
                    theme === value
                      ? "bg-primary/15 text-primary"
                      : "text-muted-foreground hover:bg-muted"
                  }`}
                  aria-label={label}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Logout */}
          <div className="border-t border-border py-1">
            <button
              onClick={() => { logout(); setOpen(false); }}
              className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-destructive hover:bg-destructive/10"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
