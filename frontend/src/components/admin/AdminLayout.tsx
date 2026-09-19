import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/useAuth';
import {
  LayoutDashboard,
  Users,
  Layers,
  FolderKanban,
  Activity,
  LineChart,
  Cpu,
  ShieldCheck,
  Briefcase,
  HeartPulse,
  LogOut,
} from 'lucide-react';

const ADMIN_NAV = [
  { name: 'Dashboard', path: '/admin', icon: LayoutDashboard, exact: true },
  { name: 'Users', path: '/admin/users', icon: Users },
  { name: 'Spaces', path: '/admin/spaces', icon: Layers },
  { name: 'Projects', path: '/admin/projects', icon: FolderKanban },
  { name: 'Activity', path: '/admin/activity', icon: Activity },
  { name: 'Analytics', path: '/admin/analytics', icon: LineChart },
  { name: 'AI Usage', path: '/admin/ai-usage', icon: Cpu },
  { name: 'AI Evaluation', path: '/admin/ai-evaluation', icon: ShieldCheck },
  { name: 'Jobs', path: '/admin/jobs', icon: Briefcase },
  { name: 'System Health', path: '/admin/system-health', icon: HeartPulse },
];

export const AdminLayout: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Admin Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md flex flex-col justify-between">
        <div>
          <div className="mb-6 flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-wide text-white">ADMIN CONSOLE</h2>
              <p className="text-xs text-slate-400">System & Governance</p>
            </div>
          </div>

          <nav className="space-y-1">
            {ADMIN_NAV.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                className={({ isActive }: { isActive: boolean }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`
                }
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="space-y-3">
          {user && (
            <div className="px-2 py-1 text-xs border-b border-slate-800 pb-2">
              <p className="font-semibold text-slate-200 truncate">{user.full_name || "Administrator"}</p>
              <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
            </div>
          )}

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 px-3 py-2.5 text-xs font-semibold text-red-400 border border-red-500/30 transition-all shadow-sm"
          >
            <LogOut className="h-4 w-4 text-red-400" />
            <span>Logout</span>
          </button>

          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-400">Server Authorization Active</p>
            <p className="mt-1">Strict role verification enforced on all admin endpoints.</p>
          </div>
        </div>
      </aside>

      {/* Admin Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};
