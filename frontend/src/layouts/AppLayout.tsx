import { useState } from "react";
import { Outlet } from "react-router-dom";
import { motion } from "framer-motion";
import { DesktopSidebar, MobileSidebar } from "@/components/common/Sidebar";
import { TopBar } from "@/components/common/TopBar";
import { MobileBottomNav } from "@/components/common/MobileBottomNav";

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Skip to content — keyboard / screen reader accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[200] focus:rounded-md focus:bg-primary focus:px-3 focus:py-1.5 focus:text-sm focus:font-semibold focus:text-primary-foreground"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <DesktopSidebar />

      {/* Mobile sidebar drawer */}
      <MobileSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main column */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />

        <motion.main
          id="main-content"
          key={location.pathname}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className="flex-1 overflow-y-auto pb-16 sm:pb-0"
        >
          <div className="mx-auto max-w-[1440px] p-6">
            <Outlet />
          </div>
        </motion.main>

        <MobileBottomNav />
      </div>
    </div>
  );
}
