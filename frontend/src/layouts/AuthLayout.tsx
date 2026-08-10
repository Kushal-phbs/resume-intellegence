import { Outlet } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-12">
      {/* Brand mark */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="mb-8 flex items-center gap-2 text-xl font-bold text-foreground"
      >
        <Sparkles className="h-5 w-5 text-primary" />
        Resume Intelligence
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.05 }}
        className="w-full max-w-md"
      >
        <Outlet />
      </motion.div>
    </div>
  );
}
