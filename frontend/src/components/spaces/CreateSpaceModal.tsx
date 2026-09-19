import React, { useState } from "react";
import { X, Layers, Palette } from "lucide-react";
import { spacesService, SpaceVisualMetadata } from "@/services/spacesService";

interface CreateSpaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const THEME_OPTIONS = [
  { id: "indigo", name: "Indigo Modern", color: "bg-indigo-500", icon: "indigo" },
  { id: "emerald", name: "Emerald Growth", color: "bg-emerald-500", icon: "emerald" },
  { id: "amber", name: "Amber Focus", color: "bg-amber-500", icon: "amber" },
  { id: "rose", name: "Rose Academic", color: "bg-rose-500", icon: "rose" },
  { id: "cyan", name: "Cyan Tech", color: "bg-cyan-500", icon: "cyan" },
  { id: "violet", name: "Violet Deep", color: "bg-violet-500", icon: "violet" },
];

const EMOJI_OPTIONS = ["🤖", "🐍", "⚡", "🗄️", "🛡️", "📊", "🎓", "🧠", "🚀", "💻"];

export const CreateSpaceModal: React.FC<CreateSpaceModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("indigo");
  const [selectedIcon, setSelectedIcon] = useState("🤖");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleNameChange = (val: string) => {
    setName(val);
    setSlug(
      val
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) {
      setError("Name and slug are required.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const visualMetadata: SpaceVisualMetadata = {
        color_theme: selectedTheme,
        icon: selectedIcon,
      };
      await spacesService.createSpace(name.trim(), slug.trim(), description.trim() || undefined, visualMetadata);
      setName("");
      setSlug("");
      setDescription("");
      onSuccess();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create space.");
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
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Create New Space</h2>
              <p className="text-xs text-slate-400">Broad learning area (Technical skill, Certification, Goal, etc.)</p>
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
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Space Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="e.g. Artificial Intelligence"
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">URL Identifier (Slug) *</label>
            <input
              type="text"
              required
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="artificial-intelligence"
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description (Optional)</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Learning modern AI technologies."
              className="w-full px-4 py-2.5 bg-slate-800/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Space Icon / Emoji</label>
            <div className="flex items-center space-x-2 overflow-x-auto pb-1">
              {EMOJI_OPTIONS.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setSelectedIcon(emoji)}
                  className={`w-9 h-9 rounded-xl border flex items-center justify-center text-base transition shrink-0 ${
                    selectedIcon === emoji
                      ? "border-indigo-500 bg-indigo-500/20 shadow-sm"
                      : "border-slate-800 bg-slate-800/50 hover:bg-slate-800"
                  }`}
                >
                  {emoji}
                </button>
              ))}
              <input
                type="text"
                value={selectedIcon}
                onChange={(e) => setSelectedIcon(e.target.value)}
                maxLength={4}
                placeholder="Custom"
                className="w-12 h-9 px-2 bg-slate-800 border border-slate-700 rounded-xl text-center text-sm font-semibold focus:outline-none focus:border-indigo-500 shrink-0"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2 flex items-center space-x-1.5">
              <Palette className="w-3.5 h-3.5 text-indigo-400" />
              <span>Theme Preset</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {THEME_OPTIONS.map((theme) => (
                <button
                  key={theme.id}
                  type="button"
                  onClick={() => setSelectedTheme(theme.id)}
                  className={`flex items-center space-x-2.5 p-2 rounded-xl border text-left transition ${
                    selectedTheme === theme.id
                      ? "border-indigo-500 bg-indigo-500/10 text-white"
                      : "border-slate-800 bg-slate-800/40 text-slate-400 hover:bg-slate-800/80"
                  }`}
                >
                  <span className={`w-3.5 h-3.5 rounded-full ${theme.color}`} />
                  <span className="text-xs font-medium truncate">{theme.name}</span>
                </button>
              ))}
            </div>
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
              <span>Create Space</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
