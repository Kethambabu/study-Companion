import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { spacesService, SpaceItem } from "@/services/spacesService";
import { projectsService, ProjectItem } from "@/services/projectsService";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { FolderKanban, Plus, Archive, ArrowLeft, Shield, Calendar, Edit3 } from "lucide-react";

export const SpaceDashboardPage: React.FC = () => {
  const { spaceId } = useParams<{ spaceId: string }>();
  const navigate = useNavigate();

  const [space, setSpace] = useState<SpaceItem | null>(null);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [archiving, setArchiving] = useState(false);

  // Edit Space Inline state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [updating, setUpdating] = useState(false);

  const loadData = useCallback(async () => {
    if (!spaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [spaceData, projectsData] = await Promise.all([
        spacesService.getSpace(spaceId),
        projectsService.listProjects(spaceId),
      ]);
      setSpace(spaceData);
      setProjects(projectsData.items);
      setEditName(spaceData.name);
      setEditDesc(spaceData.description || "");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load space dashboard.");
    } finally {
      setLoading(false);
    }
  }, [spaceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpdateSpace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!spaceId || !editName.trim()) return;
    try {
      setUpdating(true);
      const updated = await spacesService.updateSpace(spaceId, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      });
      setSpace(updated);
      setIsEditing(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update space.");
    } finally {
      setUpdating(false);
    }
  };

  const handleArchiveSpace = async () => {
    if (!spaceId) return;
    try {
      setArchiving(true);
      await spacesService.archiveSpace(spaceId);
      navigate("/spaces");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive space.");
    } finally {
      setArchiving(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading space workspace..." />;
  }

  if (error || !space) {
    return <ErrorState title="Space Error" message={error || "Space not found."} onRetry={loadData} />;
  }

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <button
        onClick={() => navigate("/spaces")}
        className="text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center space-x-1 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Spaces</span>
      </button>

      {/* Space Hero Card */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-indigo-950/20 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
                {space.slug}
              </span>
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                Role: <strong className="text-slate-200 capitalize">{space.role}</strong>
              </span>
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                {new Date(space.created_at).toLocaleDateString()}
              </span>
            </div>

            {isEditing ? (
              <form onSubmit={handleUpdateSpace} className="space-y-3 mt-2">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 font-bold text-xl"
                />
                <textarea
                  rows={2}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-300 text-sm"
                />
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={updating}
                    className="px-3 py-1 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500"
                  >
                    Save
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
                  <span className="text-3xl p-2 bg-slate-800/80 rounded-xl border border-slate-700/60 shadow-inner">
                    {space.visual_metadata?.icon || "🤖"}
                  </span>
                  <div>
                    <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight flex items-center gap-2">
                      <span>{space.name}</span>
                      {(space.role === "owner" || space.role === "admin") && (
                        <button
                          onClick={() => setIsEditing(true)}
                          className="text-slate-500 hover:text-indigo-400 p-1 transition text-sm"
                          title="Edit space metadata"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      )}
                    </h1>
                    <p className="text-xs text-indigo-400 font-medium mt-0.5">Broad Learning Space</p>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mt-3 leading-relaxed">
                  {space.description || "Learning modern technologies & skills."}
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={() => setIsCreateProjectOpen(true)}
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>+ Create Project</span>
            </button>
            {(space.role === "owner" || space.role === "admin") && (
              <button
                onClick={() => setIsArchiveOpen(true)}
                className="px-3 py-2 text-sm font-semibold text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-xl transition"
                title="Archive Space"
              >
                <Archive className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* High-Level Space Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active Projects</p>
          <p className="text-xl font-extrabold text-slate-100 mt-1">{projects.length}</p>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Average Progress</p>
          <p className="text-xl font-extrabold text-indigo-400 mt-1">
            {projects.length > 0
              ? `${Math.round(projects.reduce((acc, p) => acc + (p.progress || 0), 0) / projects.length)}%`
              : "0%"}
          </p>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recent Activity</p>
          {projects.some((p) => (p.materials_count || 0) > 0) ? (
            <p className="text-xs font-medium text-emerald-400 mt-1.5 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Active Study Session
            </p>
          ) : (
            <p className="text-xs font-medium text-slate-400 mt-1.5">No recent activity recorded</p>
          )}
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/40">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Areas Requiring Attention</p>
          <p className="text-xs font-medium text-amber-400 mt-1.5">
            {projects.length === 0 ? "None" : "No weak concepts identified"}
          </p>
        </div>
      </div>

      {/* Projects List Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-indigo-400" />
            <span>Projects in this Space ({projects.length})</span>
          </h2>
          <button
            onClick={() => setIsCreateProjectOpen(true)}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Project</span>
          </button>
        </div>

        {projects.length === 0 ? (
          <EmptyState
            icon={<FolderKanban className="w-8 h-8 text-slate-500" />}
            title="No Projects in Space"
            description="This space has no active projects. Create your first project to start organizing materials and learning goals."
            actionLabel="+ Create Project"
            onAction={() => setIsCreateProjectOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((pj) => {
              const projectProgress = pj.progress ?? 0;
              const materialsCount = pj.materials_count ?? 0;
              return (
                <div
                  key={pj.id}
                  className="group glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/70 transition duration-200 flex flex-col justify-between space-y-4 shadow-lg hover:shadow-indigo-500/5"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 rounded-full border border-indigo-500/20">
                        Project
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20 capitalize">
                        {pj.status}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-slate-100 group-hover:text-indigo-400 transition">
                      {pj.name}
                    </h3>

                    {/* Progress Bar */}
                    <div className="space-y-1.5 pt-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-400">Progress</span>
                        <span className="text-indigo-400">{projectProgress}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${projectProgress}%` }}
                        />
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 flex items-center justify-between pt-1">
                      <span className="bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60 font-medium">
                        📚 {materialsCount} materials
                      </span>
                    </div>

                    {pj.learning_goal && (
                      <p className="text-xs text-slate-400 italic bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 line-clamp-2">
                        Goal: &ldquo;{pj.learning_goal}&rdquo;
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[11px] text-slate-500">
                      Updated {new Date(pj.updated_at).toLocaleDateString()}
                    </span>
                    <Link
                      to={`/projects/${pj.id}`}
                      className="px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-md shadow-indigo-600/20 flex items-center gap-1"
                    >
                      Open Project &rarr;
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        defaultSpaceId={space.id}
        onClose={() => setIsCreateProjectOpen(false)}
        onSuccess={loadData}
      />

      <ConfirmDialog
        isOpen={isArchiveOpen}
        title="Archive Space"
        description={`Are you sure you want to archive space "${space.name}"? Soft archiving retains all underlying data.`}
        confirmLabel="Archive Space"
        isLoading={archiving}
        onConfirm={handleArchiveSpace}
        onClose={() => setIsArchiveOpen(false)}
      />
    </div>
  );
};
