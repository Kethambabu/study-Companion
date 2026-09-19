import React from "react";
import { Sparkles, LogOut, User, Shield } from "lucide-react";
import { useAuth } from "@/context/useAuth";

export const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border glass-panel px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 text-primary rounded-lg border border-primary/20">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-foreground">AI Study Companion</h1>
          <p className="text-xs text-muted-foreground">SaaS Learning Workspace</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {(user?.role === "admin" || user?.is_admin) && (
          <a
            href="/admin"
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 px-3 py-1.5 text-xs font-bold text-indigo-300 border border-indigo-500/30 transition-all shadow-xs"
          >
            <Shield className="h-3.5 w-3.5 text-indigo-400" />
            <span>Admin Console</span>
          </a>
        )}

        <div className="flex items-center gap-3 pl-3">
          <div className="h-8 w-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-medium text-xs">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-medium text-foreground">{user?.full_name || "Authenticated User"}</p>
            <p className="text-[10px] text-muted-foreground">{user?.email}</p>
          </div>
        </div>

        <button
          onClick={logout}
          title="Log out"
          aria-label="Log out"
          className="p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors flex items-center gap-1.5 text-xs font-medium"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
};
