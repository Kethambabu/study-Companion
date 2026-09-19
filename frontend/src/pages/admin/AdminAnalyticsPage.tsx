import React, { useEffect, useState } from 'react';
import { adminService, GlobalAnalytics } from '../../services/adminService';
import { LineChart, BarChart2, BookOpen, Brain, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts';

export const AdminAnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<GlobalAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const ga = await adminService.getGlobalAnalytics();
        setAnalytics(ga);
      } catch (err) {
        console.error('Failed to load global admin analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
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
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2 text-indigo-400">
          <LineChart className="h-6 w-6" />
          <h1 className="text-2xl font-bold text-white">Platform Analytics</h1>
        </div>
        <p className="text-xs text-slate-400">Global learning telemetry, concept mastery distributions, and project activity metrics.</p>
      </div>

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Total Tutor Interactions</span>
            <Brain className="h-4 w-4 text-purple-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-white">{analytics?.total_tutor_messages ?? 0}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Quiz Attempts Completed</span>
            <Activity className="h-4 w-4 text-blue-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-white">{analytics?.total_quizzes ?? 0}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Avg Concept Mastery</span>
            <BarChart2 className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-400">{Math.round((analytics?.avg_concept_mastery ?? 0) * 100)}%</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>Active Learning Projects</span>
            <BookOpen className="h-4 w-4 text-indigo-400" />
          </div>
          <p className="mt-2 text-2xl font-bold text-white">{analytics?.total_projects ?? 0}</p>
        </div>
      </div>

      {/* Recharts Activity Timeline & Project Engagement */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white mb-4">7-Day Study Volume Trend</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics?.activity_timeline || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff' }} />
                <Area type="monotone" dataKey="study_time_minutes" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white mb-4">Top Active Student Projects</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.top_active_projects || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="title" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff' }} />
                <Bar dataKey="activity_count" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
