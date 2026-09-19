import React, { useState, useEffect } from "react";
import { X, Target, FolderKanban } from "lucide-react";
import { projectsService } from "@/services/projectsService";
import { spacesService, SpaceItem } from "@/services/spacesService";

interface CreateProjectModalProps {
  isOpen: boolean;
  defaultSpaceId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  defaultSpaceId,
  onClose,
  onSuccess,
}) => {
  const [spaces, setSpaces] = useState<SpaceItem[]>([]);
  const [selectedSpaceId, setSelectedSpaceId] = useState(defaultSpaceId || "");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [learningGoal, setLearningGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchingSpaces, setFetchingSpaces] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && !defaultSpaceId) {
      setFetchingSpaces(true);
      spacesService
        .listSpaces(undefined, 1, 50)
        .then((res) => {
          setSpaces(res.items);
          if (res.items.length > 0) {
            setSelectedSpaceId((prev) => (prev ? prev : res.items[0].id));
          }
        })
        .catch(() => setError("Failed to load available spaces."))
        .finally(() => setFetchingSpaces(false));
    } else if (defaultSpaceId) {
      setSelectedSpaceId(defaultSpaceId);
    }
  }, [isOpen, defaultSpaceId]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSpaceId) {
      setError("Please select a space for this project.");
      return;
    }
    if (!name.trim()) {
      setError("Project name is required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await projectsService.createProject({
        space_id: selectedSpaceId,
        name: name.trim(),
        description: description.trim() || undefined,
        learning_goal: learningGoal.trim() || undefined,
      });
      setName("");
      setDescription("");
      setLearningGoal("");
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100 relative">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <FolderKanban className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Create Learning Project</h2>
              <p className="text-xs text-slate-400">Define your structured study objectives and material workspace</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!defaultSpaceId && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Target Space *</label>
              {fetchingSpaces ? (
                <div className="h-10 bg-slate-800 animate-pulse rounded-xl" />
              ) : (
                <select
                  value={selectedSpaceId}
                  onChange={(e) => setSelectedSpaceId(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                >
                  {spaces.map((sp) => (
                    <option key={sp.id} value={sp.id}>
                      {sp.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Project Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. RAG Fundamentals"
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description (Optional)</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Learn retrieval augmented generation."
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center space-x-1.5">
              <Target className="w-3.5 h-3.5 text-indigo-400" />
              <span>Target Learning Goal (Optional)</span>
            </label>
            <textarea
              rows={3}
              value={learningGoal}
              onChange={(e) => setLearningGoal(e.target.value)}
              placeholder="e.g. Understand how to build reliable RAG systems using embeddings, vector search, reranking and grounded generation."
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center space-x-2"
            >
              {loading && <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
              <span>Create Project</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
