import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/useAuth";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { spacesService, SpaceItem } from "@/services/spacesService";
import { projectsService, ProjectItem } from "@/services/projectsService";
import { analyticsService, StudentGlobalAnalyticsData } from "@/services/analyticsService";
import { CreateSpaceModal } from "@/components/spaces/CreateSpaceModal";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import {
  Layers,
  FolderKanban,
  Plus,
  ArrowRight,
  Sparkles,
  BookOpen,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
} from "lucide-react";

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [spaces, setSpaces] = useState<SpaceItem[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [analytics, setAnalytics] = useState<StudentGlobalAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateSpaceOpen, setIsCreateSpaceOpen] = useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);

  const loadDashboardData = async () => {
    setError(null);
    try {
      const [spacesRes, projectsRes] = await Promise.all([
        spacesService.listSpaces(),
        projectsService.listProjects(),
      ]);
      setSpaces(spacesRes.items || []);
      setProjects(projectsRes.items || []);
      setLoading(false);

      // Non-blocking background fetch for analytics telemetry
      analyticsService
        .getStudentGlobalAnalytics()
        .then((analyticsRes) => setAnalytics(analyticsRes))
        .catch(() => setAnalytics(null));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data.");
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  if (loading && spaces.length === 0 && projects.length === 0) {
    return <LoadingState message="Loading your personalized learning dashboard..." />;
  }

  if (error) {
    return <ErrorState title="Dashboard Error" message={error} onRetry={loadDashboardData} />;
  }

  // Determine active project for Continue Learning card
  const activeProject = projects.length > 0 ? projects[0] : null;
  const overallMasteryPct = analytics?.overall_mastery_pct || 0;
  const weakAreas = analytics?.areas_to_improve || [];

  return (
    <div className="space-y-8 pb-10">
      {/* Top Banner / Welcome Greeting */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-400 mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI STUDY COMPANION</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-100">
            {getGreeting()}, {user?.full_name || "Student"}
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Welcome back to your isolated learning workspace. Here is your current progress and next steps.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setIsCreateSpaceOpen(true)}
            className="px-4 py-2 text-sm font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition flex items-center space-x-2"
          >
            <Plus className="w-4 h-4 text-indigo-400" />
            <span>+ Create Space</span>
          </button>
          <button
            onClick={() => setIsCreateProjectOpen(true)}
            className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>+ Create Project</span>
          </button>
        </div>
      </div>

      {/* Main Student Home Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 1: Continue Learning */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-indigo-950/20 shadow-xl flex flex-col justify-between space-y-4 relative overflow-hidden">
          <div className="absolute -right-8 -top-8 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-indigo-400" />
                Continue Learning
              </span>
              <span className="text-[10px] font-medium bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/20">
                {activeProject ? "Active Project" : "No Active Session"}
              </span>
            </div>

            {activeProject ? (
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-100">{activeProject.name}</h3>
                  <span className="text-xs font-semibold text-indigo-400">{overallMasteryPct}%</span>
                </div>

                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full transition-all duration-700" style={{ width: `${Math.min(100, Math.max(0, overallMasteryPct))}%` }} />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                  <span>Goal: {activeProject.learning_goal || activeProject.description || "Active learning workspace"}</span>
                </div>
              </div>
            ) : (
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-center space-y-2">
                <p className="text-xs text-slate-400">No active project session started yet.</p>
              </div>
            )}
          </div>

          <div>
            {activeProject ? (
              <button
                onClick={() => navigate(`/projects/${activeProject.id}`)}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-1.5"
              >
                <span>Continue Learning</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => setIsCreateProjectOpen(true)}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-1.5"
              >
                <span>Create First Project</span>
                <Plus className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Card 2 & 3 Column: Overall Progress & Areas Requiring Attention */}
        <div className="space-y-6">
          {/* Overall Progress */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Overall Progress
              </span>
              <span className="text-xl font-extrabold text-emerald-400">{overallMasteryPct}%</span>
            </div>

            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 via-emerald-400 to-emerald-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.min(100, Math.max(0, overallMasteryPct))}%` }}
              />
            </div>
            <p className="text-[11px] text-slate-400">Mastery score aggregated across your active study spaces.</p>
          </div>

          {/* Areas Requiring Attention */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Areas Requiring Attention
            </span>

            {weakAreas.length === 0 ? (
              <p className="text-xs text-slate-400 italic pt-1">
                No weak concepts identified yet. Complete quizzes to identify areas for focus.
              </p>
            ) : (
              <ul className="space-y-2 text-xs text-slate-300 pt-1">
                {weakAreas.map((area, idx) => (
                  <li key={idx} className="flex items-center space-x-2 bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                    <span className="font-semibold text-slate-200">{area}</span>
                    <span className="text-[10px] text-amber-300 ml-auto font-mono">Requires Attention</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Card 4: Recommended Next Action */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-purple-950/20 shadow-xl flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
                <Lightbulb className="w-4 h-4 text-purple-400" />
                Recommended Next Action
              </span>
              <span className="text-[10px] font-semibold bg-purple-500/10 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/20">
                AI Recommendation
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
              <p className="text-sm font-semibold text-slate-100 leading-snug">
                {weakAreas.length > 0
                  ? `Review ${weakAreas[0]} and complete an assessment`
                  : activeProject
                  ? "Upload study materials or take an adaptive quiz session"
                  : "Create your first project to start learning"}
              </p>
              <p className="text-xs text-slate-400">
                {weakAreas.length > 0
                  ? `Target weak concepts in ${weakAreas[0]} to improve overall concept mastery.`
                  : "Continuous assessment and study material exploration boosts learning retention."}
              </p>
            </div>
          </div>

          <button
            onClick={() => navigate(activeProject ? `/projects/${activeProject.id}` : "/projects")}
            className="w-full py-2.5 px-4 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-purple-600/20 flex items-center justify-center gap-1.5"
          >
            <span>Start Learning Action</span>
            <CheckCircle2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Section: Recent Projects */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-indigo-400" />
            <span>Recent Projects</span>
          </h2>
          <Link to="/projects" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            View All Projects <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {projects.length === 0 ? (
          <EmptyState
            icon={<FolderKanban className="w-8 h-8 text-slate-500" />}
            title="No Projects Yet"
            description="Create projects inside your study spaces to organize learning materials and quizzes."
            actionLabel="Create Project"
            onAction={() => setIsCreateProjectOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {projects.map((pj) => (
              <button
                key={pj.id}
                onClick={() => navigate(`/projects/${pj.id}`)}
                className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-800/60 transition text-left group flex flex-col justify-between space-y-3"
              >
                <div>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 rounded-md border border-indigo-500/20">
                    {pj.status}
                  </span>
                  <h3 className="text-sm font-bold text-slate-100 group-hover:text-indigo-400 transition mt-2 truncate">
                    {pj.name}
                  </h3>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                    {pj.learning_goal || pj.description || "Active learning project"}
                  </p>
                </div>
                <div className="text-[10px] font-medium text-indigo-400 flex items-center justify-between pt-2 border-t border-slate-800/60">
                  <span>Open Project</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Section: Spaces Overview */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            <span>My Spaces ({spaces.length})</span>
          </h2>
          <Link to="/spaces" className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
            Manage Spaces <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {spaces.length === 0 ? (
          <EmptyState
            icon={<Layers className="w-8 h-8 text-slate-500" />}
            title="No Spaces Found"
            description="Create your first broad learning space (e.g. Artificial Intelligence, Python, DBMS)."
            actionLabel="Create Space"
            onAction={() => setIsCreateSpaceOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {spaces.map((sp) => (
              <Link
                key={sp.id}
                to={`/spaces/${sp.id}`}
                className="glass-panel p-5 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-800/60 transition group flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{sp.visual_metadata?.icon || "🤖"}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-800 text-slate-300 rounded-md border border-slate-700">
                      {sp.slug}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-100 group-hover:text-emerald-400 transition">
                    {sp.name}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2">
                    {sp.description || "Learning space container."}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-500">
                  <span>Role: {sp.role}</span>
                  <span className="text-emerald-400 font-semibold group-hover:translate-x-1 transition">
                    Open Space &rarr;
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <CreateSpaceModal
        isOpen={isCreateSpaceOpen}
        onClose={() => setIsCreateSpaceOpen(false)}
        onSuccess={loadDashboardData}
      />

      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onSuccess={loadDashboardData}
      />
    </div>
  );
};
