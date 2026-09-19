import React, { useEffect, useState, useCallback } from "react";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { materialsService, MaterialItem } from "@/services/materialsService";
import { projectsService, ProjectItem } from "@/services/projectsService";
import { UploadMaterialModal } from "@/components/materials/UploadMaterialModal";
import { MaterialDetailDrawer } from "@/components/materials/MaterialDetailDrawer";
import { FileText, Plus, Search, RefreshCw, AlertTriangle, Layers } from "lucide-react";

export const MaterialsPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState<MaterialItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Initial projects fetch
  useEffect(() => {
    projectsService
      .listProjects(undefined, "active", undefined, 1, 100)
      .then((res) => {
        setProjects(res.items);
      })
      .catch(() => {});
  }, []);

  const fetchMaterials = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await materialsService.listMaterials(
        selectedProjectId || undefined,
        search.trim() || undefined
      );
      setMaterials(res.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load materials.");
    } finally {
      setLoading(false);
    }
  }, [selectedProjectId, search]);

  useEffect(() => {
    fetchMaterials();
  }, [fetchMaterials]);

  const handleMaterialClick = (mat: MaterialItem) => {
    setSelectedMaterial(mat);
    setIsDrawerOpen(true);
  };

  const statusBadges = {
    uploaded: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    queued: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    processing: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20 animate-pulse",
    ready: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-400" />
            <span>Study Materials & Document Extraction</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload PDF documents for PyMuPDF text extraction, OCR fallback, and structured page parsing.
          </p>
        </div>

        <button
          onClick={() => setIsUploadOpen(true)}
          className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 flex items-center space-x-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Upload Material</span>
        </button>
      </div>

      {/* Asynchronous Processing Status Pipeline Visualizer */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-2">
        <p className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider">
          Asynchronous Material Processing Pipeline
        </p>
        <div className="flex items-center justify-between overflow-x-auto text-[11px] font-medium text-slate-300 space-x-2 py-1">
          <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700 whitespace-nowrap">
            1. Queued ⏳
          </span>
          <span className="text-slate-600">&rarr;</span>
          <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700 whitespace-nowrap">
            2. Processing / OCR ⚙️
          </span>
          <span className="text-slate-600">&rarr;</span>
          <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700 whitespace-nowrap">
            3. Content Extraction 📑
          </span>
          <span className="text-slate-600">&rarr;</span>
          <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700 whitespace-nowrap">
            4. Knowledge Extraction 🧠
          </span>
          <span className="text-slate-600">&rarr;</span>
          <span className="px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700 whitespace-nowrap">
            5. Search / Retrieval 🔎
          </span>
          <span className="text-slate-600">&rarr;</span>
          <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20 font-bold whitespace-nowrap">
            6. READY ✓
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search materials by filename..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Accessible Projects</option>
            {projects.map((pj) => (
              <option key={pj.id} value={pj.id}>
                {pj.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={fetchMaterials}
          title="Refresh state"
          className="p-2 bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-xl transition shrink-0"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <LoadingState message="Loading study materials..." />
      ) : error ? (
        <ErrorState title="Failed to load materials" message={error} onRetry={fetchMaterials} />
      ) : materials.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-8 h-8 text-slate-500" />}
          title={search ? "No Materials Match Search" : "No Materials Ingested Yet"}
          description={
            search
              ? `No document matching filename query "${search}".`
              : "Upload your first PDF study material to start automatic document extraction."
          }
          actionLabel={search ? "Clear Search" : "Upload PDF Material"}
          onAction={search ? () => setSearch("") : () => setIsUploadOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {materials.map((mat) => (
            <div
              key={mat.id}
              onClick={() => handleMaterialClick(mat)}
              className="group glass-panel p-6 rounded-2xl border border-slate-800 bg-slate-900/40 hover:bg-slate-800/50 transition duration-200 flex flex-col justify-between cursor-pointer"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span
                    className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border capitalize ${
                      statusBadges[mat.status] || statusBadges.uploaded
                    }`}
                  >
                    {mat.status}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {(mat.file_size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-100 group-hover:text-indigo-400 transition truncate">
                  {mat.filename}
                </h3>

                {mat.status === "processing" && (
                  <div className="mt-3 space-y-1.5">
                    <div className="flex justify-between text-[11px] text-indigo-300 font-medium">
                      <span>{mat.current_step || "Processing..."}</span>
                      <span>{mat.progress_pct || 0}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 transition-all duration-300"
                        style={{ width: `${mat.progress_pct || 10}%` }}
                      />
                    </div>
                  </div>
                )}

                {mat.status === "failed" && (
                  <div className="mt-3 p-2.5 bg-rose-950/40 rounded-xl border border-rose-500/20 space-y-1">
                    <div className="flex items-center space-x-1.5 text-rose-400 text-xs font-bold">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>{mat.error_code || "PROCESSING_ERROR"}</span>
                    </div>
                    <p className="text-xs text-rose-300 font-mono line-clamp-2">
                      {mat.last_error || "Extraction failed."}
                    </p>
                  </div>
                )}

                {mat.status === "ready" && (mat.word_count || 0) > 0 && (
                  <div className="mt-3 flex items-center gap-3 text-xs text-slate-400">
                    <span>{mat.word_count?.toLocaleString()} words</span>
                    <span>•</span>
                    <span>~{mat.estimated_reading_minutes || 1} min read</span>
                  </div>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  {mat.page_count} Pages
                </span>
                <span className="text-indigo-400 font-semibold group-hover:translate-x-1 transition">
                  Details &rarr;
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <UploadMaterialModal
        isOpen={isUploadOpen}
        defaultProjectId={selectedProjectId || undefined}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={fetchMaterials}
      />

      <MaterialDetailDrawer
        material={selectedMaterial}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onRefresh={() => {
          fetchMaterials();
          if (selectedMaterial) {
            materialsService.getMaterial(selectedMaterial.id).then(setSelectedMaterial);
          }
        }}
      />
    </div>
  );
};
