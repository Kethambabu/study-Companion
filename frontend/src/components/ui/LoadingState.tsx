import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading data...",
  className = "",
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center text-muted-foreground ${className}`}
    >
      <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};
