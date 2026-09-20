import React, { useEffect, useState, useCallback } from "react";
import { LoadingState } from "@/components/ui/LoadingState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import {
  analyticsService,
  ProjectAnalyticsData,
  StudentGlobalAnalyticsData,
} from "@/services/analyticsService";
import {
  BarChart3,
  Bot,
  BrainCircuit,
  TrendingUp,
  AlertTriangle,
  Award,
  Globe,
  FolderKanban,
  CheckCircle2,
  Clock,
  Activity,
} from "lucide-react";

export const AnalyticsPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("global");
  const [viewMode, setViewMode] = useState<"global" | "project">("global");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [projectAnalytics, setProjectAnalytics] = useState<ProjectAnalyticsData | null>(null);
  const [studentGlobalAnalytics, setStudentGlobalAnalytics] = useState<StudentGlobalAnalyticsData | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      const list = await projectsService.listProjects();
      const items = list.items || [];
      setProjects(items);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load projects.";
      setError(msg);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      if (!studentGlobalAnalytics && !projectAnalytics) {
        setLoading(true);
      }
      setError(null);

      if (viewMode === "global" || selectedProjectId === "global") {
        const globalData = await analyticsService.getStudentGlobalAnalytics();
        setStudentGlobalAnalytics(globalData);
      } else {
        const projData = await analyticsService.getProjectAnalytics(selectedProjectId);
        setProjectAnalytics(projData);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load analytics data.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [viewMode, selectedProjectId]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading && projects.length === 0 && !studentGlobalAnalytics) {
    return <LoadingState message="Loading Student Analytics Engine..." />;
  }

  const activeProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header & View Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-indigo-400" />
            <span>{viewMode === "global" ? "My Learning Analytics" : `${activeProject?.name || "Project"} Analytics`}</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {viewMode === "global"
              ? "Section 19: Aggregated learning activity across all your Spaces & Projects."
              : "Section 18: Student-level project analytics, mastery trends & AI telemetry."}
          </p>
        </div>

        {/* View Switcher & Project Selector */}
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1">
            <button
              onClick={() => {
                setViewMode("global");
                setSelectedProjectId("global");
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                viewMode === "global"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>All Spaces (Global)</span>
            </button>

            <button
              onClick={() => {
                setViewMode("project");
                if (projects.length > 0 && selectedProjectId === "global") {
                  setSelectedProjectId(projects[0].id);
                }
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                viewMode === "project"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FolderKanban className="w-3.5 h-3.5" />
              <span>Project Specific</span>
            </button>
          </div>

          {viewMode === "project" && (
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SECTION 19: GLOBAL ANALYTICS FOR STUDENT (ALL SPACES) */}
      {viewMode === "global" && (
        <div className="space-y-6">
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="border-b border-slate-700/60 pb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Globe className="w-5 h-5 text-indigo-400" />
                <span>All Spaces</span>
              </h2>
              <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">
                Cross-Project Aggregation
              </span>
            </div>

            {/* Projects Summary Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Projects</span>
                <div className="text-3xl font-extrabold text-slate-100">
                  {studentGlobalAnalytics?.total_projects ?? 0}
                </div>
                <div className="text-[11px] text-slate-400 pt-1 flex justify-between">
                  <span>Completed: <strong className="text-emerald-400">{studentGlobalAnalytics?.completed_projects ?? 0}</strong></span>
                  <span>Active: <strong className="text-sky-400">{studentGlobalAnalytics?.active_projects ?? 0}</strong></span>
                </div>
              </div>

              <div className="p-5 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Overall Mastery</span>
                <div className="text-3xl font-extrabold text-emerald-400">
                  {studentGlobalAnalytics?.overall_mastery_pct ?? 0}%
                </div>
                <p className="text-[11px] text-slate-400 pt-1">Aggregated across all learning spaces</p>
              </div>

              <div className="p-5 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Learning Time</span>
                <div className="text-3xl font-extrabold text-indigo-400 flex items-center gap-2">
                  <Clock className="w-6 h-6 text-indigo-400" />
                  <span>{studentGlobalAnalytics?.learning_time_formatted || "0h 0m"}</span>
                </div>
                <p className="text-[11px] text-slate-400 pt-1">Total active study session duration</p>
              </div>
            </div>

            {/* Strongest Areas vs. Areas to Improve */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="p-5 bg-slate-900/90 rounded-2xl border border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Strongest Areas</span>
                </h3>
                {(!studentGlobalAnalytics?.strongest_areas || studentGlobalAnalytics.strongest_areas.length === 0) ? (
                  <p className="text-xs text-slate-400 italic">No strong areas identified yet. Achieve &ge;75% mastery on concepts.</p>
                ) : (
                  <ul className="space-y-2 text-xs font-medium text-slate-200">
                    {studentGlobalAnalytics.strongest_areas.map((area, idx) => (
                      <li key={idx} className="flex items-center gap-2 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                        <span className="text-emerald-400 font-bold">✓</span>
                        <span>{area}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="p-5 bg-slate-900/90 rounded-2xl border border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Areas to Improve</span>
                </h3>
                {(!studentGlobalAnalytics?.areas_to_improve || studentGlobalAnalytics.areas_to_improve.length === 0) ? (
                  <p className="text-xs text-slate-400 italic">No critical areas to improve identified yet.</p>
                ) : (
                  <ul className="space-y-2 text-xs font-medium text-slate-200">
                    {studentGlobalAnalytics.areas_to_improve.map((area, idx) => (
                      <li key={idx} className="flex items-center gap-2 bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                        <span className="text-rose-400 font-bold">⚠</span>
                        <span>{area}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Recent Global Activity Stream */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                <span>Recent Global Activity</span>
              </h3>
              {(!studentGlobalAnalytics?.recent_activity || studentGlobalAnalytics.recent_activity.length === 0) ? (
                <p className="text-xs text-slate-400 italic">No recent activity recorded yet.</p>
              ) : (
                <div className="space-y-2">
                  {studentGlobalAnalytics.recent_activity.map((act, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-3">
                        <span className="text-indigo-400 font-bold">•</span>
                        <div>
                          <p className="font-semibold text-slate-200">{act.title}</p>
                          <span className="text-[10px] text-slate-500 font-mono">{act.project_name}</span>
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">{new Date(act.timestamp).toLocaleDateString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SECTION 18: PROJECT-LEVEL ANALYTICS */}
      {viewMode === "project" && (
        <div className="space-y-6">
          {/* 1. Learning Activity Section */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm border-b border-slate-700/60 pb-3">
              <BrainCircuit className="w-4 h-4" />
              <span>Learning Activity</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold block">Tutor Questions</span>
                <div className="text-2xl font-extrabold text-indigo-400">
                  {projectAnalytics?.tutor_questions_count ?? 0}
                </div>
              </div>

              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold block">Quiz Attempts</span>
                <div className="text-2xl font-extrabold text-emerald-400">
                  {projectAnalytics?.quiz_attempts_count ?? 0}
                </div>
              </div>

              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold block">Questions Answered</span>
                <div className="text-2xl font-extrabold text-sky-400">
                  {projectAnalytics?.questions_answered_count ?? 0}
                </div>
              </div>

              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 font-semibold block">Assessments</span>
                <div className="text-2xl font-extrabold text-amber-400">
                  {projectAnalytics?.assessments_count ?? 0}
                </div>
              </div>
            </div>
          </div>

          {/* 2. Performance Section */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-sm border-b border-slate-700/60 pb-3">
              <Award className="w-4 h-4" />
              <span>Performance</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-semibold block">Quiz Accuracy</span>
                  <p className="text-xs text-slate-400 mt-0.5">Correct answer ratio across all quiz attempts</p>
                </div>
                <div className="text-3xl font-extrabold text-emerald-400">
                  {projectAnalytics?.quiz_accuracy_pct ?? 0}%
                </div>
              </div>

              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-semibold block">Assessment Average</span>
                  <p className="text-xs text-slate-400 mt-0.5">Average score on multi-dimensional open-ended evaluations</p>
                </div>
                <div className="text-3xl font-extrabold text-indigo-400">
                  {projectAnalytics?.assessment_average_score ?? 0}/10
                </div>
              </div>
            </div>
          </div>

          {/* 3. Mastery Trend Visualizer */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm border-b border-slate-700/60 pb-3">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Mastery Trend</span>
            </div>

            {!projectAnalytics?.mastery_trend_weeks || projectAnalytics.mastery_trend_weeks.length === 0 ? (
              <div className="p-6 bg-slate-950/90 rounded-xl border border-slate-800 text-center text-xs text-slate-400">
                No weekly mastery trend recorded yet for this project. Complete quizzes over time to view progression.
              </div>
            ) : (
              <div className="p-6 bg-slate-950/90 rounded-xl border border-slate-800 font-mono space-y-4">
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  {projectAnalytics.mastery_trend_weeks.map((w, idx) => (
                    <div key={idx} className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                      <p className="text-[10px] text-slate-400 font-sans font-semibold uppercase">{w.week}</p>
                      <p className="text-lg font-bold text-indigo-400 mt-1">{w.mastery}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 4. AI Activity Section */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 text-amber-400 font-bold text-sm border-b border-slate-700/60 pb-3">
              <Bot className="w-4 h-4" />
              <span>AI Activity</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-semibold block">Tutor Interactions</span>
                  <p className="text-xs text-slate-400 mt-0.5">Total grounded conversational exchanges</p>
                </div>
                <div className="text-3xl font-extrabold text-amber-400">
                  {projectAnalytics?.ai_tutor_interactions ?? 0}
                </div>
              </div>

              <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-semibold block">Average Response Time</span>
                  <p className="text-xs text-slate-400 mt-0.5">Sub-second retrieval & LLM generation latency</p>
                </div>
                <div className="text-3xl font-extrabold text-emerald-400 flex items-center space-x-1">
                  <span>{projectAnalytics?.ai_average_response_time_seconds ?? 0}s</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
