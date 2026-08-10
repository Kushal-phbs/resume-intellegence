import { Menu, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { UserDropdown } from "./UserDropdown";
import { NotificationPanel } from "./NotificationPanel";
import { useCurrentUser } from "@/hooks/useAuth";
import { ROUTES } from "@/constants/routes";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { data: user } = useCurrentUser();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-card/70 px-4 backdrop-blur-md">
      {/* Mobile hamburger */}
      <button
        onClick={onMenuClick}
        aria-label="Open menu"
        className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-muted lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile logo (hidden on desktop — sidebar shows it) */}
      <Link
        to={ROUTES.dashboard}
        className="flex items-center gap-2 font-bold text-foreground lg:hidden"
      >
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm">Resume Intelligence</span>
      </Link>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right side */}
      <div className="flex items-center gap-1">
        <NotificationPanel />
        {user && <UserDropdown user={user} />}
      </div>
    </header>
  );
}
