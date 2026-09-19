import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { SpacesPage } from "@/pages/SpacesPage";
import { ProjectsPage } from "@/pages/ProjectsPage";
import { MaterialsPage } from "@/pages/MaterialsPage";
import { TutorPage } from "@/pages/TutorPage";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { GrowthPage } from "@/pages/GrowthPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

import { SpaceDashboardPage } from "@/pages/SpaceDashboardPage";
import { ProjectDashboardPage } from "@/pages/ProjectDashboardPage";

import { AdminLayout } from "@/components/admin/AdminLayout";
import { AdminOverviewPage } from "@/pages/admin/AdminOverviewPage";
import { AdminUsersPage } from "@/pages/admin/AdminUsersPage";
import { AdminSpacesPage } from "@/pages/admin/AdminSpacesPage";
import { AdminProjectsPage } from "@/pages/admin/AdminProjectsPage";
import { AdminActivityPage } from "@/pages/admin/AdminActivityPage";
import { AdminAnalyticsPage } from "@/pages/admin/AdminAnalyticsPage";
import { AdminAIUsagePage } from "@/pages/admin/AdminAIUsagePage";
import { AdminAIEvaluationPage } from "@/pages/admin/AdminAIEvaluationPage";
import { AdminJobsPage } from "@/pages/admin/AdminJobsPage";
import { AdminSystemHealthPage } from "@/pages/admin/AdminSystemHealthPage";

export const AppRouter: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminOverviewPage />} />
            <Route path="users" element={<AdminUsersPage />} />
            <Route path="spaces" element={<AdminSpacesPage />} />
            <Route path="projects" element={<AdminProjectsPage />} />
            <Route path="activity" element={<AdminActivityPage />} />
            <Route path="analytics" element={<AdminAnalyticsPage />} />
            <Route path="ai-usage" element={<AdminAIUsagePage />} />
            <Route path="ai-evaluation" element={<AdminAIEvaluationPage />} />
            <Route path="jobs" element={<AdminJobsPage />} />
            <Route path="system-health" element={<AdminSystemHealthPage />} />
          </Route>

          {/* Protected Workspace Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="spaces" element={<SpacesPage />} />
            <Route path="spaces/:spaceId" element={<SpaceDashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:projectId" element={<ProjectDashboardPage />} />
            <Route path="materials" element={<MaterialsPage />} />
            <Route path="tutor" element={<TutorPage />} />
            <Route path="assessment" element={<AssessmentPage />} />
            <Route path="growth" element={<GrowthPage initialTab="growth" />} />
            <Route path="mastery" element={<GrowthPage initialTab="mastery" />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
