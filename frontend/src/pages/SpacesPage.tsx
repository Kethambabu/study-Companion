import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { spacesService, SpaceItem } from "@/services/spacesService";
import { CreateSpaceModal } from "@/components/spaces/CreateSpaceModal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Layers, Plus, Search, Archive, ArrowRight, Shield } from "lucide-react";

export const SpacesPage: React.FC = () => {
  const [spaces, setSpaces] = useState<SpaceItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [spaceToArchive, setSpaceToArchive] = useState<SpaceItem | null>(null);
  const [archiving, setArchiving] = useState(false);

  const fetchSpaces = useCallback(async () => {
    setSpaces((prev) => {
      if (prev.length === 0) setLoading(true);
      return prev;
    });
    setError(null);
    try {
      const res = await spacesService.listSpaces(search.trim() || undefined);
      setSpaces(res?.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load spaces.");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchSpaces();
  }, [fetchSpaces]);

  const handleArchive = async () => {
    if (!spaceToArchive) return;
    try {
      setArchiving(true);
      await spacesService.archiveSpace(spaceToArchive.id);
      setSpaceToArchive(null);
      await fetchSpaces();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to archive space.");
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
            <Layers className="w-6 h-6 text-indigo-400" />
            <span>Spaces Domain</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Multi-tenant workspace boundaries with Row Level Security isolation.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Space</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search spaces by name or slug..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>
      </div>

      {loading && spaces.length === 0 ? (
        <LoadingState message="Loading your spaces..." />
      ) : error ? (
        <ErrorState title="Failed to load spaces" message={error} onRetry={fetchSpaces} />
      ) : spaces.length === 0 ? (
        <EmptyState
          icon={<Layers className="w-8 h-8 text-slate-500" />}
          title={search ? "No Spaces Match Search" : "No Spaces Found"}
          description={
            search
              ? `No workspace matched your query "${search}".`
              : "Create your first multi-tenant space to start managing study projects."
          }
          actionLabel={search ? "Clear Search" : "Create Space"}
          onAction={search ? () => setSearch("") : () => setIsCreateOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {spaces.map((sp) => (
            <div
              key={sp.id}
              className="group glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:bg-slate-800/50 transition duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 text-xs font-medium bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20 font-mono">
                    {sp.slug}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Shield className="w-3 h-3 text-emerald-400" />
                      {sp.role}
                    </span>
                    {(sp.role === "owner" || sp.role === "admin") && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          setSpaceToArchive(sp);
                        }}
                        title="Archive space"
                        className="text-slate-500 hover:text-rose-400 p-1 rounded-md transition"
                      >
                        <Archive className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2.5">
                  <span className="text-xl shrink-0 p-1.5 bg-slate-800/80 rounded-lg border border-slate-700/60">
                    {sp.visual_metadata?.icon || "📚"}
                  </span>
                  <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-400 transition">
                    {sp.name}
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                  {sp.description || "No description provided."}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-xs text-slate-500">
                  Updated {new Date(sp.updated_at).toLocaleDateString()}
                </span>
                <Link
                  to={`/spaces/${sp.id}`}
                  className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
                >
                  Enter Space <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateSpaceModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={fetchSpaces}
      />

      <ConfirmDialog
        isOpen={!!spaceToArchive}
        title="Archive Space"
        description={`Are you sure you want to archive space "${spaceToArchive?.name}"? Soft archiving maintains data integrity.`}
        confirmLabel="Archive Space"
        isLoading={archiving}
        onConfirm={handleArchive}
        onClose={() => setSpaceToArchive(null)}
      />
    </div>
  );
};
