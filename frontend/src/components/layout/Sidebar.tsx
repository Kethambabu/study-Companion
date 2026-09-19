import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Boxes,
  FolderKanban,
  FileText,
  Bot,
  BrainCircuit,
  TrendingUp,
  BarChart3,
  Settings,
  Layers,
} from "lucide-react";

const navigationItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Spaces", href: "/spaces", icon: Boxes },
  { name: "Projects", href: "/projects", icon: FolderKanban },
  { name: "Materials", href: "/materials", icon: FileText },
  { name: "AI Tutor", href: "/tutor", icon: Bot },
  { name: "Assessment", href: "/assessment", icon: BrainCircuit },
  { name: "Mastery", href: "/mastery", icon: Layers },
  { name: "Growth", href: "/growth", icon: TrendingUp },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {

  return (
    <aside className="w-64 border-r border-border glass-panel flex flex-col justify-between py-6 px-4 hidden md:flex">
      <div className="space-y-6">
        <div className="px-3">
          <p className="text-[11px] font-semibold tracking-wider uppercase text-muted-foreground">
            Learning Loop Navigation
          </p>
        </div>

        <nav className="space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                end={item.href === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>


      </div>

      <div className="px-3 py-4 glass-card rounded-xl text-xs space-y-2">
        <div className="flex items-center justify-between text-muted-foreground">
          <span>System Status</span>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>
        <p className="font-medium text-foreground">Backend Connected</p>
        <p className="text-[10px] text-muted-foreground">v0.1.0 Modular Monolith</p>
      </div>
    </aside>
  );
};
