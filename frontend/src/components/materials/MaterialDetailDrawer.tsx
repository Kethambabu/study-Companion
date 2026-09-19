import React, { useEffect, useState, useCallback } from "react";
import { X, FileText, AlertTriangle, RefreshCw, CheckCircle2, Clock, ShieldCheck, Database, Layers } from "lucide-react";
import { materialsService, MaterialItem, MaterialPageItem } from "@/services/materialsService";

interface MaterialDetailDrawerProps {
  material: MaterialItem | null;
  isOpen: boolean;
  onClose: () => void;
  onRefresh: () => void;
}

export const MaterialDetailDrawer: React.FC<MaterialDetailDrawerProps> = ({
  material,
  isOpen,
  onClose,
  onRefresh,
}) => {
  const [pages, setPages] = useState<MaterialPageItem[]>([]);
  const [loadingPages, setLoadingPages] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPages = useCallback(async () => {
    if (!material || material.status !== "ready") return;
    setLoadingPages(true);
    try {
      const res = await materialsService.getMaterialPages(material.id);
      setPages(res.items);
    } catch {
      // Soft error
    } finally {
      setLoadingPages(false);
    }
  }, [material]);

  useEffect(() => {
    if (isOpen && material) {
      fetchPages();
    } else {
      setPages([]);
    }
  }, [isOpen, material, fetchPages]);

  if (!isOpen || !material) return null;

  const handleRetry = async () => {
    try {
      setRetrying(true);
      setError(null);
      await materialsService.retryMaterial(material.id);
      onRefresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Retry failed.");
    } finally {
      setRetrying(false);
    }
  };

  const statusColors = {
    uploaded: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    queued: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    processing: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    ready: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    failed: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl p-6 text-slate-100 flex flex-col justify-between overflow-y-auto">
          {/* Header */}
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-100 truncate max-w-sm">
                    {material.filename}
                  </h2>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 mt-1 rounded-full text-xs font-medium border capitalize ${
                      statusColors[material.status] || statusColors.uploaded
                    }`}
                  >
                    {material.status}
                  </span>
                </div>
              </div>

              <button
                onClick={onClose}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl">
                {error}
              </div>
            )}

            {/* Failure Box & Retry trigger */}
            {material.status === "failed" && (
              <div className="p-4 bg-rose-950/40 border border-rose-500/30 rounded-2xl space-y-3">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-rose-200">Processing Extraction Failed</h4>
                    <p className="text-xs text-rose-300/80 mt-1 font-mono">
                      {material.last_error || "Unknown extraction error."}
                    </p>
                    <p className="text-xs text-slate-400 mt-2">
                      Attempts executed: <strong>{material.attempt_count}</strong>
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleRetry}
                  disabled={retrying}
                  className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-xl transition flex items-center space-x-2 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${retrying ? "animate-spin" : ""}`} />
                  <span>{retrying ? "Retrying Processing..." : "Retry Document Extraction"}</span>
                </button>
              </div>
            )}

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Database className="w-3.5 h-3.5 text-indigo-400" /> Storage Path
                </span>
                <p className="text-xs text-slate-200 font-mono truncate">{material.storage_path}</p>
              </div>

              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> SHA-256 Checksum
                </span>
                <p className="text-xs text-slate-200 font-mono truncate">{material.checksum}</p>
              </div>

              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-400" /> Word Count & Reading Time
                </span>
                <p className="text-xs text-slate-200 font-bold">
                  {material.word_count ? `${material.word_count.toLocaleString()} words (~${material.estimated_reading_minutes || 1} min)` : "N/A"}
                </p>
              </div>

              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 space-y-1">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-blue-400" /> Extracted Pages
                </span>
                <p className="text-xs font-bold text-slate-100">{material.page_count} Pages</p>
              </div>
            </div>

            {/* Extracted Pages Section */}
            <div className="space-y-3 pt-2">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Extracted Document Pages</span>
              </h3>

              {loadingPages ? (
                <div className="p-6 text-center text-slate-400 text-xs">Loading page texts...</div>
              ) : pages.length === 0 ? (
                <div className="p-6 text-center text-slate-500 text-xs bg-slate-950/40 border border-slate-800 rounded-xl">
                  {material.status === "ready"
                    ? "No pages extracted."
                    : "Extracted page text will appear once processing reaches 'ready' status."}
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
                  {pages.map((p) => (
                    <div
                      key={p.id}
                      className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2"
                    >
                      <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                        <span className="text-xs font-bold text-indigo-400">
                          Page {p.page_number}
                        </span>
                        {p.metadata_json && (
                          <span className="text-[10px] text-slate-500 font-mono">
                            Method: {p.metadata_json.extraction_method || "pymupdf"} | {p.metadata_json.word_count || 0} words
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed line-clamp-6">
                        {p.extracted_text}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 rounded-xl"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
