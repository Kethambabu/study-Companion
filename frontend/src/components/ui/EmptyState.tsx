import React, { ReactNode } from "react";
import { FolderOpen } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  actionLabel,
  onAction,
  icon,
  className = "",
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-10 glass-panel rounded-xl text-center max-w-lg mx-auto ${className}`}
    >
      <div className="p-4 bg-secondary text-primary rounded-2xl mb-4 shadow-inner">
        {icon || <FolderOpen className="h-8 w-8" />}
      </div>
      <h3 className="text-xl font-bold text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">{description}</p>
      {action && <div className="mt-2">{action}</div>}
      {!action && actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition shadow-md shadow-indigo-600/20"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
