import React from "react";
import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <div className="p-4 bg-primary/10 text-primary rounded-2xl mb-4 border border-primary/20">
        <Compass className="h-10 w-10 animate-pulse" />
      </div>
      <h2 className="text-3xl font-extrabold tracking-tight text-foreground mb-2">404 - Page Not Found</h2>
      <p className="text-sm text-muted-foreground mb-6 max-w-md">
        The requested route does not exist in the AI Study Companion routing shell.
      </p>
      <Link
        to="/"
        className="px-5 py-2.5 bg-primary text-primary-foreground text-sm font-semibold rounded-lg shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all"
      >
        Return to Dashboard
      </Link>
    </div>
  );
};
