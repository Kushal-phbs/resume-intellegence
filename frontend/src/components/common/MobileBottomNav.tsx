import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, FileText, Brain, MessageSquare, Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

const TABS = [
  { label: "Home", icon: LayoutDashboard, to: ROUTES.dashboard, end: true },
  { label: "Resumes", icon: FileText, to: ROUTES.resumes },
  { label: "Studio", icon: Brain, to: ROUTES.tailoring },
  { label: "Chat", icon: MessageSquare, to: ROUTES.chat },
  { label: "Settings", icon: Settings, to: ROUTES.settings },
];

/** Bottom tab bar visible only on mobile (<640px). */
export function MobileBottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex h-16 border-t border-border bg-card sm:hidden">
      {TABS.map(({ label, icon: Icon, to, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition-colors",
              isActive ? "text-primary" : "text-muted-foreground"
            )
          }
          aria-label={label}
        >
          <Icon className="h-5 w-5" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
