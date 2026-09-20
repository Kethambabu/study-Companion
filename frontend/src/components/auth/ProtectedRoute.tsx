import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/useAuth";
import { LoadingState } from "@/components/ui/LoadingState";
import { authService } from "@/services/authService";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requireAdmin = false }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show spinner while session is loading OR while a token exists but user state
  // hasn't been populated yet (brief window after login before React re-renders).
  if (isLoading || (!user && authService.getToken())) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingState message="Verifying session security..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !(user?.role === "admin" || user?.is_admin)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
