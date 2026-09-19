import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDestructive = true,
  isLoading = false,
  onConfirm,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 text-slate-100 relative">
        <button
          onClick={onClose}
          disabled={isLoading}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-start space-x-4 mb-4">
          <div className={`p-3 rounded-xl ${isDestructive ? "bg-rose-500/10 text-rose-400" : "bg-indigo-500/10 text-indigo-400"}`}>
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
            <p className="text-sm text-slate-400 mt-1">{description}</p>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 text-sm font-medium rounded-xl transition flex items-center space-x-2 ${
              isDestructive
                ? "bg-rose-600 hover:bg-rose-500 text-white"
                : "bg-indigo-600 hover:bg-indigo-500 text-white"
            } disabled:opacity-50`}
          >
            {isLoading && <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />}
            <span>{confirmLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
