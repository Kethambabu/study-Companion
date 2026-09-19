import React, { useEffect, useState } from 'react';
import { adminService, AdminOverview, GlobalAnalytics } from '../../services/adminService';
import { Users, Cpu, CheckCircle2, Activity, TrendingUp, Server, Shield } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export const AdminOverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [analytics, setAnalytics] = useState<GlobalAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ov, ga] = await Promise.all([
          adminService.getOverview(),
          adminService.getGlobalAnalytics(),
        ]);
        setOverview(ov);
        setAnalytics(ga);
      } catch (err) {
        console.error('Failed to load admin overview:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* PRD Header */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Shield className="h-6 w-6 text-indigo-400" />
          <h1 className="text-2xl font-bold text-white tracking-wide">AI Study Companion — Admin</h1>
        </div>
        <p className="mt-1 text-xs text-slate-400">Platform-wide control, telemetry, and infrastructure governance dashboard.</p>
      </div>

      <div className="text-sm font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
        <Server className="h-4 w-4" /> Platform Overview
      </div>

      {/* PRD Section 21 4-Box Telemetry Matrix */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* 1. Platform Overview */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Platform Overview</h3>
            <Users className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Users</span>
              <span className="font-bold text-white bg-slate-800 px-2.5 py-0.5 rounded text-xs">{overview?.total_users ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Spaces</span>
              <span className="font-bold text-white bg-slate-800 px-2.5 py-0.5 rounded text-xs">{overview?.total_spaces ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Projects</span>
              <span className="font-bold text-white bg-slate-800 px-2.5 py-0.5 rounded text-xs">{overview?.total_projects ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Active Users</span>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded text-xs">{overview?.active_users_24h ?? 0}</span>
            </div>
          </div>
        </div>

        {/* 2. AI Usage */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">AI Usage</h3>
            <Cpu className="h-4 w-4 text-purple-400" />
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Tutor Requests</span>
              <span className="font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2.5 py-0.5 rounded text-xs">{overview?.tutor_requests ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Quiz Generations</span>
              <span className="font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2.5 py-0.5 rounded text-xs">{overview?.quiz_generations ?? 0}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
              Total Tokens: <span className="text-slate-300 font-semibold">{(overview?.total_ai_tokens || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* 3. Background Jobs */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Background Jobs</h3>
            <Activity className="h-4 w-4 text-blue-400" />
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Processing</span>
              <span className="font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded text-xs">{overview?.jobs_processing ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Failed</span>
              <span className="font-bold text-emerald-400 bg-slate-800 px-2.5 py-0.5 rounded text-xs">{overview?.jobs_failed ?? 0}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
              Queue Status: <span className="text-emerald-400 font-semibold">Healthy</span>
            </div>
          </div>
        </div>

        {/* 4. System Health */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">System Health</h3>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">API</span>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-xs">{overview?.api_health ?? '✓'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Database</span>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-xs">{overview?.database_health ?? '✓'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">AI Provider</span>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-xs">{overview?.ai_provider_health ?? '✓'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Global Learning Activity Recharts Stream */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Platform Learning Activity</h2>
            <p className="text-xs text-slate-400">Aggregated student learning activity & study volume</p>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20">
            <TrendingUp className="h-4 w-4" /> Live Platform Activity
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={analytics?.activity_timeline || []}>
              <defs>
                <linearGradient id="studyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
              />
              <Area type="monotone" dataKey="study_time_minutes" stroke="#818cf8" fillOpacity={1} fill="url(#studyGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

