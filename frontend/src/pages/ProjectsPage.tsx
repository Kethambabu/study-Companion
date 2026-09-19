import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { projectsService, ProjectItem } from "@/services/projectsService";
import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { FolderKanban, Plus, Search, Archive, ArrowRight, Target } from "lucide-react";

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("active");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [projectToArchive, setProjectToArchive] = useState<ProjectItem | null>(null);
  const [archiving, setArchiving] = useState(false);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await projectsService.listProjects(
        undefined,
        statusFilter || undefined,
        search.trim() || undefined
      );
      setProjects(res.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleArchive = async () => {
    if (!projectToArchive) return;
    try {
      setArchiving(true);
      await projectsService.archiveProject(projectToArchive.id);
      setProjectToArchive(null);
      await fetchProjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive project.");
    } finally {
      setArchiving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-emerald-400" />
            <span>Learning Projects</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Goal-driven study projects isolated inside tenant space containers.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Learning Project</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects by name or goal..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {["active", "completed", "archived"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl capitalize transition ${
                statusFilter === st
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-900/60 text-slate-400 border border-slate-800 hover:bg-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingState message="Loading projects..." />
      ) : error ? (
        <ErrorState title="Failed to load projects" message={error} onRetry={fetchProjects} />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban className="w-8 h-8 text-slate-500" />}
          title={search ? "No Projects Match Search" : `No ${statusFilter} Projects`}
          description={
            search
              ? `No project matched query "${search}".`
              : `You have no ${statusFilter} projects configured.`
          }
          actionLabel={search ? "Clear Search" : "Create Project"}
          onAction={search ? () => setSearch("") : () => setIsCreateOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((pj) => (
            <div
              key={pj.id}
              className="group glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:bg-slate-800/50 transition duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span
                    className={`px-2.5 py-0.5 text-xs font-medium rounded-full border capitalize ${
                      pj.status === "active"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : pj.status === "completed"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}
                  >
                    {pj.status}
                  </span>
                  {pj.status !== "archived" && (
                    <button
                      onClick={() => setProjectToArchive(pj)}
                      title="Archive project"
                      className="text-slate-500 hover:text-rose-400 p-1 rounded-md transition"
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <h3 className="text-base font-bold text-slate-100 group-hover:text-emerald-400 transition">
                  {pj.name}
                </h3>

                {pj.learning_goal ? (
                  <div className="mt-3 p-2.5 bg-slate-950/60 rounded-xl border border-slate-800 flex items-start space-x-2">
                    <Target className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-300 italic line-clamp-2">
                      {pj.learning_goal}
                    </p>
                  </div>
                ) : pj.description ? (
                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                    {pj.description}
                  </p>
                ) : null}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Updated {new Date(pj.updated_at).toLocaleDateString()}
                </span>
                <Link
                  to={`/projects/${pj.id}`}
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition"
                >
                  Project Dashboard <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateProjectModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={fetchProjects}
      />

      <ConfirmDialog
        isOpen={!!projectToArchive}
        title="Archive Project"
        description={`Are you sure you want to archive project "${projectToArchive?.name}"? Soft deletion is safe and recoverable.`}
        confirmLabel="Archive Project"
        isLoading={archiving}
        onConfirm={handleArchive}
        onClose={() => setProjectToArchive(null)}
      />
    </div>
  );
};
