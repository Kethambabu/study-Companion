import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "Failed to load requested resources. Please try again.",
  onRetry,
  className = "",
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 glass-panel rounded-xl text-center max-w-md mx-auto ${className}`}
    >
      <div className="p-3 bg-red-500/10 text-red-400 rounded-full mb-4">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg transition-colors shadow-lg shadow-primary/20"
        >
          <RefreshCw className="h-4 w-4" />
          Try Again
        </button>
      )}
    </div>
  );
};
