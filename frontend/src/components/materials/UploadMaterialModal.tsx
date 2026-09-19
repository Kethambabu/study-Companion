import React, { useState, useEffect } from "react";
import { X, UploadCloud, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { materialsService } from "@/services/materialsService";
import { projectsService, ProjectItem } from "@/services/projectsService";

interface UploadMaterialModalProps {
  isOpen: boolean;
  defaultProjectId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

const MAX_SIZE_MB = 25;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export const UploadMaterialModal: React.FC<UploadMaterialModalProps> = ({
  isOpen,
  defaultProjectId,
  onClose,
  onSuccess,
}) => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState(defaultProjectId || "");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    if (isOpen && !defaultProjectId) {
      projectsService
        .listProjects(undefined, "active", undefined, 1, 50)
        .then((res) => {
          setProjects(res.items);
          if (res.items.length > 0 && !selectedProjectId) {
            setSelectedProjectId(res.items[0].id);
          }
        })
        .catch(() => setError("Failed to load target projects."));
    } else if (defaultProjectId) {
      setSelectedProjectId(defaultProjectId);
    }
  }, [isOpen, defaultProjectId, selectedProjectId]);

  if (!isOpen) return null;

  const handleFileSelect = (file: File) => {
    setError(null);
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF document files (.pdf) are supported.");
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError(`File size exceeds maximum allowed limit of ${MAX_SIZE_MB}MB.`);
      return;
    }
    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) {
      setError("Please select a target project.");
      return;
    }
    if (!selectedFile) {
      setError("Please select a PDF document to upload.");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setProgress(0);

      await materialsService.uploadMaterial(selectedProjectId, selectedFile, (pct) => {
        setProgress(pct);
      });

      setSelectedFile(null);
      setProgress(100);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100 relative">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Upload Study Material</h2>
              <p className="text-xs text-slate-400">PDF Document Processing & Extraction Subsystem</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={uploading}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleUpload} className="space-y-4">
          {!defaultProjectId && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Target Project *</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                required
                disabled={uploading}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              >
                {projects.map((pj) => (
                  <option key={pj.id} value={pj.id}>
                    {pj.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer flex flex-col items-center justify-center ${
              dragActive
                ? "border-indigo-500 bg-indigo-500/10"
                : "border-slate-800 bg-slate-950/40 hover:bg-slate-900/60 hover:border-slate-700"
            }`}
          >
            <input
              type="file"
              accept=".pdf,application/pdf"
              id="file-upload-input"
              disabled={uploading}
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
            />

            <label htmlFor="file-upload-input" className="cursor-pointer space-y-2 flex flex-col items-center">
              <div className="p-3 bg-slate-800 text-indigo-400 rounded-xl">
                <FileText className="w-8 h-8" />
              </div>

              {selectedFile ? (
                <div className="flex items-center space-x-2 text-indigo-300 font-semibold text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{selectedFile.name}</span>
                  <span className="text-xs text-slate-400">
                    ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
              ) : (
                <>
                  <p className="text-sm font-semibold text-slate-200">
                    Click to browse or drag and drop PDF file
                  </p>
                  <p className="text-xs text-slate-500">
                    Maximum file size: {MAX_SIZE_MB}MB. Validated via server magic bytes.
                  </p>
                </>
              )}
            </label>
          </div>

          {/* Progress Bar */}
          {uploading && (
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Uploading document bytes...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full transition-all duration-150"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center space-x-2"
            >
              {uploading && <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
              <span>{uploading ? "Ingesting..." : "Upload & Process"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
