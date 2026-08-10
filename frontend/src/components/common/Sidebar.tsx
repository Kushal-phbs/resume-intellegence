import { NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, FileText, Brain, Briefcase,
  MessageSquare, Settings, User, ChevronRight, Sparkles, X,
} from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { cn } from "@/lib/utils";

export interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, to: ROUTES.dashboard, end: true },
  { label: "Resumes", icon: FileText, to: ROUTES.resumes },
  { label: "AI Studio", icon: Brain, to: ROUTES.tailoring },
  { label: "Job Analysis", icon: Briefcase, to: ROUTES.jobAnalysis },
  { label: "Chat", icon: MessageSquare, to: ROUTES.chat },
];

const ACCOUNT_ITEMS = [
  { label: "Profile", icon: User, to: ROUTES.profile },
  { label: "Settings", icon: Settings, to: ROUTES.settings },
];

function NavItem({ label, icon: Icon, to, end, onClick }: {
  label: string; icon: typeof LayoutDashboard; to: string; end?: boolean; onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          "group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-all",
          "border-l-2 border-transparent",
          isActive
            ? "border-l-primary bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-muted hover:text-foreground hover:translate-x-0.5"
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{label}</span>
      <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-40" />
    </NavLink>
  );
}

function SidebarContent({ onClose }: { onClose?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-1 overflow-y-auto p-4">
      {/* Logo */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-foreground">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm">Resume Intelligence <span className="text-muted-foreground font-normal">OS</span></span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Main nav */}
      <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        Workspace
      </p>
      {NAV_ITEMS.map((item) => (
        <NavItem key={item.to + item.label} {...item} onClick={onClose} />
      ))}

      {/* Account nav */}
      <p className="mb-1 mt-4 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        Account
      </p>
      {ACCOUNT_ITEMS.map((item) => (
        <NavItem key={item.to + item.label} {...item} onClick={onClose} />
      ))}
    </div>
  );
}

/** Desktop sidebar: always visible ≥1024px */
export function DesktopSidebar() {
  return (
    <aside className="hidden w-[248px] shrink-0 border-r border-border bg-card lg:block">
      <SidebarContent />
    </aside>
  );
}

/** Mobile sidebar: drawer overlay, animated */
export function MobileSidebar({ open, onClose }: SidebarProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={onClose}
            aria-hidden
          />
          {/* Drawer */}
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            className="fixed left-0 top-0 z-50 h-full w-[248px] border-r border-border bg-card lg:hidden"
          >
            <SidebarContent onClose={onClose} />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
