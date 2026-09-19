import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import { spacesService, SpaceItem } from "@/services/spacesService";
import { materialsService, MaterialItem } from "@/services/materialsService";
import { masteryService, GrowthSummaryItem } from "@/services/masteryService";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { KnowledgeExplorer } from "@/components/knowledge/KnowledgeExplorer";
import {
  FolderKanban,
  Target,
  FileText,
  BrainCircuit,
  HelpCircle,
  TrendingUp,
  Sparkles,
  Archive,
  ArrowLeft,
  Edit3,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Bot,
  BarChart2,
} from "lucide-react";

export const ProjectDashboardPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectItem | null>(null);
  const [space, setSpace] = useState<SpaceItem | null>(null);
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [growthSummary, setGrowthSummary] = useState<GrowthSummaryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<
    "dashboard" | "materials" | "knowledge" | "tutor" | "quiz" | "mastery" | "growth" | "analytics"
  >("dashboard");

  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [archiving, setArchiving] = useState(false);

  // Edit inline modal
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editGoal, setEditGoal] = useState("");
  const [updating, setUpdating] = useState(false);

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const [proj, matsRes, growthRes] = await Promise.all([
        projectsService.getProject(projectId),
        materialsService.listMaterials(projectId, undefined, 1, 50).catch(() => ({ items: [], total: 0, page: 1, limit: 50 })),
        masteryService.getGrowthSummary(projectId).catch(() => null),
      ]);
      setProject(proj);
      setEditName(proj.name);
      setEditDesc(proj.description || "");
      setEditGoal(proj.learning_goal || "");
      setMaterials(matsRes.items || []);
      setGrowthSummary(growthRes);

      try {
        const sp = await spacesService.getSpace(proj.space_id);
        setSpace(sp);
      } catch {
        // Soft fallback
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load project details.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !editName.trim()) return;
    try {
      setUpdating(true);
      const updated = await projectsService.updateProject(projectId, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
        learning_goal: editGoal.trim() || undefined,
      });
      setProject(updated);
      setIsEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update project.");
    } finally {
      setUpdating(false);
    }
  };

  const handleArchive = async () => {
    if (!projectId) return;
    try {
      setArchiving(true);
      await projectsService.archiveProject(projectId);
      navigate("/projects");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive project.");
    } finally {
      setArchiving(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading project workspace..." />;
  }

  if (error || !project) {
    return <ErrorState title="Project Error" message={error || "Project not found."} onRetry={loadData} />;
  }

  return (
    <div className="space-y-8 pb-10">
      {/* Navigation Breadcrumb */}
      <div className="flex items-center space-x-2 text-xs font-medium text-slate-400">
        <button
          onClick={() => navigate("/projects")}
          className="hover:text-slate-200 flex items-center space-x-1 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Projects</span>
        </button>
        {space && (
          <>
            <span>/</span>
            <Link to={`/spaces/${space.id}`} className="hover:text-indigo-400 font-mono flex items-center gap-1">
              <Layers className="w-3 h-3 text-indigo-400" />
              {space.name}
            </Link>
          </>
        )}
        <span>/</span>
        <span className="text-slate-200 font-semibold">{project.name}</span>
      </div>

      {/* Project Hero Header */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-emerald-950/20 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex items-center space-x-3">
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20 capitalize">
                {project.status}
              </span>
              <span className="text-xs text-slate-400">
                Created {new Date(project.created_at).toLocaleDateString()}
              </span>
            </div>

            {isEditing ? (
              <form onSubmit={handleUpdate} className="space-y-3 mt-2">
                <div>
                  <label className="text-xs font-semibold text-slate-400">Project Name</label>
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 font-bold text-xl"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400">Description</label>
                  <textarea
                    rows={2}
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-300 text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400">Learning Goal</label>
                  <textarea
                    rows={2}
                    value={editGoal}
                    onChange={(e) => setEditGoal(e.target.value)}
                    className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-300 text-sm"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={updating}
                    className="px-3 py-1 text-xs font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-500"
                  >
                    Save Changes
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-1 text-xs font-semibold text-slate-400 bg-slate-800 rounded-lg hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <div className="flex items-center space-x-3">
                  <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight flex items-center gap-3">
                    <FolderKanban className="w-7 h-7 text-emerald-400" />
                    <span>{project.name}</span>
                  </h1>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="text-slate-500 hover:text-emerald-400 p-1 transition"
                    title="Edit project details"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                  {project.description || "Active learning project workspace."}
                </p>

                <div className="mt-4 p-3.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex items-start space-x-3">
                  <Target className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                      Target Learning Goal
                    </p>
                    <p className="text-xs text-slate-200 mt-0.5 font-medium">
                      {project.learning_goal || "No specific learning goal defined for this project yet."}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => setIsArchiveOpen(true)}
              className="px-3 py-2 text-sm font-semibold text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl transition flex items-center space-x-2"
              title="Archive Project"
            >
              <Archive className="w-4 h-4" />
              <span>Archive</span>
            </button>
          </div>
        </div>
      </div>

      {/* Domain Navigation Bar (PRD Section 7) */}
      <div className="border-b border-slate-800 flex space-x-2 overflow-x-auto pb-1">
        {[
          { id: "dashboard", label: "Overview", icon: FolderKanban },
          { id: "materials", label: "Materials", icon: FileText },
          { id: "knowledge", label: "Knowledge", icon: BrainCircuit },
          { id: "tutor", label: "AI Tutor", icon: Bot },
          { id: "quiz", label: "Quiz", icon: HelpCircle },
          { id: "mastery", label: "Mastery", icon: Layers },
          { id: "growth", label: "Growth", icon: TrendingUp },
          { id: "analytics", label: "Analytics", icon: BarChart2 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold rounded-t-xl transition border-b-2 whitespace-nowrap ${
                isActive
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Tab Content */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          {/* PRD Section 7: Overall Progress & Concept Mastery */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Overall Progress Card */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  Overall Progress
                </span>
                <span className="text-2xl font-extrabold text-emerald-400">
                  {growthSummary ? `${Math.round(growthSummary.overall_mastery * 100)}%` : "0%"}
                </span>
              </div>

              <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${growthSummary ? Math.round(growthSummary.overall_mastery * 100) : 0}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">Overall project completion and concept retention score.</p>
            </div>

            {/* Concept Mastery Scores */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <BrainCircuit className="w-4 h-4 text-indigo-400" />
                Concept Mastery
              </span>

              {!growthSummary || (growthSummary.improving_concepts.length === 0 && growthSummary.stable_concepts.length === 0 && growthSummary.weak_concepts.length === 0) ? (
                <p className="text-xs text-slate-400 italic">
                  No concept mastery data available for this project yet. Complete a quiz to build concept scores.
                </p>
              ) : (
                <div className="space-y-3 text-xs">
                  {[...growthSummary.improving_concepts, ...growthSummary.stable_concepts, ...growthSummary.weak_concepts].map((item, idx) => {
                    const scorePct = Math.round((item.mastery_score || 0) * 100);
                    return (
                      <div key={idx}>
                        <div className="flex justify-between font-semibold text-slate-200 mb-1">
                          <span>{item.concept_id}</span>
                          <span className="text-emerald-400">{scorePct}%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${scorePct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Recent Activity & Attention Areas */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Activity */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Recent Activity
              </span>

              {materials.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No recent activity recorded for this project yet.</p>
              ) : (
                <ul className="space-y-2 text-xs">
                  {materials.slice(0, 4).map((m) => (
                    <li key={m.id} className="flex items-center space-x-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 text-slate-200">
                      <span className="text-emerald-400 font-bold">✓</span>
                      <span>Uploaded {m.filename}</span>
                      <span className="text-[10px] text-slate-500 ml-auto">{m.status.toUpperCase()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Areas Requiring Attention & Recommended Next Action */}
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Areas Requiring Attention
                </span>

                {!growthSummary || growthSummary.weak_concepts.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No critical attention areas identified.</p>
                ) : (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {growthSummary.weak_concepts.map((wc, idx) => (
                      <span key={idx} className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold rounded-lg">
                        ⚠ {wc.concept_id}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-purple-950/20 shadow-xl space-y-4">
                <span className="text-xs font-bold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
                  <Lightbulb className="w-4 h-4 text-purple-400" />
                  Recommended Next Action
                </span>

                <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs space-y-1">
                  <p className="font-semibold text-slate-100">
                    {growthSummary && growthSummary.weak_concepts.length > 0
                      ? `Review ${growthSummary.weak_concepts[0].concept_id} and complete an adaptive assessment.`
                      : materials.length > 0
                      ? "Explore your uploaded study materials or launch an AI Tutor session."
                      : "Upload PDF materials to extract knowledge and enable grounded Q&A."}
                  </p>
                </div>

                <button
                  onClick={() => navigate("/assessment")}
                  className="w-full py-2.5 px-4 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-purple-600/20 flex items-center justify-center gap-1.5"
                >
                  <span>Start Recommendation</span>
                  <Sparkles className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "materials" && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-100">Project Study Materials ({materials.length})</h3>
            <button
              onClick={() => navigate("/materials")}
              className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-xl"
            >
              Open Materials Manager
            </button>
          </div>
          {materials.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
              <FileText className="w-10 h-10 text-slate-500 mx-auto" />
              <p className="text-sm font-semibold text-slate-300">No Study Materials Uploaded Yet</p>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Upload course PDFs to extract knowledge chunks, enable vector search, and power the grounded AI Tutor.
              </p>
              <button
                onClick={() => navigate("/materials")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition"
              >
                Upload First PDF
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {materials.map((m) => (
                <div key={m.id} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex justify-between font-bold text-slate-100">
                    <span>📄 {m.filename}</span>
                    <span className={m.status === "ready" ? "text-emerald-400" : m.status === "failed" ? "text-rose-400" : "text-amber-400"}>
                      {m.status.toUpperCase()} {m.status === "ready" ? "✓" : "⏳"}
                    </span>
                  </div>
                  <p className="text-slate-400">
                    {m.page_count ? `${m.page_count} pages` : `${(m.file_size / 1024).toFixed(1)} KB`} &bull; Uploaded: {new Date(m.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "tutor" && (
        <div className="p-4 glass-panel rounded-2xl border border-slate-800 text-center space-y-4">
          <Bot className="w-12 h-12 text-indigo-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-100">AI Tutor Interface</h3>
          <p className="text-xs text-slate-400">Ask questions grounded in RAG Fundamentals materials.</p>
          <button
            onClick={() => navigate("/tutor")}
            className="px-5 py-2.5 bg-indigo-600 text-white text-xs font-bold rounded-xl"
          >
            Launch AI Tutor Workspace &rarr;
          </button>
        </div>
      )}

      {activeTab === "quiz" && (
        <div className="p-6 glass-panel rounded-2xl border border-slate-800 text-center space-y-3">
          <HelpCircle className="w-10 h-10 text-amber-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-100">Adaptive Quizzes</h3>
          <p className="text-xs text-slate-400">Test your recall on vector search and reranking concepts.</p>
          <button
            onClick={() => navigate("/assessment")}
            className="px-4 py-2 bg-amber-600 text-white text-xs font-bold rounded-xl"
          >
            Start Quiz Session
          </button>
        </div>
      )}

      {activeTab === "growth" && (
        <div className="p-6 glass-panel rounded-2xl border border-slate-800 text-center space-y-3">
          <TrendingUp className="w-10 h-10 text-emerald-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-100">Growth Engine</h3>
          <p className="text-xs text-slate-400">Track concept retention and learning trajectory.</p>
          <button
            onClick={() => navigate("/growth")}
            className="px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl"
          >
            View Growth Analytics
          </button>
        </div>
      )}

      {activeTab === "analytics" && (
        <div className="p-6 glass-panel rounded-2xl border border-slate-800 text-center space-y-3">
          <BarChart2 className="w-10 h-10 text-indigo-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-100">Analytics Domain</h3>
          <p className="text-xs text-slate-400">Deep-dive telemetry into token usage and study time.</p>
          <button
            onClick={() => navigate("/analytics")}
            className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-xl"
          >
            Open Analytics Dashboard
          </button>
        </div>
      )}

      {activeTab === "knowledge" && projectId && (
        <KnowledgeExplorer projectId={projectId} />
      )}

      <ConfirmDialog
        isOpen={isArchiveOpen}
        title="Archive Project"
        description={`Are you sure you want to archive project "${project.name}"?`}
        confirmLabel="Archive Project"
        isLoading={archiving}
        onConfirm={handleArchive}
        onClose={() => setIsArchiveOpen(false)}
      />
    </div>
  );
};
